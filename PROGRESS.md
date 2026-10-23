# AgPitch - progress notes

Keeping track of what I've built and what's left, so I don't lose the thread between sessions.

## What I decided
- Going for the Synthetic Match Insights Engine challenge
- My fake match is Kryptonites vs Ultras. Ultras win 2-1 (I'm the Ultras captain: one goal, and the assist for the winner)
- Insights in English and Telugu (a lot of Telugu fans started watching football after the 2026 World Cup, and there's barely any coverage in Telugu)
- Agents run on Azure AI Foundry with gpt-5-mini, and I'm writing the orchestration myself in Python
- Backend is FastAPI, streaming live updates with Server-Sent Events
- Frontend in Next.js
- Hosting on Azure Container Apps for the backend and Static Web Apps for the frontend
- Deadline is 27 Oct, but I want to submit that morning, not last minute

## Done so far
- Repo, Python 3.13 venv, folder structure
- generator.py: builds the synthetic match from a scripted storyline (Kryptonites control early, Ultras press after half time and turn it around). Fixed seed, so it's the same match every run
- stats.py: plain Python, no AI. Possession, pass accuracy, pass distance and a 0-10 pass difficulty score, pressure, shot speed, player stats. Flags key moments with simple rules (turnover streaks, pressure spikes, momentum swings, speed alerts)
- main.py: FastAPI server that replays the match live over SSE, with speed and start-minute options
- agents.py: four agents in Foundry (Pundit, Overlay, Fan, Recap), created from code so the instructions live in the repo. JSON in, JSON out
- orchestrator.py: sends key moments to the agents in the background so the stream never freezes. Pundit and Overlay run once per moment, Fan runs per viewer. Results are cached, and if Azure fails the stream still sends a basic card
- Checked the Telugu output myself. The agent was mixing up ని and నీ and translating word by word, so I added Telugu style rules with a real commentator phrase as the example ("గేమ్ Ultras చేతుల్లోకి వెళ్తోంది")

## Things I noticed
- Each insight takes about 10-15 seconds from the agents, fine for TV-style graphics. Replays come from the cache and are instant
- Always start the server with `python -m uvicorn backend.app.main:app --reload`, plain `uvicorn` picked up my global Python instead of the venv

## Still to do
- Check the Telugu again after updating the agents
- Next.js frontend: live feed, insight cards, mode / club / player / language switcher
- Deploy to Azure
- README, demo video (under 2 min), pitch, submit