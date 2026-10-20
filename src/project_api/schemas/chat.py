"""Public request, response, and error schemas for chat."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from project_api.core.config import get_settings


class ChatRequest(BaseModel):
    """Prompt submitted to the chat endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(
        min_length=1,
        max_length=2000,
        description="Prompt to send to the language model (1–2,000 characters).",
        examples=["Explain dependency injection in simple words."],
    )

    @field_validator("message")
    @classmethod
    def enforce_configured_input_limit(cls, value: str) -> str:
        if not value:
            raise ValueError("Message must not be empty or whitespace only.")
        limit = get_settings().llm_max_input_length
        if len(value) > limit:
            raise ValueError(f"Message must not exceed {limit} characters.")
        return value


class TokenUsage(BaseModel):
    """Token usage reported by the provider, when available."""

    input_tokens: int | None = Field(description="Input tokens, or null when unavailable.")
    output_tokens: int | None = Field(description="Output tokens, or null when unavailable.")


class ChatResponse(BaseModel):
    """Provider-independent response returned to API clients."""

    answer: str = Field(min_length=1)
    model: str
    usage: TokenUsage


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
