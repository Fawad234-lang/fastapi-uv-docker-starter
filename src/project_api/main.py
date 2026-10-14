from fastapi import FastAPI

from project_api import __version__

app = FastAPI(title="Project API", version=__version__)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Return basic service health information."""
    return {"status": "ok", "version": __version__}
