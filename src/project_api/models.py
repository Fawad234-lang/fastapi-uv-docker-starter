"""Pydantic models retained from Task 02."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageCreate(BaseModel):
    """Fields required to create a message."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value:
            raise ValueError("Content must not be empty or whitespace only.")
        return value


class MessageUpdate(BaseModel):
    """Fields allowed when updating a message."""

    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=2000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value:
            raise ValueError("Content must not be empty or whitespace only.")
        return value


class MessageResponse(BaseModel):
    """Message returned by the API."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


def current_utc_time() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)
