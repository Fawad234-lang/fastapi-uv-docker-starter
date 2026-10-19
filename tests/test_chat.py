import pytest
from fastapi.testclient import TestClient

from project_api import chat as chat_api
from project_api import main as api
from project_api.llm_service import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMRateLimitError,
    LLMRequestTimeoutError,
    LLMResult,
    LLMUnavailableError,
)


@pytest.fixture
def client():
    with TestClient(api.app) as test_client:
        yield test_client


def test_chat_success_uses_fake_llm(monkeypatch, client):
    called = {}

    async def fake_generate_reply(message):
        called["message"] = message
        return LLMResult(
            answer="Dependency injection supplies a dependency from outside a function.",
            model="test-model",
            input_tokens=12,
            output_tokens=18,
        )

    monkeypatch.setattr(chat_api, "generate_reply", fake_generate_reply)
    response = client.post(
        "/api/v1/chat",
        json={"message": "  Explain dependency injection.  "},
    )

    assert response.status_code == 200
    assert called["message"] == "Explain dependency injection."
    assert response.json() == {
        "answer": "Dependency injection supplies a dependency from outside a function.",
        "model": "test-model",
        "usage": {"input_tokens": 12, "output_tokens": 18},
    }


@pytest.mark.parametrize("message", ["", "   ", "\t\n"])
def test_chat_rejects_empty_or_whitespace_message(client, message):
    response = client.post("/api/v1/chat", json={"message": message})
    assert response.status_code == 422


def test_chat_rejects_oversized_message(client):
    response = client.post("/api/v1/chat", json={"message": "x" * 2001})
    assert response.status_code == 422


def test_chat_timeout_returns_safe_503(monkeypatch, client):
    async def fake_generate_reply(_message):
        raise LLMRequestTimeoutError("internal timeout detail must not leak")

    monkeypatch.setattr(chat_api, "generate_reply", fake_generate_reply)
    response = client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "llm_timeout"
    assert "internal timeout detail" not in response.text


def test_chat_provider_auth_failure_is_safe(monkeypatch, client):
    async def fake_generate_reply(_message):
        raise LLMAuthenticationError("API KEY SECRET MUST NOT LEAK")

    monkeypatch.setattr(chat_api, "generate_reply", fake_generate_reply)
    response = client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 502
    assert response.json()["detail"]["code"] == "llm_authentication_failed"
    assert "SECRET" not in response.text


def test_chat_rate_limit_returns_429(monkeypatch, client):
    async def fake_generate_reply(_message):
        raise LLMRateLimitError("provider detail must not leak")

    monkeypatch.setattr(chat_api, "generate_reply", fake_generate_reply)
    response = client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "llm_rate_limited"
    assert "provider detail" not in response.text


def test_chat_missing_configuration_returns_safe_503(monkeypatch, client):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    # This test deliberately exercises configuration validation, not the network.
    response = client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "llm_not_configured"


def test_chat_provider_outage_returns_safe_503(monkeypatch, client):
    async def fake_generate_reply(_message):
        raise LLMUnavailableError("private provider response must not leak")

    monkeypatch.setattr(chat_api, "generate_reply", fake_generate_reply)
    response = client.post("/api/v1/chat", json={"message": "Hello"})

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "llm_unavailable"
    assert "private provider response" not in response.text


def test_health_endpoint_still_works(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_messages_endpoint_still_works(client):
    response = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Task 03 must preserve Task 02."},
    )
    assert response.status_code == 201
