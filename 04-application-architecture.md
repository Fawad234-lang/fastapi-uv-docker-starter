# Task 04 — Refactor into a Maintainable FastAPI Architecture

## Learning goal

Learn separation of concerns, dependency injection, application configuration, and consistent error handling by refactoring the Task 03 chatbot without changing its public behavior.

> This is a refactoring task. Do not add PostgreSQL, authentication, LangChain, or LangGraph yet.

## User story

As a developer, I want the chatbot backend divided into clear layers so that it is easy to test, maintain, and extend in later tasks.

## Required project structure

Students may make small naming changes, but the responsibilities must remain separate.

```text
src/
└── app/
    ├── main.py
    ├── api/
    │   ├── dependencies.py
    │   └── v1/
    │       ├── router.py
    │       └── chat.py
    ├── core/
    │   ├── config.py
    │   └── exceptions.py
    ├── schemas/
    │   └── chat.py
    └── services/
        └── llm.py
tests/
```

## Layer responsibilities

### `main.py`

- Create the FastAPI application.
- Register routers, middleware, and exception handlers.
- Do not place chatbot business logic here.

### API router

- Receive and validate HTTP requests.
- Call the injected LLM service.
- Return the declared response model and status code.
- Do not create the provider client or read environment variables directly.

### Schemas

- Define request, response, token-usage, and error models with Pydantic.
- Keep API models separate from provider-specific response objects.

### LLM service

- Define the interface used by the route, such as:

```python
from typing import Protocol


class LLMService(Protocol):
    async def generate_reply(self, message: str) -> LLMResult:
        ...
```

- Implement the interface using the provider selected in Task 03.
- Translate provider-specific responses and exceptions into application types.
- Prevent provider SDK objects from leaking into the API layer.

### Configuration

- Load the API key, model name, timeout, input limit, and output limit from environment variables.
- Use typed settings and validate required values.
- Cache or create settings once instead of reading the environment in every request.
- Keep `.env.example` updated without including real secrets.

### Dependencies

- Provide the LLM service through a FastAPI dependency.
- Allow tests to replace the real service with a fake by using dependency overrides.

## API behavior

Keep the Task 03 endpoint:

### `POST /api/v1/chat`

Request:

```json
{
  "message": "Why is separation of concerns useful?"
}
```

Successful response — `200 OK`:

```json
{
  "answer": "Separation of concerns helps...",
  "model": "configured-model-name",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 42
  }
}
```

The existing `/health` and message endpoints must continue to work.

## Application errors

Create application-level exceptions for at least:

- LLM provider unavailable or timed out.
- LLM provider rate limit reached.
- LLM provider authentication/configuration failure.

Register global exception handlers that convert these exceptions into consistent JSON responses. Routes must not catch every provider exception individually.

Example error response:

```json
{
  "error": {
    "code": "llm_unavailable",
    "message": "The chatbot service is temporarily unavailable.",
    "request_id": "7f3389b4-4d5b-4f29-a1f7-12a3456789ab"
  }
}
```

Do not expose provider response bodies, stack traces, credentials, or internal exception messages.

## Request ID middleware

- Accept an optional `X-Request-ID` header or generate a new request ID.
- Return the request ID in the `X-Request-ID` response header.
- Make it available to exception handlers.
- Validate or replace unsafe and excessively long client-provided values.

Full structured logging will be added later; only request correlation is required now.

## Acceptance criteria

- The application follows the required separation between API, schemas, services, configuration, and dependencies.
- `POST /api/v1/chat` retains the behavior established in Task 03.
- Route handlers contain no direct provider SDK calls.
- The LLM provider implementation can be replaced without changing the route.
- Tests replace the real LLM service through FastAPI dependency overrides.
- Missing required configuration produces a clear configuration/startup error.
- Provider-specific errors become safe, consistent API responses.
- Every response includes an `X-Request-ID` header.
- Error responses include the matching request ID.
- Existing endpoints and previous automated tests continue to pass.
- No LangChain, LangGraph, PostgreSQL, or authentication is added.

## Verification

Add tests for at least these cases:

1. Successful chat using an injected fake LLM service.
2. Provider timeout mapped to the expected safe error response.
3. Provider rate limit mapped to the chosen status code.
4. Provider authentication/configuration failure does not expose secret details.
5. A supplied valid `X-Request-ID` is returned to the client.
6. A request without an ID receives a generated ID.
7. Existing health, message, and chat tests still pass.

Run the application once with the real provider after refactoring to confirm that the integration still works.

## Submission

Push branch `task/04-application-architecture` and open a pull request containing:

- The refactored application and tests.
- A short project directory tree.
- A brief explanation of the responsibility of each layer.
- An explanation of how dependency overrides prevent real paid LLM calls during tests.
- One sample success response and one safe error response showing their request IDs.
- Confirmation that no new product feature was added; the purpose was architecture and testability.

## Instructor review questions

1. What belongs in a FastAPI route, and what belongs in a service?
2. Why should provider SDK objects not be returned directly from the route?
3. How does dependency injection make the LLM integration easier to test?
4. Why should settings be validated once instead of reading environment variables throughout the code?
5. What is the value of a request ID when investigating an error?
6. If the class implementing `LLMService` changes, which parts of the application should remain unchanged?

## Expected evaluation cues

- The student can identify clear boundaries rather than only showing folders.
- Tests use a fake service through dependency overrides, not monkey-patching random internals.
- The router remains small and provider-independent.
- Configuration is typed, centralized, and secret-safe.
- Error handling distinguishes internal diagnostic details from safe client messages.
- The student understands that abstraction is being introduced because later tasks will add persistence, LangGraph, and tools.
