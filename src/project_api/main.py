
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, Response

from project_api import __version__
from project_api.chat import router as chat_router
from project_api.models import (
    MessageCreate,
    MessageResponse,
    MessageUpdate,
)

app = FastAPI(
    title="Project API",
    version=__version__,
    description="A simple in-memory Messages API for learning REST fundamentals.",
)

# Temporary in-memory storage. Messages disappear when the app restarts.
messages: dict[int, MessageResponse] = {}
next_message_id = 1


class MessageNotFoundError(Exception):
    """Raised when a requested message does not exist."""

    def __init__(self, message_id: int) -> None:
        self.message_id = message_id


@app.exception_handler(MessageNotFoundError)
async def message_not_found_handler(
    request: Request,
    exc: MessageNotFoundError,
) -> JSONResponse:
    """Return a consistent custom JSON response for missing messages."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "message_not_found",
                "message": f"Message with ID {exc.message_id} was not found.",
            }
        },
    )


def get_message_or_raise(message_id: int) -> MessageResponse:
    """Find a message or raise the custom not-found exception."""
    message = messages.get(message_id)
    if message is None:
        raise MessageNotFoundError(message_id)
    return message


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Return basic service health information."""
    return {"status": "ok", "version": __version__}


@app.post(
    "/api/v1/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["messages"],
    summary="Create a message",
    description="Create a user or assistant message in temporary memory.",
)
def create_message(payload: MessageCreate) -> MessageResponse:
    """Create a message and assign its ID and creation timestamp."""
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


@app.get(
    "/api/v1/messages",
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
        default=None,
        description="Filter messages by role",
    ),
) -> list[MessageResponse]:
    """Return messages in insertion order with optional filtering."""
    results = list(messages.values())

    if role is not None:
        results = [message for message in results if message.role == role]

    return results[offset : offset + limit]


@app.get(
    "/api/v1/messages/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    tags=["messages"],
    summary="Retrieve a message",
    description="Retrieve a single message by its ID.",
    responses={
        404: {
            "description": "Message not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "message_not_found",
                            "message": "Message with ID 999 was not found."
                        }
                    }
                }
            },
        }
    },
)
def retrieve_message(message_id: int) -> MessageResponse:
    """Return one existing message."""
    return get_message_or_raise(message_id)


@app.patch(
    "/api/v1/messages/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    tags=["messages"],
    summary="Update a message",
    description="Replace the content of an existing message.",
)
def update_message(
    message_id: int,
    payload: MessageUpdate,
) -> MessageResponse:
    """Update message content while preserving its ID, role and timestamp."""
    existing = get_message_or_raise(message_id)

    updated = existing.model_copy(update={"content": payload.content})
    messages[message_id] = updated
    return updated


@app.delete(
    "/api/v1/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    tags=["messages"],
    summary="Delete a message",
    description="Delete an existing message. Returns an empty response body.",
)
def delete_message(message_id: int) -> Response:
    """Delete one message and return no content."""
    get_message_or_raise(message_id)
    del messages[message_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Task 03: one-turn LLM chat endpoint.
app.include_router(chat_router)
