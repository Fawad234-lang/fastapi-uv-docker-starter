"""In-memory messages endpoints retained from Task 02."""

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Query, Response, status

from project_api.core.exceptions import MessageNotFoundError
from project_api.models import MessageCreate, MessageResponse, MessageUpdate

router = APIRouter()

# Temporary in-memory storage. Messages disappear when the app restarts.
messages: dict[int, MessageResponse] = {}
next_message_id = 1


def reset_message_store() -> None:
    """Clear the in-memory store. Intended for tests and local development."""
    global next_message_id
    messages.clear()
    next_message_id = 1


def get_message_or_raise(message_id: int) -> MessageResponse:
    message = messages.get(message_id)
    if message is None:
        raise MessageNotFoundError(message_id)
    return message


@router.post(
    "/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["messages"],
    summary="Create a message",
    description="Create a user or assistant message in temporary memory.",
)
def create_message(payload: MessageCreate) -> MessageResponse:
    global next_message_id
    message = MessageResponse(
        id=next_message_id,
        role=payload.role,
        content=payload.content,
        created_at=datetime.now(timezone.utc),
    )
    messages[message.id] = message
    next_message_id += 1
    return message


@router.get(
    "/messages",
    response_model=list[MessageResponse],
    status_code=status.HTTP_200_OK,
    tags=["messages"],
    summary="List messages",
    description="List messages with pagination and optional role filtering.",
)
def list_messages(
    limit: int = Query(default=20, ge=1, le=100, description="Maximum messages to return"),
    offset: int = Query(default=0, ge=0, description="Number of messages to skip"),
    role: Literal["user", "assistant"] | None = Query(
        default=None, description="Filter messages by role"
    ),
) -> list[MessageResponse]:
    results = list(messages.values())
    if role is not None:
        results = [message for message in results if message.role == role]
    return results[offset : offset + limit]


@router.get(
    "/messages/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    tags=["messages"],
    summary="Retrieve a message",
    description="Retrieve a single message by its ID.",
)
def retrieve_message(message_id: int) -> MessageResponse:
    return get_message_or_raise(message_id)


@router.patch(
    "/messages/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    tags=["messages"],
    summary="Update a message",
    description="Replace the content of an existing message.",
)
def update_message(message_id: int, payload: MessageUpdate) -> MessageResponse:
    existing = get_message_or_raise(message_id)
    updated = existing.model_copy(update={"content": payload.content})
    messages[message_id] = updated
    return updated


@router.delete(
    "/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["messages"],
    summary="Delete a message",
    description="Delete an existing message. Returns an empty response body.",
)
def delete_message(message_id: int) -> Response:
    get_message_or_raise(message_id)
    del messages[message_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
