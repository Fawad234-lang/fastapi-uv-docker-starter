"""LLM interface and Gemini implementation."""

import asyncio
from dataclasses import dataclass
from typing import Protocol

import httpx

from project_api.core.config import Settings
from project_api.core.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailableError,
)


@dataclass(frozen=True)
class LLMResult:
    """Normalized provider result; no SDK object leaks outside this service."""

    answer: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


class LLMService(Protocol):
    """Interface that route handlers depend on, rather than Gemini itself."""

    async def generate_reply(self, message: str) -> LLMResult:
        ...


class GeminiLLMService:
    """Implementation of LLMService using Google's official async SDK."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def generate_reply(self, message: str) -> LLMResult:
        # Import here so mocked services do not need SDK access or credentials.
        try:
            from google import genai
            from google.genai import errors, types
        except ImportError:
            raise LLMUnavailableError() from None

        api_key = self._settings.gemini_api_key
        if api_key is None or not api_key.get_secret_value().strip():
            from project_api.core.exceptions import LLMConfigurationError
            raise LLMConfigurationError() from None

        client = genai.Client(
            api_key=api_key.get_secret_value(),
            http_options=types.HttpOptions(
                timeout=int(self._settings.llm_timeout_seconds * 1000)
            ),
        )
        try:
            try:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=self._settings.gemini_model,
                        contents=message,
                        config=types.GenerateContentConfig(
                            max_output_tokens=self._settings.llm_max_output_tokens
                        ),
                    ),
                    timeout=self._settings.llm_timeout_seconds,
                )
            except (asyncio.TimeoutError, TimeoutError, httpx.TimeoutException):
                raise LLMTimeoutError() from None
            except errors.APIError as exc:
                status_code = getattr(exc, "code", None)
                provider_status = str(getattr(exc, "status", "")).lower()
                provider_message = str(getattr(exc, "message", "")).lower()
                if status_code == 429 or "resource_exhausted" in provider_status:
                    raise LLMRateLimitError() from None
                if (
                    status_code in (401, 403)
                    or "api key" in provider_message
                    or "api_key_invalid" in provider_status
                ):
                    raise LLMAuthenticationError() from None
                if status_code in (408, 504):
                    raise LLMTimeoutError() from None
                raise LLMUnavailableError() from None
            except (LLMAuthenticationError, LLMRateLimitError, LLMTimeoutError, LLMUnavailableError):
                raise
            except Exception:
                # Never expose raw SDK exception messages or provider response bodies.
                raise LLMUnavailableError() from None

            answer = (response.text or "").strip()
            if not answer:
                raise LLMUnavailableError()

            usage = getattr(response, "usage_metadata", None)
            return LLMResult(
                answer=answer,
                model=self._settings.gemini_model,
                input_tokens=(getattr(usage, "prompt_token_count", None) if usage else None),
                output_tokens=(getattr(usage, "candidates_token_count", None) if usage else None),
            )
        finally:
            try:
                await client.aio.aclose()
            except Exception:
                pass
            try:
                client.close()
            except Exception:
                pass
