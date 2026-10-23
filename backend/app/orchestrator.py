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
    stream picks up (like TV graphics arriving a few seconds after the play).
  - A semaphore limits how many AI calls run at the same time.
  - Results are cached. If two viewers share a profile, or the match is
    replayed, the AI is not asked again. Second run = instant.
  - If an agent fails, the viewer still gets a simple card built from the
    stats engine's headline, so the stream never breaks.
"""

import asyncio
import time

from . import agents

MAX_PARALLEL_CALLS = 4

# Shared by every connection: survives as long as the server runs
_analysis_cache = {}   # moment key -> task returning {"analysis", "overlay"}
_card_cache = {}       # (moment key, profile key) -> task returning the fan card
_recap_cache = {}      # profile key -> task returning the recap
_semaphore = None


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


async def _analyse(moment, stats):
    analysis = await _call(agents.pundit, moment, stats)
    overlay = await _call(agents.overlay, moment, analysis)
    return {"analysis": analysis, "overlay": overlay}


def _shared(cache, key, make):
    """Start the work once; everyone else awaits the same task."""
    task = cache.get(key)
    if task is None or (task.done() and (task.cancelled() or task.exception())):
        task = asyncio.ensure_future(make())
        cache[key] = task
    # shield: if one viewer disconnects, the shared work keeps going for the others
    return asyncio.shield(task)


class Orchestrator:
    """One per viewer connection."""

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
        started = time.time()
        key = moment_key(moment)
        try:
            shared = await _shared(_analysis_cache, key, lambda: _analyse(moment, stats))
            card = await _shared(
                _card_cache, (key, profile_key(self.profile)),
                lambda: _call(agents.fan, shared["overlay"], shared["analysis"], self.profile),
            )
            insight = {**shared, "card": card, "fallback": False}
        except Exception as error:  # never let one failed call break the stream
            print(f"[orchestrator] {key} failed: {error!r}")
            insight = {
                "analysis": None,
                "overlay": {"graphic": "summary_card", "headline": moment["headline"],
                            "body": "", "stat": None, "duration_seconds": 6, "priority": "low"},
                "card": {"headline": moment["headline"], "body": "", "stat": None, "tone": "neutral"},
                "fallback": True,
            }
        insight["moment"] = moment
        insight["latency_s"] = round(time.time() - started, 1)
        await self.queue.put(("insight", insight))

    async def recap(self, final_stats):
        key = profile_key(self.profile)
        moments = [m for m in self.moments_seen if m["kind"] not in ("milestone",)]
        try:
            result = await _shared(_recap_cache, key,
                                   lambda: _call(agents.recap, final_stats, moments, self.profile))
            return {"recap": result, "fallback": False}
        except Exception as error:
            print(f"[orchestrator] recap failed: {error!r}")
            return {"recap": None, "fallback": True}

    def cancel(self):
        for task in list(self.tasks):
            task.cancel()
