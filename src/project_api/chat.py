"""FastAPI route for one-turn LLM chat."""

from fastapi import APIRouter, HTTPException, status

from project_api.chat_models import ChatRequest, ChatResponse, TokenUsage
from project_api.llm_service import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMRateLimitError,
    LLMRequestTimeoutError,
    LLMUnavailableError,
    generate_reply,
)

router = APIRouter()


def _safe_error(code: str, message: str, status_code: int) -> HTTPException:
    """Build a public error that contains no provider details or secrets."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


@router.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["chat"],
    summary="Generate an LLM answer",
    description="Send a single prompt to the configured language model.",
    responses={
        422: {"description": "The prompt is empty, whitespace-only, or longer than 2,000 characters."},
        429: {"description": "The provider rate limit or quota was reached."},
        502: {"description": "The provider rejected its configured credentials."},
        503: {"description": "The provider is unavailable, timed out, or is not configured."},
    },
)
async def chat(payload: ChatRequest) -> ChatResponse:
    """Delegate prompt generation to the provider service."""
    try:
        result = await generate_reply(payload.message)
    except LLMConfigurationError:
        raise _safe_error(
            "llm_not_configured",
            "The LLM service is not configured correctly.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from None
    except LLMAuthenticationError:
        raise _safe_error(
            "llm_authentication_failed",
            "The LLM provider rejected the configured credentials.",
            status.HTTP_502_BAD_GATEWAY,
        ) from None
    except LLMRateLimitError:
        raise _safe_error(
            "llm_rate_limited",
            "The LLM provider rate limit or quota was reached. Please retry later.",
            status.HTTP_429_TOO_MANY_REQUESTS,
        ) from None
    except LLMRequestTimeoutError:
        raise _safe_error(
            "llm_timeout",
            "The LLM provider did not respond in time. Please retry.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from None
    except LLMUnavailableError:
        raise _safe_error(
            "llm_unavailable",
            "The LLM provider could not complete the request. Please retry later.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from None

    return ChatResponse(
        answer=result.answer,
        model=result.model,
        usage=TokenUsage(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )
