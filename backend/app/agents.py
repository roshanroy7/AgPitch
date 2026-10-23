"""
AgPitch - AI agents on Azure AI Foundry

Four agents, each with one job:
  Pundit   explains WHY a key moment matters
  Overlay  turns the Pundit's explanation into an on-screen graphic
  Fan      rewrites the overlay for one viewer (mode, club, player, language)
  Recap    writes the full-time match summary

The agents live in your Foundry project. Their instructions are defined
here, in code, so they are versioned in GitHub.

Commands (run from the AgPitch folder, with the venv active):
    python -m backend.app.agents setup   create / update the 4 agents in Foundry
    python -m backend.app.agents test    run one real moment through the pipeline

Every agent receives JSON and replies with JSON, so the rest of the code
never has to guess what the AI meant.
"""

import json
import os
import sys
import time
from functools import lru_cache
from pathlib import Path

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, Reasoning
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

MODEL = os.environ.get("MODEL_DEPLOYMENT", "gpt-5-mini")
REASONING_EFFORT = os.environ.get("REASONING_EFFORT", "low")  # lower = faster

# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

SHARED_RULES = """
You work inside AgPitch, a live match-insights engine for football broadcasts.
The match data is synthetic. Never mention real clubs, real players or real leagues.
Only use facts and numbers that are in the input. Never invent statistics.
Reply with a single JSON object and nothing else. No markdown, no code fences.
"""

TELUGU_STYLE = """
TELUGU STYLE:
- Write the way a Telugu TV commentator speaks to fans: natural spoken Telugu in Telugu
  script, not a word-by-word translation of English.
- Use natural Telugu word order (subject, object, verb), with the verb at the end.
  Wrong: "నీ Ultras తీసుకుంటుంది గేమ్"   Right: "గేమ్ Ultras చేతుల్లోకి వెళ్తోంది"
- Prefer the phrases Telugu commentators really use over literal translations.
  Example: for "Ultras are taking control", say "గేమ్ Ultras చేతుల్లోకి వెళ్తోంది"
  (the game is going into Ultras' hands), not a word-by-word "take" sentence.
- "ని" after a noun is the object marker (గేమ్‌ని, బాల్‌ని). Never confuse it with "నీ" (your).
- Keep ONE consistent register: address the viewer as "మీరు" or not at all.
  For a supporter of the club involved, "మన" (our) is good: "మన Ultras".
- Keep player and club names in English letters.
- Keep football words Telugu fans say in English (goal, pass, press, possession,
  equaliser, momentum) in English letters, inside a proper Telugu sentence.
- Short, clear sentences. Read your sentence back once: if it sounds translated, rewrite it.
"""

PUNDIT = SHARED_RULES + """
You are the Pundit: an experienced football analyst.
Input: a key moment flagged by the stats engine, plus the current match stats.
Your job is to explain WHY the moment matters, not just WHAT happened.
Think about: control vs chaos, pressing and pressure, momentum, game rhythm,
how the score changes what each team must do, and individual impact.

Return JSON with exactly these keys:
{
  "theme": one of "control", "chaos", "pressure", "momentum", "rhythm", "individual", "result",
  "importance": a number from 1 (minor) to 5 (match-defining),
  "insight": 2 sentences explaining why this matters, max 45 words,
  "key_stat": {"label": short label, "value": the number or text from the input}
}
"""

OVERLAY = SHARED_RULES + """
You are the Overlay producer for a live TV broadcast.
Input: the original moment and the Pundit's analysis.
Turn it into one graphic that can sit on screen next to the live match.

Return JSON with exactly these keys:
{
  "graphic": one of "goal_banner", "stat_bar", "momentum_meter", "player_tag",
             "speed_alert", "pressure_gauge", "milestone_badge", "summary_card",
  "headline": max 6 words, punchy,
  "body": one line, max 18 words,
  "stat": {"label": short label, "value": value} or null,
  "duration_seconds": how long to show it, between 5 and 12,
  "priority": "high", "medium" or "low"
}
"""

FAN = SHARED_RULES + """
You are the Fan agent. You personalise one on-screen insight for one viewer.
Input: the overlay, the Pundit's analysis, and a viewer profile with:
  mode: "analyst" (wants numbers, tactics, precise terms),
        "casual" (simple words, emotion, no jargon, explain like a friend),
        "player_focus" (relate everything to their favourite player)
  favourite_club: the team the viewer supports, or null
  favourite_player: a player name, or null
  language: "en" (English) or "te" (Telugu)

Rules:
- Analyst and casual must feel genuinely different, not just shorter or longer.
- If the viewer's club is involved, speak to them as a supporter of that club.
- In player_focus mode, mention the favourite player and how the moment affects them,
  but never invent stats for that player.
- Talk TO the viewer about the match. Never give orders or advice to the players or team.
- For Telugu (language "te"), follow TELUGU STYLE below.
""" + TELUGU_STYLE + """
Return JSON with exactly these keys:
{
  "headline": max 6 words,
  "body": max 25 words,
  "stat": {"label": short label, "value": value} or null,
  "tone": a single word describing the tone you used
}
"""

RECAP = SHARED_RULES + """
You are the Recap writer. At full time you write the match summary.
Input: final stats, the list of key moments, and a viewer profile
(same fields as the Fan agent: mode, favourite_club, favourite_player, language).

Write the recap for that viewer: analyst = tactical and numerical,
casual = story-like and simple, player_focus = built around their player.
If language is "te", follow the TELUGU STYLE rules below.
""" + TELUGU_STYLE + """
Return JSON with exactly these keys:
{
  "title": max 8 words,
  "summary": 3 short paragraphs, max 150 words in total,
  "turning_point": one sentence naming the moment that decided the match,
  "player_of_the_match": {"name": a player from the input, "reason": one sentence}
}
"""

AGENTS = {
    "agpitch-pundit": PUNDIT,
    "agpitch-overlay": OVERLAY,
    "agpitch-fan": FAN,
    "agpitch-recap": RECAP,
}

# ---------------------------------------------------------------------------
# Azure clients (created once, then reused)
# ---------------------------------------------------------------------------


@lru_cache
def project_client():
    endpoint = os.environ.get("PROJECT_ENDPOINT")
    if not endpoint:
        raise RuntimeError("PROJECT_ENDPOINT is missing. Check your .env file.")
    return AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())


@lru_cache
def openai_client():
    return project_client().get_openai_client()


# ---------------------------------------------------------------------------
# Setup: create or update the agents in Foundry
# ---------------------------------------------------------------------------


def setup_agents():
    for name, instructions in AGENTS.items():
        agent = project_client().agents.create_version(
            agent_name=name,
            definition=PromptAgentDefinition(
                model=MODEL,
                instructions=instructions.strip(),
                reasoning=Reasoning(effort=REASONING_EFFORT),
            ),
            description=f"AgPitch {name.split('-')[1]} agent",
        )
        print(f"Ready: {agent.name} (version {agent.version})")


# ---------------------------------------------------------------------------
# Calling an agent
# ---------------------------------------------------------------------------


def parse_json(text):
    """Agents are told to reply with JSON only, but be forgiving."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Agent did not return JSON: {text[:200]}")
    return json.loads(text[start:end + 1])


def ask(agent_name, payload):
    """Send JSON to one agent and get JSON back."""
    response = openai_client().responses.create(
        input=json.dumps(payload, ensure_ascii=False),
        extra_body={"agent_reference": {"name": agent_name, "type": "agent_reference"}},
    )
    return parse_json(response.output_text)


def pundit(moment, stats):
    return ask("agpitch-pundit", {"moment": moment, "stats": stats})


def overlay(moment, analysis):
    return ask("agpitch-overlay", {"moment": moment, "analysis": analysis})


def fan(overlay_card, analysis, profile):
    return ask("agpitch-fan", {"overlay": overlay_card, "analysis": analysis, "viewer": profile})


def recap(final_stats, moments, profile):
    return ask("agpitch-recap", {"final_stats": final_stats, "key_moments": moments, "viewer": profile})


# ---------------------------------------------------------------------------
# Test: run your goal through the whole chain
# ---------------------------------------------------------------------------


def test():
    from .stats import StatsEngine

    match = json.loads((Path(__file__).resolve().parent.parent / "data" / "match_001.json").read_text())
    engine = StatsEngine(match["info"])
    goal = None
    for event in match["events"]:
        for m in engine.process(event):
            if m["kind"] == "goal" and m["player"] == "Roshan Palem":
                goal = m
        if goal:
            break
    stats = engine.snapshot()

    def timed(label, fn, *args):
        start = time.time()
        result = fn(*args)
        print(f"\n--- {label} ({time.time() - start:.1f}s) ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result

    print("Moment:", goal["headline"], f"at {goal['minute']}:{goal['second']:02d}")
    analysis = timed("Pundit", pundit, goal, stats)
    card = timed("Overlay", overlay, goal, analysis)
    timed("Fan: analyst, English", fan, card, analysis,
          {"mode": "analyst", "favourite_club": None, "favourite_player": None, "language": "en"})
    timed("Fan: casual Ultras fan, Telugu", fan, card, analysis,
          {"mode": "casual", "favourite_club": "Ultras", "favourite_player": None, "language": "te"})


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "setup":
        setup_agents()
    elif command == "test":
        test()
    else:
        print("Use: python -m backend.app.agents setup   or   python -m backend.app.agents test")
