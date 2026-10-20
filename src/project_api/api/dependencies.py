"""FastAPI dependencies for API routes."""

from project_api.core.config import get_settings
from project_api.core.exceptions import LLMConfigurationError
from project_api.services.llm import GeminiLLMService, LLMService


def get_llm_service() -> LLMService:
    """Build the configured provider service; tests may override this dependency."""
    settings = get_settings()
    if settings.gemini_api_key is None or not settings.gemini_api_key.get_secret_value().strip():
        raise LLMConfigurationError()
    return GeminiLLMService(settings)
