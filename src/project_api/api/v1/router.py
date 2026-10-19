"""Compose the versioned API routes."""

from fastapi import APIRouter

from project_api.api.v1.chat import router as chat_router
from project_api.api.v1.health import router as health_router
from project_api.api.v1.messages import router as messages_router

api_router = APIRouter()
api_router.include_router(chat_router, prefix="/api/v1")
api_router.include_router(messages_router, prefix="/api/v1")
api_router.include_router(health_router)
