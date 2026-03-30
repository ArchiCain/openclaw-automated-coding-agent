"""Pydantic models for the mastra_agents feature."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """A single chat message."""

    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Request body for agent run endpoint."""

    prompt: str
    conversation_id: str | None = None


class AgentInfo(BaseModel):
    """Metadata about an available AI agent."""

    id: str
    name: str
    description: str
    model: str
    provider: str


class ChatHistoryEntry(BaseModel):
    """A stored conversation history entry."""

    id: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
