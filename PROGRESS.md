# AgPitch - progress notes

Keeping track of what I've built and what's left, not losing the thread between sessions.

## What I decided
- Going for the Synthetic Match Insights Engine challenge
- My fake match is Kryptonites vs Ultras
- Insights in English and Telugu (a lot of Telugu fans started watching football after the 2026 World Cup, and there's barely any coverage in Telugu)
- Agents run on Azure AI Foundry with gpt-5-mini, and I'm writing the orchestration myself in Python
- Backend is FastAPI, streaming live updates with Server-Sent Events
- Frontend in Next.js
- Hosting on Azure Container Apps for the backend and Static Web Apps for the frontend
- Deadline is 27 Oct, but I want to submit that morning, not last minute

## Done so far
- Created the repo and cloned it
- Set up Python 3.13 with a virtual environment
- Made the folder structure

## Still to do
- Match data generator
- Stats engine
- FastAPI server with the live stream
- The AI agents and wiring them together
- Frontend
- Deploy, record the demo, submit