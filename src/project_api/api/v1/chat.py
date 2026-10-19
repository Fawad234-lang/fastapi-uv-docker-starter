"""Provider-independent chat endpoint."""

from fastapi import APIRouter, Depends, status

from project_api.api.dependencies import get_llm_service
from project_api.schemas.chat import ChatRequest, ChatResponse, TokenUsage
from project_api.services.llm import LLMResult, LLMService

router = APIRouter()


def _to_response(result: LLMResult) -> ChatResponse:
    """Convert service result into the public API response schema."""
    return ChatResponse(
        answer=result.answer,
        model=result.model,
        usage=TokenUsage(
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        ),
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["chat"],
    summary="Generate an LLM answer",
    description="Send one prompt to the configured language model.",
)
async def chat(
    payload: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> ChatResponse:
    """Delegate generation to the injected service; provider code stays elsewhere."""
    result = await llm_service.generate_reply(payload.message)
    return _to_response(result)
