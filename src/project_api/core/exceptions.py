"""Application-level exceptions with safe public messages."""


class AppError(Exception):
    """Base error safe to translate into an HTTP response."""

    status_code = 500
    code = "application_error"
    public_message = "The request could not be completed."


class LLMConfigurationError(AppError):
    status_code = 503
    code = "llm_not_configured"
    public_message = "The chatbot service is not configured correctly."


class LLMAuthenticationError(AppError):
    status_code = 502
    code = "llm_authentication_failed"
    public_message = "The LLM provider rejected the configured credentials."


class LLMRateLimitError(AppError):
    status_code = 429
    code = "llm_rate_limited"
    public_message = "The LLM provider rate limit or quota was reached. Please retry later."


class LLMTimeoutError(AppError):
    status_code = 503
    code = "llm_timeout"
    public_message = "The chatbot service did not respond in time. Please retry."


class LLMUnavailableError(AppError):
    status_code = 503
    code = "llm_unavailable"
    public_message = "The chatbot service is temporarily unavailable."


class MessageNotFoundError(AppError):
    status_code = 404
    code = "message_not_found"

    def __init__(self, message_id: int) -> None:
        self.public_message = f"Message with ID {message_id} was not found."
        super().__init__(self.public_message)
