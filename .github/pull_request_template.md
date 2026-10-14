## Summary

- Added a minimal FastAPI application with `GET /health`.
- Added `uv` project configuration and lockfile for reproducible dependency installation.
- Added Dockerfile and Compose development service with source hot reload.
- Documented setup, verification, and project layout.

## Verification evidence

- [ ] `uv sync --frozen` completed successfully
- [ ] API started with `uv run --frozen ...`
- [ ] `GET /health` returned HTTP 200 and valid JSON
- [ ] `docker compose up --build` completed successfully
- [ ] Health check passed before and after `docker compose restart api`
- [ ] Added actual terminal output or screenshots below / as attachments

Paste actual command output or attach screenshots here. Remove any secrets before sharing.

## Project layout

- `src/project_api/main.py`: FastAPI application and health endpoint
- `pyproject.toml` / `uv.lock`: project metadata and pinned dependency resolution
- `Dockerfile` / `compose.yaml`: container build and development runtime
- `scripts/verify_health.py`: HTTP smoke check
- `.gitignore` / `.dockerignore` / `.env.example`: repository hygiene and safe configuration example
