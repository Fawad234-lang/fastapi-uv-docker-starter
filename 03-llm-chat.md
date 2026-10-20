# Task 03 — Connect the First LLM

## Learning goal

Learn what an LLM API call actually needs before introducing LangChain or LangGraph abstractions.

> Use the selected LLM provider's official Python SDK in this task. Do not use LangChain or LangGraph yet.

## User story

As an API user, I want to send a prompt to the chatbot and receive an AI-generated answer.

## API to build

### `POST /api/v1/chat`

Request:

```json
{
  "message": "Explain dependency injection in simple words."
}
```

Successful response — `200 OK`:

```json
{
  "answer": "Dependency injection means...",
  "model": "configured-model-name",
  "usage": {
    "input_tokens": 12,
    "output_tokens": 48
  }
}
```

Token usage may be nullable if the provider does not return it.

## Implementation requirements

- Create one asynchronous LLM generation function or small service, for example:

```python
async def generate_reply(message: str) -> LLMResult:
    ...
```

- Call the provider through its official SDK.
- Read the API key, model name, and timeout from environment settings.
- Keep the provider call outside the FastAPI route handler.
- Validate and trim the incoming message.
- Set a maximum input length and a maximum generated-output size.
- Convert provider authentication, rate-limit, timeout, and unavailable errors into safe application errors.
- Never return API keys, raw provider responses, stack traces, or internal exception messages.

## Acceptance criteria

- A valid message returns a non-empty LLM answer.
- Empty or whitespace-only messages return `422 Unprocessable Entity`.
- Oversized messages return `422 Unprocessable Entity`.
- Missing server configuration causes a clear startup/configuration failure.
- Provider authentication failure is handled without exposing credentials.
- Provider timeout or outage returns a safe `503 Service Unavailable` response.
- Provider rate limiting returns a documented safe response such as `429 Too Many Requests` or `503 Service Unavailable`.
- The route delegates generation to the LLM function/service rather than containing SDK code.
- Automated tests do not make real paid API calls.

## Verification

Add tests for:

1. A successful response using a fake LLM function.
2. Empty input.
3. Oversized input.
4. Provider timeout.
5. Provider authentication failure.
6. Provider rate limiting.

Make one real local LLM call for the demonstration, but keep real credentials and real network calls out of automated tests and CI.

## Submission

Push branch `task/03-llm-chat` and open a pull request containing:

- The endpoint, generation function/service, schemas, and tests.
- An updated `.env.example` containing variable names only.
- One sample request and response with secrets removed.
- A short explanation of input tokens, output tokens, timeout, and approximate cost considerations.
- Confirmation that LangChain and LangGraph have not been added yet.

## Future connection

The provider-specific function will be placed behind a cleaner interface in Task 04. LangGraph will replace direct workflow orchestration later, after students understand persistence and conversation history. LangChain components may be introduced at that point only where they help LangGraph integration.
