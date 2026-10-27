"""
AgPitch - synthetic match generator

Builds one fake but realistic football match (Kryptonites vs Ultras) and
saves every event to backend/data/match_001.json.

How it works:
  1. The match is split into PHASES. Each phase says which team is on top
     and whether anyone is pressing high. This is what shapes the story.
  2. The clock runs from 0 to 90 minutes. One team has the ball and plays
     a CHAIN of passes moving forward, until they lose it, foul, or shoot.
  3. The three GOALS are scripted, so the story always ends Ultras 2-1.
  4. A fixed random SEED means the match is identical every time we run it.

Pitch coordinates: [x, y] from 0 to 100, always from the point of view of
the team with the ball. x = 0 is their own goal, x = 100 is the goal they
attack. y = 0 and y = 100 are the two touchlines.
"""

import json
import random
from pathlib import Path

SEED = 7
random.seed(SEED)

# ---------------------------------------------------------------------------
# 1. Match info: teams and players
# ---------------------------------------------------------------------------

MATCH_INFO = {
    "match_id": "match_001",
    "competition": "AgPitch Demo League",
    "venue": "Riverside Arena",
    "date": "2026-10-24",
    "home": "Kryptonites",
    "away": "Ultras",
    "teams": {
        "Kryptonites": {
            "formation": "4-3-3",
            "players": [
                {"name": "Matt Collins", "number": 1, "position": "GK"},
                {"name": "Josh Bennett", "number": 2, "position": "RB"},
                {"name": "Chris Holloway", "number": 5, "position": "CB", "captain": True},
                {"name": "Sam Fletcher", "number": 6, "position": "CB"},
                {"name": "Liam Parker", "number": 3, "position": "LB"},
                {"name": "Dan Whitmore", "number": 8, "position": "CM"},
                {"name": "Ollie Grant", "number": 4, "position": "CM"},
                {"name": "Jamie Rowe", "number": 10, "position": "CAM"},
                {"name": "Tyler Brooks", "number": 7, "position": "RW"},
                {"name": "Nathan Price", "number": 11, "position": "LW"},
                {"name": "Callum Reed", "number": 9, "position": "ST"},
            ],
        },
        "Ultras": {
            "formation": "4-2-3-1",
            "players": [
                {"name": "Ethan Moore", "number": 1, "position": "GK"},
                {"name": "Luke Simmons", "number": 2, "position": "RB"},
                {"name": "Harry Lawson", "number": 5, "position": "CB"},
                {"name": "George Mitchell", "number": 6, "position": "CB"},
                {"name": "Adam Fisher", "number": 3, "position": "LB"},
                {"name": "Owen Clarke", "number": 4, "position": "CDM"},
                {"name": "Ben Hollis", "number": 8, "position": "CDM"},
                {"name": "Danny Marsh", "number": 10, "position": "CAM"},
                {"name": "Kieran Shaw", "number": 7, "position": "RW"},
                {"name": "Max Turner", "number": 11, "position": "LW"},
                {"name": "Roshan Palem", "number": 9, "position": "ST", "captain": True},
            ],
        },
    },
}

TEAMS = ["Kryptonites", "Ultras"]

# How often each position touches the ball (midfielders more, keepers less)
POSITION_WEIGHT = {
    "GK": 2, "RB": 6, "LB": 6, "CB": 7,
    "CDM": 9, "CM": 9, "CAM": 10, "RW": 7, "LW": 7, "ST": 5,
}

# ---------------------------------------------------------------------------
# 2. Phases: the storyline
#    control  = how strong each team is on the ball (affects pass success)
#    pressing = which team is pressing high (puts the other team under pressure)
#    star     = player who gets extra touches in that phase
# ---------------------------------------------------------------------------

PHASES = [
    {"start": 0,  "end": 30, "control": {"Kryptonites": 0.10, "Ultras": -0.05},
     "pressing": "Kryptonites", "star": {"Kryptonites": "Jamie Rowe"}},
    {"start": 30, "end": 45, "control": {"Kryptonites": 0.05, "Ultras": -0.03},
     "pressing": None, "star": {}},
    {"start": 45, "end": 60, "control": {"Kryptonites": -0.06, "Ultras": 0.04},
     "pressing": "Ultras", "star": {}},
    {"start": 60, "end": 85, "control": {"Kryptonites": -0.08, "Ultras": 0.08},
     "pressing": "Ultras", "star": {"Ultras": "Danny Marsh"}},
    {"start": 85, "end": 91, "control": {"Kryptonites": 0.02, "Ultras": 0.02},
     "pressing": None, "star": {}},
]

# ---------------------------------------------------------------------------
# 3. Scripted goals (seconds from kick-off)
# ---------------------------------------------------------------------------

GOALS = [
    {"time": 24 * 60 + 10, "team": "Kryptonites", "scorer": "Callum Reed", "assist": "Jamie Rowe"},
    {"time": 63 * 60 + 40, "team": "Ultras", "scorer": "Roshan Palem", "assist": "Kieran Shaw"},
    {"time": 87 * 60 + 5,  "team": "Ultras", "scorer": "Danny Marsh", "assist": "Roshan Palem"},
]

# Players in the scripted goals never get sent off, so the story always holds
PROTECTED = {name for g in GOALS for name in (g["scorer"], g["assist"])}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

events = []
cards = {}       # player -> yellow cards so far
sent_off = set() # players with a red card
score = {"Kryptonites": 0, "Ultras": 0}


def other(team):
    return "Ultras" if team == "Kryptonites" else "Kryptonites"


def phase_at(seconds):
    minute = seconds / 60
    for phase in PHASES:
        if phase["start"] <= minute < phase["end"]:
            return phase
    return PHASES[-1]


def players_of(team):
    return MATCH_INFO["teams"][team]["players"]


def pick_player(team, phase, exclude=None, outfield_only=False):
    """Pick who gets the ball. Midfielders and the phase's star get more touches."""
    names, weights = [], []
    for p in players_of(team):
        if p["name"] == exclude or p["name"] in sent_off:
            continue
        if outfield_only and p["position"] == "GK":
            continue
        weight = POSITION_WEIGHT[p["position"]]
        if phase["star"].get(team) == p["name"]:
            weight *= 3
        names.append(p["name"])
        weights.append(weight)
    return random.choices(names, weights=weights)[0]


def clamp(value, low=1, high=99):
    return max(low, min(high, round(value, 1)))


def add_event(seconds, **fields):
    event = {
        "id": len(events) + 1,
        "minute": int(seconds // 60),
        "second": int(seconds % 60),
        **fields,
    }
    events.append(event)
    return event


def flip(pos):
    """Turn a position into the other team's point of view."""
    return [clamp(100 - pos[0]), clamp(100 - pos[1])]


# ---------------------------------------------------------------------------
# 4. A normal possession chain
# ---------------------------------------------------------------------------

def keeper_of(team):
    return next(p["name"] for p in players_of(team) if p["position"] == "GK")


def corner_taker(team, phase):
    names = [p["name"] for p in players_of(team)
             if p["position"] in ("RW", "LW", "CAM") and p["name"] not in sent_off]
    return random.choice(names)


def play_chain(clock, team, start, half_end, counter=False):
    """One team keeps the ball until they lose it or shoot.
    Returns (new clock, team with the ball next, where the ball is, is_counter)."""
    phase = phase_at(clock)
    ball = start
    holder = pick_player(team, phase, outfield_only=ball[0] > 20)
    fast_passes = 0
    set_piece = False  # True right after a corner is delivered into the box

    if counter:
        # Won the ball deep and broke forward quickly
        add_event(clock, type="counter_attack", team=team, player=holder, position=ball)
        fast_passes = 2

    while clock < half_end:
        phase = phase_at(clock)
        pressed = phase["pressing"] == other(team)
        under_pressure = random.random() < (0.55 if pressed else 0.2)

        # Occasional sprint, used for speed alerts on screen
        if random.random() < (0.25 if fast_passes else 0.04):
            add_event(clock, type="sprint", team=team, player=holder,
                      top_speed_kmh=round(random.uniform(27, 35), 1),
                      distance_m=round(random.uniform(15, 45), 1))

        # Near the box: chance to shoot (much higher on a counter or from a corner)
        if set_piece:
            shoot_chance = 0.45
        elif counter:
            shoot_chance = 0.3
        else:
            shoot_chance = 0.09
        if ball[0] > (72 if counter else 80) and random.random() < shoot_chance:
            roll = random.random()
            outcome = "saved" if roll < 0.4 else "blocked" if roll < 0.65 else "off_target"
            speed = round(random.uniform(60, 115), 1)
            add_event(clock, type="shot", team=team, player=holder, start=ball,
                      shot_speed_kmh=speed, on_target=outcome == "saved",
                      outcome=outcome, under_pressure=under_pressure,
                      header=set_piece, from_counter=counter)
            clock += random.uniform(2, 4)

            if outcome == "saved":
                add_event(clock, type="save", team=other(team), player=keeper_of(other(team)),
                          shooter=holder, shot_speed_kmh=speed)

            # Saves pushed wide and blocks often go out for a corner
            corner_chance = {"saved": 0.35, "blocked": 0.5, "off_target": 0.0}[outcome]
            if random.random() < corner_chance:
                clock += random.uniform(12, 25)
                side = random.choice(["left", "right"])
                taker = corner_taker(team, phase)
                ball = [99, 2 if side == "left" else 98]
                add_event(clock, type="corner", team=team, player=taker, side=side, position=ball)
                clock += random.uniform(3, 6)

                # The delivery into the box
                target = [clamp(random.uniform(88, 95)), clamp(random.uniform(35, 65))]
                receiver = pick_player(team, phase, exclude=taker, outfield_only=True)
                won = random.random() < 0.45
                add_event(clock, type="pass", team=team, player=taker,
                          receiver=receiver if won else None, start=ball, end=target,
                          outcome="success" if won else "fail", under_pressure=True, corner=True)
                clock += random.uniform(1, 2)
                if won:
                    holder, ball, set_piece, counter = receiver, target, True, False
                    continue
                defender = pick_player(other(team), phase, outfield_only=True)
                where = flip(target)
                add_event(clock, type="clearance", team=other(team), player=defender, position=where)
                add_event(clock, type="possession_change", team=other(team), position=where)
                return clock + random.uniform(1, 3), other(team), where, False

            clock += random.uniform(6, 16)
            return clock, other(team), [8, 50], False  # goal kick or keeper's ball

        set_piece = False

        # Small chance of a foul by the defending team (more when pressing hard)
        if random.random() < (0.035 if pressed else 0.025):
            fouler = pick_player(other(team), phase, outfield_only=True)
            hard = random.random() < 0.3
            add_event(clock, type="foul", team=other(team), player=fouler,
                      fouled=holder, position=flip(ball), hard=hard)
            clock += random.uniform(5, 10)

            # Hard fouls can bring a yellow card (two yellows = red)
            if hard and random.random() < 0.6 and fouler not in PROTECTED:
                cards[fouler] = cards.get(fouler, 0) + 1
                if cards[fouler] == 1:
                    add_event(clock, type="yellow_card", team=other(team), player=fouler,
                              reason="hard foul", fouled=holder)
                elif fouler not in sent_off:
                    sent_off.add(fouler)
                    add_event(clock, type="red_card", team=other(team), player=fouler,
                              reason="second yellow", fouled=holder)
                clock += random.uniform(15, 30)

            # ...and sometimes an injury: treatment on the pitch, then play on
            if hard and random.random() < 0.3:
                add_event(clock, type="injury", team=team, player=holder,
                          treatment_seconds=int(random.uniform(45, 120)))
                clock += random.uniform(60, 120)

            clock += random.uniform(5, 15)
            continue  # same team keeps the ball for the free kick

        # Pass (a counter-attack starts with quick, direct forward passes)
        if fast_passes:
            long_ball = True
            forward = random.uniform(18, 30)
            sideways = random.uniform(-15, 15)
        else:
            long_ball = random.random() < 0.12
            forward = random.uniform(10, 35) if long_ball else random.uniform(-6, 14)
            sideways = random.uniform(-25, 25) if long_ball else random.uniform(-14, 14)
        target = [clamp(ball[0] + forward), clamp(ball[1] + sideways, 3, 97)]

        if fast_passes:
            success_chance = 0.8
            fast_passes -= 1
        else:
            success_chance = 0.85 + phase["control"].get(team, 0)
            if under_pressure:
                success_chance -= 0.15
            if long_ball:
                success_chance -= 0.2
        success = random.random() < success_chance

        receiver = pick_player(team, phase, exclude=holder, outfield_only=True)
        add_event(clock, type="pass", team=team, player=holder,
                  receiver=receiver if success else None,
                  start=ball, end=target,
                  outcome="success" if success else "fail",
                  under_pressure=under_pressure)
        clock += random.uniform(1.5, 3) if counter else random.uniform(2, 5)

        if success:
            holder = receiver
            ball = target
            continue

        # Lost the ball: tackle if pressed, otherwise an interception
        winner = other(team)
        defender = pick_player(winner, phase_at(clock), outfield_only=True)
        where = flip(target)
        add_event(clock, type="tackle" if under_pressure else "interception",
                  team=winner, player=defender, position=where)
        add_event(clock, type="possession_change", team=winner, position=where)
        clock += random.uniform(1, 3)
        # Won it in their own half: sometimes they break on the counter
        breaks = where[0] < 45 and random.random() < 0.12
        return clock, winner, where, breaks

    return clock, team, ball, counter


# ---------------------------------------------------------------------------
# 5. A scripted goal with a short build-up
# ---------------------------------------------------------------------------

def play_goal(goal):
    team = goal["team"]
    clock = goal["time"] - 14
    phase = phase_at(clock)
    ball = [48, 50]
    holder = pick_player(team, phase, exclude=goal["assist"], outfield_only=True)

    # Three build-up passes moving towards goal
    for x in (60, 70, 78):
        receiver = pick_player(team, phase, exclude=holder, outfield_only=True)
        if receiver in (goal["scorer"], goal["assist"]):
            receiver = pick_player(team, phase, exclude=receiver, outfield_only=True)
        target = [x, clamp(random.uniform(30, 70))]
        add_event(clock, type="pass", team=team, player=holder, receiver=receiver,
                  start=ball, end=target, outcome="success", under_pressure=False)
        holder, ball = receiver, target
        clock += 3

    # Pass to the assister, then the assist itself
    target = [84, clamp(random.uniform(25, 75))]
    add_event(clock, type="pass", team=team, player=holder, receiver=goal["assist"],
              start=ball, end=target, outcome="success", under_pressure=False)
    ball = target
    clock = goal["time"] - 1

    target = [91, clamp(random.uniform(40, 60))]
    add_event(clock, type="pass", team=team, player=goal["assist"], receiver=goal["scorer"],
              start=ball, end=target, outcome="success", under_pressure=False, assist=True)

    score[team] += 1
    add_event(goal["time"], type="shot", team=team, player=goal["scorer"], start=target,
              shot_speed_kmh=round(random.uniform(85, 118), 1),
              on_target=True, outcome="goal", under_pressure=False)
    add_event(goal["time"], type="goal", team=team, player=goal["scorer"],
              assist=goal["assist"], score=dict(score))

    # Celebration, then the other team kicks off
    return goal["time"] + 60, other(team)


# ---------------------------------------------------------------------------
# 6. Run the whole match
# ---------------------------------------------------------------------------

def play_half(clock, half_end, team):
    add_event(clock, type="kickoff", team=team, player=pick_player(team, phase_at(clock)))
    ball = [50, 50]
    goals_left = [g for g in GOALS if clock <= g["time"] < half_end]
    counter = False

    while clock < half_end:
        if goals_left and clock >= goals_left[0]["time"] - 30:
            clock, team = play_goal(goals_left.pop(0))
            add_event(clock, type="kickoff", team=team, player=pick_player(team, phase_at(clock)))
            ball = [50, 50]
            counter = False
            continue
        clock, team, ball, counter = play_chain(clock, team, ball, half_end, counter)
        clock += random.uniform(1, 4)


def generate():
    play_half(0, 45 * 60, "Kryptonites")
    add_event(45 * 60, type="half_time", score=dict(score))
    play_half(45 * 60, 90 * 60, "Ultras")
    add_event(90 * 60, type="full_time", score=dict(score))

    events.sort(key=lambda e: (e["minute"], e["second"], e["id"]))
    for i, event in enumerate(events, start=1):
        event["id"] = i

    match = {"info": MATCH_INFO, "seed": SEED, "events": events}
    out = Path(__file__).resolve().parent.parent / "data" / "match_001.json"
    out.write_text(json.dumps(match, indent=2))

    types = {}
    for e in events:
        types[e["type"]] = types.get(e["type"], 0) + 1
    print(f"Saved {len(events)} events to {out}")
    print(f"Final score: Kryptonites {score['Kryptonites']} - {score['Ultras']} Ultras")
    print("Event counts:", types)


if __name__ == "__main__":
    generate()
