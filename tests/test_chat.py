"""Chat tests use dependency overrides; they never call a live provider."""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from project_api.api.dependencies import get_llm_service
from project_api.core.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from project_api.main import create_app
from project_api.services.llm import LLMResult


class FakeLLMService:
    def __init__(self, result=None, error=None):
        self.result = result or LLMResult(
            answer="Separation of concerns keeps each part focused on one responsibility.",
            model="test-model",
            input_tokens=10,
            output_tokens=42,
        )
        self.error = error
        self.last_message = None

    async def generate_reply(self, message: str) -> LLMResult:
        self.last_message = message
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def app():
    application = create_app()
    # Default fake keeps tests independent of local credentials and network.
    application.dependency_overrides[get_llm_service] = lambda: FakeLLMService()
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


def use_fake(app, service):
    app.dependency_overrides[get_llm_service] = lambda: service


def test_chat_success_uses_injected_fake_service(app, client):
    fake = FakeLLMService()
    use_fake(app, fake)
    response = client.post(
        "/api/v1/chat",
        json={"message": "  Why is separation of concerns useful?  "},
        headers={"X-Request-ID": "task04-test-123"},
    )
    assert response.status_code == 200
    assert fake.last_message == "Why is separation of concerns useful?"
    assert response.json() == {
        "answer": "Separation of concerns keeps each part focused on one responsibility.",
        "model": "test-model",
        "usage": {"input_tokens": 10, "output_tokens": 42},
    }
    assert response.headers["X-Request-ID"] == "task04-test-123"


@pytest.mark.parametrize("message", ["", "   ", "\t\n"])
def test_chat_rejects_empty_or_whitespace_message(client, message):
    response = client.post("/api/v1/chat", json={"message": message})
    assert response.status_code == 422
    assert response.headers.get("X-Request-ID")


def test_chat_rejects_oversized_message(client):
    response = client.post("/api/v1/chat", json={"message": "x" * 2001})
    assert response.status_code == 422


def test_timeout_maps_to_safe_503_and_matching_request_id(app, client):
    use_fake(app, FakeLLMService(error=LLMTimeoutError("PRIVATE TIMEOUT DETAIL")))
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello"},
        headers={"X-Request-ID": "timeout-case-42"},
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "llm_timeout"
    assert response.json()["error"]["request_id"] == "timeout-case-42"
    assert response.headers["X-Request-ID"] == "timeout-case-42"
    assert "PRIVATE TIMEOUT DETAIL" not in response.text


def test_rate_limit_maps_to_safe_429(app, client):
    use_fake(app, FakeLLMService(error=LLMRateLimitError("PRIVATE QUOTA DETAIL")))
    response = client.post("/api/v1/chat", json={"message": "Hello"})
    assert response.status_code == 429
    assert response.json()["error"]["code"] == "llm_rate_limited"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    assert "PRIVATE QUOTA DETAIL" not in response.text


@pytest.mark.parametrize(
    ("error", "status_code", "code", "secret"),
    [
        (LLMAuthenticationError("GEMINI KEY SECRET"), 502, "llm_authentication_failed", "GEMINI KEY SECRET"),
        (LLMConfigurationError("CONFIG SECRET"), 503, "llm_not_configured", "CONFIG SECRET"),
        (LLMUnavailableError("PRIVATE RESPONSE BODY"), 503, "llm_unavailable", "PRIVATE RESPONSE BODY"),
    ],
)
def test_provider_auth_configuration_and_outage_are_safe(app, client, error, status_code, code, secret):
    use_fake(app, FakeLLMService(error=error))
    response = client.post("/api/v1/chat", json={"message": "Hello"})
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    assert secret not in response.text


def test_request_without_id_gets_generated_id(client):
    response = client.get("/health")
    request_id = response.headers.get("X-Request-ID")
    assert request_id
    UUID(request_id)


def test_unsafe_request_id_is_replaced(client):
    response = client.get("/health", headers={"X-Request-ID": "bad\r\nheader"})
    request_id = response.headers["X-Request-ID"]
    assert request_id != "bad\r\nheader"
    UUID(request_id)


def test_health_endpoint_still_works(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_messages_endpoint_still_works(client):
    response = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Task 04 preserves Task 02."},
    )
    assert response.status_code == 201
