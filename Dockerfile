# AgPitch backend: FastAPI + the agent orchestrator.
# Azure builds this image in the cloud (az containerapp up --source .),
# so Docker is not needed on the developer's machine.
FROM python:3.13-slim

WORKDIR /app

# Install packages first, so this layer is reused when only the code changes
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# The app, the demo match and the prepared agent answers
COPY backend backend

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
