"""Provider-specific Gemini integration, kept separate from FastAPI routes."""

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import httpx

# Load local development values without overriding values already in the process.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env", override=False)


class LLMServiceError(Exception):
    """Base class for safe, provider-independent LLM errors."""


class LLMConfigurationError(LLMServiceError):
    """Required server-side configuration is missing or invalid."""


class LLMAuthenticationError(LLMServiceError):
    """The provider rejected the API credentials."""


class LLMRateLimitError(LLMServiceError):
    """The provider rate limit or quota was reached."""


class LLMRequestTimeoutError(LLMServiceError):
    """The provider did not respond before the configured timeout."""


class LLMUnavailableError(LLMServiceError):
    """The provider could not complete the request."""


@dataclass(frozen=True)
class LLMResult:
    """Provider answer with usage metadata normalized for the API."""

    answer: str
    model: str
    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True)
class _Settings:
    api_key: str
    model: str
    timeout_seconds: float
    max_output_tokens: int


def _read_settings() -> _Settings:
    """Read and validate runtime configuration without revealing secret values."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "").strip()
    if not api_key or not model:
        raise LLMConfigurationError("Required LLM configuration is missing.")

    try:
        timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "512"))
    except ValueError:
        raise LLMConfigurationError("LLM timeout or output-token configuration is invalid.") from None

    if timeout_seconds <= 0 or max_output_tokens < 1:
        raise LLMConfigurationError("LLM timeout or output-token configuration is invalid.")

    return _Settings(
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
        max_output_tokens=max_output_tokens,
    )


def _map_provider_error(exc: Exception) -> LLMServiceError:
    """Map provider failures to safe application-level exceptions."""
    code = getattr(exc, "code", None)
    status_text = str(getattr(exc, "status", "")).lower()
    message_text = str(getattr(exc, "message", "")).lower()

    if code == 429:
        return LLMRateLimitError()
    if code in (401, 403) or "api key" in message_text or "api_key_invalid" in status_text:
        return LLMAuthenticationError()
    if code in (408, 504):
        return LLMRequestTimeoutError()
    return LLMUnavailableError()


async def generate_reply(message: str) -> LLMResult:
    """Generate a single answer using Google's official asynchronous SDK."""
    settings = _read_settings()

    # Import only when an actual configured generation is requested. This also
    # lets mock-based tests exercise the API without making network calls.
    try:
        from google import genai
        from google.genai import errors, types
    except ImportError:
        raise LLMUnavailableError() from None

    client = genai.Client(
        api_key=settings.api_key,
        http_options=types.HttpOptions(timeout=int(settings.timeout_seconds * 1000)),
    )
    try:
        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=settings.model,
                    contents=message,
                    config=types.GenerateContentConfig(
                        max_output_tokens=settings.max_output_tokens,
                    ),
                ),
                timeout=settings.timeout_seconds,
            )
        except (asyncio.TimeoutError, TimeoutError, httpx.TimeoutException):
            raise LLMRequestTimeoutError() from None
        except errors.APIError as exc:
            raise _map_provider_error(exc) from None
        except Exception:
            # Do not return SDK exception text, response bodies, or credentials.
            raise LLMUnavailableError() from None

        answer = (response.text or "").strip()
        if not answer:
            raise LLMUnavailableError()

        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", None) if usage else None
        output_tokens = getattr(usage, "candidates_token_count", None) if usage else None
        return LLMResult(
            answer=answer,
            model=settings.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    finally:
        # Close both clients to release their HTTP resources.
        try:
            await client.aio.aclose()
        except Exception:
            pass
        try:
            client.close()
        except Exception:
            pass
