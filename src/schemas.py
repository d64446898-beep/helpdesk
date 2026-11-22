"""Схемы запросов и ответов API (валидация данных)."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

Status = Literal["new", "in_progress", "resolved", "closed"]
Priority = Literal["low", "normal", "high"]


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=100)
    full_name: str = Field(default="", max_length=100)

    @field_validator("username")
    @classmethod
    def lowercase_username(cls, value: str) -> str:
        return value.lower()


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=100)

    @field_validator("username")
    @classmethod
    def lowercase_username(cls, value: str) -> str:
        return value.strip().lower()


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=1, max_length=5000)
    priority: Priority = "normal"

    @field_validator("title", "description")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("пустое значение")
        return value


class TicketUpdate(BaseModel):
    """Частичное обновление: меняются только переданные поля."""

    status: Optional[Status] = None
    priority: Optional[Priority] = None
    assignee_id: Optional[int] = None


class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("пустое значение")
        return value


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    created_at: datetime
    author: UserOut


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    author: UserOut
    assignee: Optional[UserOut] = None
    comments_count: int = 0


class TicketDetail(TicketOut):
    comments: list[CommentOut] = []


class StatsOut(BaseModel):
    total: int
    new: int
    in_progress: int
    resolved: int
    closed: int
