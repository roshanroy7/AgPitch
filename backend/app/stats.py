"""
AgPitch - Stats Engine

Reads match events one at a time, exactly as they would arrive live,
and keeps a running picture of the match. No AI here, only maths.

Two outputs:
  1. snapshot()  -> the current numbers (score, possession, pass accuracy, ...)
  2. moments     -> key moments flagged by simple rules, e.g.
                    "Kryptonites lost the ball 5 times in 5 minutes".
                    These are what the Pundit agent will explain later.

Usage:
    engine = StatsEngine(match_info)
    for event in events:
        new_moments = engine.process(event)
"""

import json
import math
from collections import deque
from pathlib import Path

PITCH_LENGTH_M = 105
PITCH_WIDTH_M = 68

# Rule thresholds for key moments
TURNOVER_WINDOW = 5 * 60        # look at the last 5 minutes
TURNOVER_LIMIT = 8              # this many lost balls in the window = a moment
MOMENTUM_WINDOW = 10 * 60       # compare the last 10 minutes with the 10 before
MOMENTUM_SWING = 18             # percentage points
PRESSURE_WINDOW = 5 * 60
PRESSURE_SHARE = 0.5            # half of a team's passes under pressure
SPRINT_ALERT_KMH = 33
ROCKET_SHOT_KMH = 100
BIG_SAVE_KMH = 90               # saves from shots this fast are key moments
PASS_MILESTONES = (50,)
COOLDOWN = 8 * 60               # same kind of moment, same team: wait this long


def seconds_of(event):
    return event["minute"] * 60 + event["second"]


def pass_distance_m(start, end):
    """Distance in metres, turning 0-100 coordinates into a real pitch size."""
    dx = (end[0] - start[0]) * PITCH_LENGTH_M / 100
    dy = (end[1] - start[1]) * PITCH_WIDTH_M / 100
    return math.hypot(dx, dy)


def pass_difficulty(event):
    """0-10. Longer, more forward and pressured passes are harder."""
    distance = pass_distance_m(event["start"], event["end"])
    forward = (event["end"][0] - event["start"][0]) * PITCH_LENGTH_M / 100

    score = min(distance / 40, 1) * 4          # up to 4 points for length
    score += max(min(forward / 30, 1), 0) * 3  # up to 3 points for going forward
    if event.get("under_pressure"):
        score += 2
    if event["end"][0] > 66:                   # into the final third
        score += 1
    return round(min(score, 10), 1)


class StatsEngine:
    def __init__(self, match_info):
        self.info = match_info
        self.teams = [match_info["home"], match_info["away"]]
        self.clock = 0
        self.score = {t: 0 for t in self.teams}
        self.team = {t: self._empty_team() for t in self.teams}
        self.players = {}
        for t in self.teams:
            for p in match_info["teams"][t]["players"]:
                self.players[p["name"]] = self._empty_player(t, p)

        # Recent history, used by the rules
        self.recent_passes = deque()     # (seconds, team, under_pressure)
        self.recent_turnovers = deque()  # (seconds, team that lost it)
        self.last_fired = {}             # (kind, team) -> seconds
        self.moments = []

    # ---------------------------------------------------------------- setup

    @staticmethod
    def _empty_team():
        return {
            "passes": 0, "passes_completed": 0, "pass_distance_m": 0.0,
            "difficulty_total": 0.0, "passes_under_pressure": 0,
            "shots": 0, "shots_on_target": 0, "fastest_shot_kmh": 0.0,
            "tackles": 0, "interceptions": 0, "fouls": 0, "turnovers": 0,
            "saves": 0, "corners": 0, "counter_attacks": 0, "clearances": 0,
            "yellow_cards": 0, "red_cards": 0, "hard_fouls": 0,
        }

    @staticmethod
    def _empty_player(team, p):
        return {
            "team": team, "number": p["number"], "position": p["position"],
            "touches": 0, "passes": 0, "passes_completed": 0,
            "difficulty_total": 0.0, "shots": 0, "goals": 0, "assists": 0,
            "tackles": 0, "interceptions": 0, "top_speed_kmh": 0.0, "saves": 0,
        }

    # --------------------------------------------------------------- update

    def process(self, event):
        """Update all numbers with one event. Returns any new key moments."""
        self.clock = seconds_of(event)
        new = []
        kind = event["type"]
        team = event.get("team")
        player = self.players.get(event.get("player"))
        if player:
            player["touches"] += 1

        if kind == "pass":
            new += self._on_pass(event, team, player)
        elif kind == "shot":
            new += self._on_shot(event, team, player)
        elif kind == "goal":
            self.score[team] += 1
            self.players[event["player"]]["goals"] += 1
            if event.get("assist"):
                self.players[event["assist"]]["assists"] += 1
            new.append(self._moment("goal", event, team, event["player"],
                                    f"GOAL! {event['player']} scores for {team}",
                                    {"score": dict(self.score), "assist": event.get("assist")}))
        elif kind in ("tackle", "interception"):
            self.team[team][kind + "s"] += 1
            if player:
                player[kind + "s"] += 1
        elif kind == "save":
            self.team[team]["saves"] += 1
            player["saves"] += 1
            if event["shot_speed_kmh"] >= BIG_SAVE_KMH:
                new.append(self._moment("big_save", event, team, event["player"],
                                        f"Big save! {event['player']} denies {event['shooter']}",
                                        {"shot_speed_kmh": event["shot_speed_kmh"],
                                         "shooter": event["shooter"]},
                                        cooldown=5 * 60))
        elif kind == "corner":
            self.team[team]["corners"] += 1
        elif kind == "clearance":
            self.team[team]["clearances"] += 1
        elif kind == "counter_attack":
            self.team[team]["counter_attacks"] += 1
            new.append(self._moment("counter_attack", event, team, event["player"],
                                    f"{team} break on the counter",
                                    {"started_by": event["player"],
                                     "counter_attacks": self.team[team]["counter_attacks"]},
                                    cooldown=6 * 60))
        elif kind in ("yellow_card", "red_card"):
            self.team[team][kind + "s"] += 1
            colour = "Yellow" if kind == "yellow_card" else "Red"
            new.append(self._moment(kind, event, team, event["player"],
                                    f"{colour} card for {event['player']}",
                                    {"reason": event.get("reason"), "fouled": event.get("fouled"),
                                     "team_" + kind + "s": self.team[team][kind + "s"]},
                                    cooldown=0))
        elif kind == "foul":
            self.team[team]["fouls"] += 1
            if event.get("hard"):
                self.team[team]["hard_fouls"] += 1
        elif kind == "sprint":
            player["top_speed_kmh"] = max(player["top_speed_kmh"], event["top_speed_kmh"])
            if event["top_speed_kmh"] >= SPRINT_ALERT_KMH:
                new.append(self._moment("speed_alert", event, team, event["player"],
                                        f"{event['player']} hits {event['top_speed_kmh']} km/h",
                                        {"top_speed_kmh": event["top_speed_kmh"],
                                         "distance_m": event["distance_m"]}))
        elif kind in ("half_time", "full_time"):
            new.append(self._moment(kind, event, None, None,
                                    f"{kind.replace('_', ' ').title()}: "
                                    f"{self.teams[0]} {self.score[self.teams[0]]} - "
                                    f"{self.score[self.teams[1]]} {self.teams[1]}",
                                    self.snapshot()))

        new += self._check_rules(event)
        new = [m for m in new if m]  # drop moments skipped by the cooldown
        self.moments += new
        return new

    def _on_pass(self, event, team, player):
        new = []
        t = self.team[team]
        distance = pass_distance_m(event["start"], event["end"])
        difficulty = pass_difficulty(event)
        success = event["outcome"] == "success"
        pressured = bool(event.get("under_pressure"))

        t["passes"] += 1
        t["pass_distance_m"] += distance
        t["difficulty_total"] += difficulty
        t["passes_under_pressure"] += pressured
        player["passes"] += 1
        player["difficulty_total"] += difficulty

        self.recent_passes.append((self.clock, team, pressured))

        if success:
            t["passes_completed"] += 1
            player["passes_completed"] += 1
            done = player["passes_completed"]
            if done in PASS_MILESTONES:
                new.append(self._moment("milestone", event, team, event["player"],
                                        f"{event['player']} completes pass number {done}",
                                        {"passes_completed": done,
                                         "accuracy": self._pct(done, player["passes"])}))
            if difficulty >= 8.5:
                new.append(self._moment("quality_pass", event, team, event["player"],
                                        f"Difficult pass completed by {event['player']}",
                                        {"difficulty": difficulty,
                                         "distance_m": round(distance, 1),
                                         "receiver": event.get("receiver")},
                                        cooldown_key=("quality_pass", None)))
        else:
            t["turnovers"] += 1
            self.recent_turnovers.append((self.clock, team))
        return [m for m in new if m]

    def _on_shot(self, event, team, player):
        t = self.team[team]
        t["shots"] += 1
        player["shots"] += 1
        if event["on_target"]:
            t["shots_on_target"] += 1
        t["fastest_shot_kmh"] = max(t["fastest_shot_kmh"], event["shot_speed_kmh"])
        if event["shot_speed_kmh"] >= ROCKET_SHOT_KMH and event["outcome"] != "goal":
            m = self._moment("rocket_shot", event, team, event["player"],
                             f"{event['player']} strikes at {event['shot_speed_kmh']} km/h",
                             {"shot_speed_kmh": event["shot_speed_kmh"],
                              "outcome": event["outcome"]})
            return [m] if m else []
        return []

    # ---------------------------------------------------------------- rules

    def _check_rules(self, event):
        new = []
        now = self.clock

        # Forget history that is too old
        while self.recent_passes and now - self.recent_passes[0][0] > 2 * MOMENTUM_WINDOW:
            self.recent_passes.popleft()
        while self.recent_turnovers and now - self.recent_turnovers[0][0] > TURNOVER_WINDOW:
            self.recent_turnovers.popleft()

        for team in self.teams:
            # Rule 1: losing the ball again and again
            lost = sum(1 for _, t in self.recent_turnovers if t == team)
            if lost >= TURNOVER_LIMIT:
                new.append(self._moment("turnover_streak", event, team, None,
                                        f"{team} have lost the ball {lost} times in 5 minutes",
                                        {"turnovers_last_5_min": lost}))

            # Rule 2: being pressed hard
            window = [p for s, t, p in self.recent_passes
                      if t == team and now - s <= PRESSURE_WINDOW]
            if len(window) >= 8:
                share = sum(window) / len(window)
                if share >= PRESSURE_SHARE:
                    new.append(self._moment("pressure_spike", event, team, None,
                                            f"{team} are under heavy pressure",
                                            {"passes_under_pressure_pct": round(share * 100)}))

        # Rule 3: momentum swing (possession now vs the 10 minutes before)
        if now >= 2 * MOMENTUM_WINDOW:
            now_share = self._possession_between(now - MOMENTUM_WINDOW, now)
            before = self._possession_between(now - 2 * MOMENTUM_WINDOW, now - MOMENTUM_WINDOW)
            for team in self.teams:
                if now_share and before:
                    swing = now_share[team] - before[team]
                    if swing >= MOMENTUM_SWING and now_share[team] >= 60:
                        new.append(self._moment("momentum_swing", event, team, None,
                                                f"Momentum swing towards {team}",
                                                {"possession_last_10_min": now_share[team],
                                                 "possession_previous_10_min": before[team]},
                                                cooldown=12 * 60))
        return [m for m in new if m]

    # -------------------------------------------------------------- helpers

    def _moment(self, kind, event, team, player, headline, data,
                cooldown=COOLDOWN, cooldown_key=None):
        """Create a key moment, unless the same kind fired too recently."""
        key = cooldown_key or (kind, team)
        always = kind in ("goal", "half_time", "full_time", "milestone", "yellow_card", "red_card")
        if not always and now_minus(self.clock, self.last_fired.get(key)) < cooldown:
            return None
        self.last_fired[key] = self.clock
        return {
            "minute": event["minute"],
            "second": event["second"],
            "kind": kind,
            "team": team,
            "player": player,
            "headline": headline,
            "data": data,
        }

    def _possession_between(self, start, end):
        counts = {t: 0 for t in self.teams}
        for s, t, _ in self.recent_passes:
            if start <= s < end:
                counts[t] += 1
        total = sum(counts.values())
        if total < 10:
            return None
        return {t: round(c / total * 100) for t, c in counts.items()}

    @staticmethod
    def _pct(part, whole):
        return round(part / whole * 100) if whole else 0

    # ------------------------------------------------------------- snapshot

    def snapshot(self):
        """The current numbers, ready to send to the frontend or the agents."""
        total_passes = sum(self.team[t]["passes"] for t in self.teams) or 1
        recent = self._possession_between(self.clock - MOMENTUM_WINDOW, self.clock)
        teams = {}
        for name in self.teams:
            t = self.team[name]
            teams[name] = {
                "possession_pct": self._pct(t["passes"], total_passes),
                "possession_last_10_min_pct": recent[name] if recent else None,
                "pass_accuracy_pct": self._pct(t["passes_completed"], t["passes"]),
                "passes": t["passes"],
                "avg_pass_distance_m": round(t["pass_distance_m"] / t["passes"], 1) if t["passes"] else 0,
                "avg_pass_difficulty": round(t["difficulty_total"] / t["passes"], 1) if t["passes"] else 0,
                "passes_under_pressure_pct": self._pct(t["passes_under_pressure"], t["passes"]),
                "shots": t["shots"],
                "shots_on_target": t["shots_on_target"],
                "fastest_shot_kmh": t["fastest_shot_kmh"],
                "tackles": t["tackles"],
                "interceptions": t["interceptions"],
                "fouls": t["fouls"],
                "turnovers": t["turnovers"],
                "saves": t["saves"],
                "corners": t["corners"],
                "counter_attacks": t["counter_attacks"],
                "yellow_cards": t["yellow_cards"],
                "red_cards": t["red_cards"],
            }
        return {
            "minute": self.clock // 60,
            "second": self.clock % 60,
            "score": dict(self.score),
            "teams": teams,
        }

    def player_stats(self, name):
        p = self.players[name]
        return {
            "name": name, **{k: v for k, v in p.items() if k != "difficulty_total"},
            "pass_accuracy_pct": self._pct(p["passes_completed"], p["passes"]),
            "avg_pass_difficulty": round(p["difficulty_total"] / p["passes"], 1) if p["passes"] else 0,
        }


def now_minus(now, then):
    return math.inf if then is None else now - then


# -------------------------------------------------------------------------
# Run this file on its own to replay the demo match and print what it finds
# -------------------------------------------------------------------------

if __name__ == "__main__":
    path = Path(__file__).resolve().parent.parent / "data" / "match_001.json"
    match = json.loads(path.read_text())
    engine = StatsEngine(match["info"])

    for event in match["events"]:
        for m in engine.process(event):
            print(f"{m['minute']:>2}:{m['second']:02d}  [{m['kind']}]  {m['headline']}")

    print("\nFull-time numbers:")
    for team, numbers in engine.snapshot()["teams"].items():
        print(f"  {team}: {numbers['possession_pct']}% possession, "
              f"{numbers['pass_accuracy_pct']}% pass accuracy, "
              f"{numbers['shots']} shots ({numbers['shots_on_target']} on target), "
              f"{numbers['turnovers']} turnovers")
    print("\nRoshan Palem:", engine.player_stats("Roshan Palem"))
    print(f"\nTotal key moments: {len(engine.moments)}")
