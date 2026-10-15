
import pytest
from fastapi.testclient import TestClient

from project_api import main as api


@pytest.fixture
def client():
    """Give every test a clean in-memory message store."""
    api.messages.clear()
    api.next_message_id = 1

    with TestClient(api.app) as test_client:
        yield test_client

    api.messages.clear()
    api.next_message_id = 1


def test_create_valid_message(client):
    response = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "What is FastAPI?"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["role"] == "user"
    assert data["content"] == "What is FastAPI?"
    assert data["created_at"].endswith("+00:00") or data["created_at"].endswith("Z")


@pytest.mark.parametrize(
    "content",
    ["", "   ", "x" * 2001],
)
def test_reject_invalid_content(client, content):
    response = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": content},
    )

    assert response.status_code == 422


def test_reject_invalid_role(client):
    response = client.post(
        "/api/v1/messages",
        json={"role": "system", "content": "Hello"},
    )

    assert response.status_code == 422


def test_list_messages_with_pagination_and_role_filter(client):
    client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "First user message"},
    )
    client.post(
        "/api/v1/messages",
        json={"role": "assistant", "content": "Assistant reply"},
    )
    client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Second user message"},
    )

    response = client.get(
        "/api/v1/messages",
        params={"limit": 1, "offset": 1, "role": "user"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "Second user message"


def test_retrieve_existing_message(client):
    created = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Hello"},
    )

    message_id = created.json()["id"]
    response = client.get(f"/api/v1/messages/{message_id}")

    assert response.status_code == 200
    assert response.json()["content"] == "Hello"


def test_missing_message_returns_custom_404(client):
    response = client.get("/api/v1/messages/999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "message_not_found",
            "message": "Message with ID 999 was not found.",
        }
    }


def test_update_message(client):
    created = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Original content"},
    )
    message_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/messages/{message_id}",
        json={"content": "Updated content"},
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated content"
    assert response.json()["role"] == "user"


def test_delete_message_and_confirm_it_is_gone(client):
    created = client.post(
        "/api/v1/messages",
        json={"role": "user", "content": "Delete me"},
    )
    message_id = created.json()["id"]

    deleted = client.delete(f"/api/v1/messages/{message_id}")

    assert deleted.status_code == 204
    assert deleted.content == b""

    retrieved = client.get(f"/api/v1/messages/{message_id}")
    assert retrieved.status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"role": "system"},
    ],
)
def test_invalid_query_parameters_return_422(client, params):
    response = client.get("/api/v1/messages", params=params)

    assert response.status_code == 422


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_message_returns_404_for_all_item_operations(client, method):
    url = "/api/v1/messages/999"

    if method == "patch":
        response = client.patch(url, json={"content": "Updated"})
    else:
        response = getattr(client, method)(url)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "message_not_found"


def test_health_endpoint_still_works(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
