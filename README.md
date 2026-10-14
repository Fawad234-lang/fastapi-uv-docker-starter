# Project API — Task 01

A minimal, reproducible FastAPI service for local development with Python 3.12+, `uv`, and Docker Compose.

## Prerequisites

- Local run: Python 3.12+ and [`uv`](https://docs.astral.sh/uv/)
- Container run: Docker Desktop (Windows/macOS) or Docker Engine with the Compose plugin
- Git and a GitHub account for submission

## 1. Run locally with uv

From the repository root:

```bash
# Resolve dependencies and create uv.lock (first setup only; commit this file)
uv lock

# Install exactly the versions in uv.lock
uv sync --frozen

# Start the development server
uv run --frozen uvicorn project_api.main:app --app-dir src --reload
```

Open <http://127.0.0.1:8000/health>. Interactive API documentation is at <http://127.0.0.1:8000/docs>.

Expected response (HTTP 200):

```json
{"status":"ok","version":"0.1.0"}
```

In a second terminal, run the smoke check:

```bash
python scripts/verify_health.py
```

Stop the server with `Ctrl+C`.

## 2. Run with Docker Compose

Docker builds the image with Python and dependencies inside the container, so a local Python installation is not needed for this path. Docker itself must be installed and running.

```bash
docker compose up --build
```

Open <http://127.0.0.1:8000/health>. The Compose service mounts `src/` and enables Uvicorn hot reload. In another terminal, verify the response and restart recovery:

```bash
python scripts/verify_health.py
docker compose restart api
python scripts/verify_health.py
```

Stop and remove the container:

```bash
docker compose down
```

PowerShell alternative for checking the endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

## Environment variables and secrets

`.env.example` documents safe local defaults. If you need a local `.env`, copy the example and edit it; `.env` is ignored by Git. Do not place real credentials in `.env.example` or commit `.env`.

## Project layout

```text
.
├── .dockerignore              # Excludes local files from Docker build context
├── .env.example               # Safe sample configuration only
├── .gitignore                 # Ignores secrets, virtualenvs, and generated files
├── Dockerfile                 # Container image for the API
├── compose.yaml               # Development service, port mapping, source mount
├── pyproject.toml             # Project metadata and dependency declarations
├── uv.lock                    # Exact resolved dependency versions (commit this)
├── scripts/verify_health.py   # Standard-library HTTP smoke check
└── src/project_api/
    ├── __init__.py            # Package version
    └── main.py                # FastAPI app and GET /health
```

## Git branch and pull request

Create an empty GitHub repository (do not add a README/license there, because this folder already has project files). Then, from this folder, run:

```bash
git init
git add .
git commit -m "Task 01: project setup"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
git switch -c task/01-project-setup
git push -u origin task/01-project-setup
```

Replace the placeholder in the remote URL with your GitHub username and repository name. On GitHub, open a pull request with base `main` and compare branch `task/01-project-setup`. Include the actual terminal output or screenshots from both the `uv` and Docker checks, and describe the project layout using the section above. Do not claim a check passed unless you ran it.

## Troubleshooting

- If `uv lock` cannot connect to PyPI, check your internet connection or network restrictions, then retry. Do not hand-write `uv.lock`; it must contain a real dependency resolution.
- If port 8000 is already in use, stop the other process or change the host-side port in `compose.yaml`.
- If Docker cannot start, make sure Docker Desktop/Engine is running before retrying `docker compose up --build`.
