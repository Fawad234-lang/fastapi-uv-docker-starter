"""Application health endpoint."""

from fastapi import APIRouter

from project_api.core.config import get_settings

router = APIRouter()


@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Return basic service health information."""
    return {"status": "ok", "version": get_settings().app_version}
