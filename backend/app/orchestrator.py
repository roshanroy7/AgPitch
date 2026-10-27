"""
AgPitch - Orchestrator

Connects the Stats Engine to the AI agents without ever freezing the live stream.

For every key moment:
    Pundit  -> Overlay      done ONCE per moment, shared by every viewer
    Fan                     done once per moment AND viewer profile
At full time:
    Recap                   once per viewer profile

How it stays live:
  - Each moment becomes a background task. The match keeps streaming while
    the agents think, and finished insights are put in a queue that the
    stream picks up.
  - A semaphore limits how many AI calls run at the same time.
  - Results are cached in memory AND on disk (backend/data/cache/), so a
    replay or a server restart doesn't ask the agents again.
  - warm_up() runs every moment of the match through the agents in parallel
    before a broadcast, so every insight is ready exactly on time.
  - If an agent fails, the viewer still gets a simple card built from the
    stats engine's headline, so the stream never breaks.
"""

import asyncio
import hashlib
import json
import time
from pathlib import Path

from . import agents

MAX_PARALLEL_CALLS = 8

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"

# In memory: running or finished tasks, shared by every connection
_tasks = {"analysis": {}, "cards": {}, "recaps": {}}
# On disk: finished results, survive a restart
_disk = {"analysis": {}, "cards": {}, "recaps": {}}
_disk_path = None
_semaphore = None


# ---------------------------------------------------------------------------
# Cache on disk (one file per match, so a regenerated match never reuses old insights)
# ---------------------------------------------------------------------------


def configure_cache(match_file):
    global _disk, _disk_path
    fingerprint = hashlib.sha1(Path(match_file).read_bytes()).hexdigest()[:10]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _disk_path = CACHE_DIR / f"insights_{fingerprint}.json"
    if _disk_path.exists():
        _disk = json.loads(_disk_path.read_text())
    print(f"[orchestrator] cache: {_disk_path.name} "
          f"({len(_disk['analysis'])} moments, {len(_disk['cards'])} cards)")


def _remember(section, key, value):
    _disk[section][key] = value
    if _disk_path:
        tmp = _disk_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(_disk, ensure_ascii=False))
        tmp.replace(_disk_path)


def clear_language(language):
    """Forget cached cards and recaps in one language (e.g. after changing the Fan agent)."""
    removed = 0
    for section in ("cards", "recaps"):
        for key in [k for k in _disk[section] if k.endswith(f"|{language}")]:
            del _disk[section][key]
            removed += 1
        for key in [k for k in _tasks[section] if k.endswith(f"|{language}")]:
            del _tasks[section][key]
    if _disk_path:
        _disk_path.write_text(json.dumps(_disk, ensure_ascii=False))
    return removed


# ---------------------------------------------------------------------------
# Running agent calls
# ---------------------------------------------------------------------------


def _limit():
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(MAX_PARALLEL_CALLS)
    return _semaphore


async def _call(fn, *args):
    """Run a (blocking) agent call in a thread, a few at a time."""
    async with _limit():
        return await asyncio.to_thread(fn, *args)


def moment_key(moment):
    return f"{moment['minute']}:{moment['second']:02d}:{moment['kind']}:{moment.get('team')}"


def profile_key(profile):
    return "|".join(str(profile.get(k)) for k in ("mode", "favourite_club", "favourite_player", "language"))


async def _cached(section, key, make):
    """Disk first, then a shared in-memory task, then do the work once."""
    if key in _disk[section]:
        return _disk[section][key]
    task = _tasks[section].get(key)
    if task is None or (task.done() and (task.cancelled() or task.exception())):
        task = asyncio.ensure_future(make())
        _tasks[section][key] = task
    # shield: if one viewer disconnects, the shared work keeps going for the others
    result = await asyncio.shield(task)
    if key not in _disk[section]:
        _remember(section, key, result)
    return result


async def _analyse(moment, stats):
    started = time.time()
    analysis = await _call(agents.pundit, moment, stats)
    overlay = await _call(agents.overlay, moment, analysis)
    return {"analysis": analysis, "overlay": overlay, "seconds": round(time.time() - started, 1)}


async def _personalise(shared, profile):
    started = time.time()
    card = await _call(agents.fan, shared["overlay"], shared["analysis"], profile)
    return {"card": card, "seconds": round(time.time() - started, 1)}


async def build_insight(moment, stats, profile):
    """Pundit -> Overlay (shared) -> Fan (per profile), with caching and a fallback."""
    started = time.time()
    key = moment_key(moment)
    try:
        shared = await _cached("analysis", key, lambda: _analyse(moment, stats))
        personal = await _cached("cards", f"{key}|{profile_key(profile)}",
                                 lambda: _personalise(shared, profile))
        insight = {
            "analysis": shared["analysis"],
            "overlay": shared["overlay"],
            "card": personal["card"],
            "computed_s": round(shared.get("seconds", 0) + personal.get("seconds", 0), 1),
            "fallback": False,
        }
    except Exception as error:  # never let one failed call break the stream
        print(f"[orchestrator] {key} failed: {error!r}")
        insight = {
            "analysis": None,
            "overlay": {"graphic": "summary_card", "headline": moment["headline"],
                        "body": "", "stat": None, "duration_seconds": 6, "priority": "low"},
            "card": {"headline": moment["headline"], "body": "", "stat": None, "tone": "neutral"},
            "computed_s": None,
            "fallback": True,
        }
    insight["moment"] = moment
    insight["latency_s"] = round(time.time() - started, 1)
    return insight


async def build_recap(final_stats, moments, profile):
    moments = [m for m in moments if m["kind"] != "milestone"]
    try:
        result = await _cached("recaps", profile_key(profile),
                               lambda: _call(agents.recap, final_stats, moments, profile))
        return {"recap": result, "fallback": False}
    except Exception as error:
        print(f"[orchestrator] recap failed: {error!r}")
        return {"recap": None, "fallback": True}


# ---------------------------------------------------------------------------
# Warm-up: prepare a whole match for one viewer profile before going live
# ---------------------------------------------------------------------------


async def warm_up(match, engine_class, profile):
    started = time.time()
    engine = engine_class(match["info"])
    jobs, moments = [], []
    for event in match["events"]:
        for moment in engine.process(event):
            moments.append(moment)
            jobs.append(build_insight(moment, engine.snapshot(), profile))
    insights = await asyncio.gather(*jobs)
    recap = await build_recap(engine.snapshot(), moments, profile)
    failed = sum(1 for i in insights if i["fallback"])
    return {
        "profile": profile,
        "moments": len(insights),
        "failed": failed,
        "recap": not recap["fallback"],
        "seconds": round(time.time() - started, 1),
    }


# ---------------------------------------------------------------------------
# One per viewer connection
# ---------------------------------------------------------------------------


class Orchestrator:
    def __init__(self, profile):
        self.profile = profile
        self.queue = asyncio.Queue()
        self.tasks = set()
        self.moments_seen = []

    def on_moment(self, moment, stats):
        """Called by the stream for every key moment. Returns immediately."""
        self.moments_seen.append(moment)
        task = asyncio.ensure_future(self._produce_insight(moment, stats))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _produce_insight(self, moment, stats):
        insight = await build_insight(moment, stats, self.profile)
        await self.queue.put(("insight", insight))

    async def recap(self, final_stats):
        return await build_recap(final_stats, self.moments_seen, self.profile)

    def cancel(self):
        for task in list(self.tasks):
            task.cancel()
