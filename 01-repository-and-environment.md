# Task 01 — Repository and Local Environment

## User story

As a developer, I want a reproducible project skeleton so that anyone can run the API locally with the same tools.

## Requirements

- Create a GitHub repository and initialize a Python 3.12+ project with uv.
- Add FastAPI, Uvicorn, a `src/` package, `.gitignore`, `.env.example`, and concise setup instructions.
- Add `GET /health` returning service status and version.
- Add a Dockerfile and Docker Compose service for the API with hot reload for development.

## Acceptance criteria

- `uv sync` installs from the lockfile and `uv run` starts the API.
- `docker compose up --build` starts the API without a local Python install.
- `/health` returns HTTP 200 and valid JSON.
- No real secret, virtual environment, or generated cache is committed.

## Verification

Run the API both with uv and Compose; call `/health`; restart the container and confirm it returns.

## Submission

Push branch `task/01-project-setup`. Open a PR containing setup instructions, command output or screenshot, and a short note explaining the project layout.
