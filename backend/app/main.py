"""
AgPitch - API server

Replays the synthetic match as if it were live and streams it to the
browser with Server-Sent Events (SSE).

Run it (from the AgPitch folder):
    uvicorn backend.app.main:app --reload

Then open:
    http://localhost:8000/                 health check
    http://localhost:8000/match            teams and players
    http://localhost:8000/stream           the live match stream
    http://localhost:8000/stream?speed=120&from_minute=60
                                           faster, starting from minute 60

SSE in one line: the browser opens ONE connection and the server keeps
sending messages down it. Each message looks like this:

    event: moment
    data: {"minute": 63, "kind": "goal", ...}

and ends with an empty line.
"""

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .stats import StatsEngine

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "match_001.json"
MATCH = json.loads(DATA_FILE.read_text())

app = FastAPI(title="AgPitch API", version="0.1.0")

# Let the Next.js frontend (running on port 3000) call this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def sse(event_name, data):
    """Format one Server-Sent Event message."""
    return f"event: {event_name}\ndata: {json.dumps(data)}\n\n"


def seconds_of(event):
    return event["minute"] * 60 + event["second"]


@app.get("/")
def health():
    return {"status": "ok", "match": f"{MATCH['info']['home']} vs {MATCH['info']['away']}"}


@app.get("/match")
def match_info():
    return MATCH["info"]


@app.get("/stream")
async def stream(
    speed: float = Query(30, ge=1, le=600,
                         description="How many match seconds pass per real second"),
    from_minute: int = Query(0, ge=0, le=90,
                             description="Skip straight to this minute"),
):
    """Replay the match live. Sends three kinds of messages:
    - event:  every match event (pass, shot, tackle, ...)
    - stats:  the latest numbers, once per match minute
    - moment: a key moment flagged by the Stats Engine
    """

    async def replay():
        engine = StatsEngine(MATCH["info"])
        last_clock = from_minute * 60
        last_minute_sent = -1

        yield sse("start", {"info": MATCH["info"], "speed": speed, "from_minute": from_minute})

        for event in MATCH["events"]:
            clock = seconds_of(event)

            # Fast-forward: update the numbers silently until from_minute
            if clock < from_minute * 60:
                engine.process(event)
                continue

            # Wait for the right moment, so it feels live
            gap = (clock - last_clock) / speed
            if gap > 0:
                await asyncio.sleep(min(gap, 5))
            last_clock = clock

            moments = engine.process(event)
            yield sse("event", event)
            for moment in moments:
                yield sse("moment", moment)

            if event["minute"] != last_minute_sent:
                last_minute_sent = event["minute"]
                yield sse("stats", engine.snapshot())

        yield sse("stats", engine.snapshot())
        yield sse("end", {"score": engine.score})

    return StreamingResponse(
        replay(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
