"""
AgPitch - API server

Replays the synthetic match as if it were live and streams it to the
browser with Server-Sent Events (SSE). Key moments are sent to the AI
agents in the background, and their insights are streamed as they arrive.

Run it (from the AgPitch folder):
    python -m uvicorn backend.app.main:app --reload

Then open:
    http://localhost:8000/                 health check
    http://localhost:8000/match            teams and players
    http://localhost:8000/stream           the live match stream

Stream options (all optional):
    speed=30           match seconds per real second
    from_minute=0      skip straight to this minute
    ai=true            set to false to stream without the AI agents
    mode=casual        analyst | casual | player_focus
    club=Ultras        favourite club
    player=...         favourite player (needed for player_focus)
    language=en        en | te (Telugu)

Example:
    /stream?speed=10&from_minute=60&mode=casual&club=Ultras&language=te

Message types sent down the stream:
    start    match info and the viewer profile
    event    every match event (pass, shot, tackle, ...)
    stats    the latest numbers, once per match minute
    moment   a key moment flagged by the Stats Engine
    insight  the agents' explanation + overlay + personalised card
    recap    the full-time summary for this viewer
    end      final score
"""

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .orchestrator import Orchestrator
from .stats import StatsEngine

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "match_001.json"
MATCH = json.loads(DATA_FILE.read_text())
TEAMS = [MATCH["info"]["home"], MATCH["info"]["away"]]
PLAYERS = {p["name"] for t in TEAMS for p in MATCH["info"]["teams"][t]["players"]}

app = FastAPI(title="AgPitch API", version="0.2.0")

# Let the Next.js frontend (running on port 3000) call this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def sse(event_name, data):
    """Format one Server-Sent Event message."""
    return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def seconds_of(event):
    return event["minute"] * 60 + event["second"]


def build_profile(mode, club, player, language):
    if mode not in ("analyst", "casual", "player_focus"):
        raise HTTPException(400, "mode must be analyst, casual or player_focus")
    if language not in ("en", "te"):
        raise HTTPException(400, "language must be en or te")
    if club and club not in TEAMS:
        raise HTTPException(400, f"club must be one of {TEAMS}")
    if player and player not in PLAYERS:
        raise HTTPException(400, "unknown player")
    if mode == "player_focus" and not player:
        raise HTTPException(400, "player_focus mode needs a player")
    return {"mode": mode, "favourite_club": club, "favourite_player": player, "language": language}


@app.get("/")
def health():
    return {"status": "ok", "match": f"{TEAMS[0]} vs {TEAMS[1]}"}


@app.get("/match")
def match_info():
    return MATCH["info"]


@app.get("/stream")
async def stream(
    speed: float = Query(30, ge=1, le=600),
    from_minute: int = Query(0, ge=0, le=90),
    ai: bool = Query(True),
    mode: str = Query("casual"),
    club: str | None = Query(None),
    player: str | None = Query(None),
    language: str = Query("en"),
):
    profile = build_profile(mode, club, player, language)

    async def replay():
        engine = StatsEngine(MATCH["info"])
        brain = Orchestrator(profile) if ai else None
        last_clock = from_minute * 60
        last_minute_sent = -1

        async def wait_and_flush(seconds):
            """Wait between events, but send any insight that is ready meanwhile."""
            if not brain:
                await asyncio.sleep(seconds)
                return
            loop = asyncio.get_running_loop()
            deadline = loop.time() + seconds
            while (remaining := deadline - loop.time()) > 0:
                try:
                    name, data = await asyncio.wait_for(brain.queue.get(), remaining)
                    yield sse(name, data)
                except asyncio.TimeoutError:
                    break

        try:
            yield sse("start", {"info": MATCH["info"], "speed": speed,
                                "from_minute": from_minute, "ai": ai, "profile": profile})

            for event in MATCH["events"]:
                clock = seconds_of(event)

                # Fast-forward: update the numbers silently until from_minute
                if clock < from_minute * 60:
                    engine.process(event)
                    continue

                # Wait for the right moment, so it feels live
                gap = (clock - last_clock) / speed
                if gap > 0:
                    async for message in wait_and_flush(min(gap, 5)):
                        yield message
                last_clock = clock

                moments = engine.process(event)
                yield sse("event", event)
                for moment in moments:
                    yield sse("moment", moment)
                    if brain:
                        brain.on_moment(moment, engine.snapshot())

                if event["minute"] != last_minute_sent:
                    last_minute_sent = event["minute"]
                    yield sse("stats", engine.snapshot())

            final = engine.snapshot()
            yield sse("stats", final)

            if brain:
                # Send the last insights as soon as each one finishes, then the recap
                while True:
                    while not brain.queue.empty():
                        name, data = brain.queue.get_nowait()
                        yield sse(name, data)
                    pending = set(brain.tasks)
                    if not pending:
                        break
                    done, _ = await asyncio.wait(pending, timeout=90,
                                                 return_when=asyncio.FIRST_COMPLETED)
                    if not done:  # agents stuck for 90s: give up on the rest
                        break
                yield sse("recap", await brain.recap(final))

            yield sse("end", {"score": engine.score})
        finally:
            if brain:
                brain.cancel()  # viewer left: stop this viewer's pending work

    return StreamingResponse(
        replay(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
