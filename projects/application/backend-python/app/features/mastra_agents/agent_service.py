"""AI agent service using Anthropic and OpenAI SDKs directly."""
from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator
from datetime import datetime

import anthropic
import openai

from app.config import settings
from app.features.mastra_agents.models import AgentInfo, ChatHistoryEntry, ChatMessage

logger = logging.getLogger(__name__)

# Available agents definition
AGENTS: list[AgentInfo] = [
    AgentInfo(
        id="claude-agent",
        name="Claude Sonnet",
        description="Helpful conversational AI powered by Anthropic Claude.",
        model="claude-sonnet-4-5",
        provider="anthropic",
    ),
    AgentInfo(
        id="gpt-agent",
        name="GPT-4o",
        description="Helpful conversational AI powered by OpenAI GPT-4o.",
        model="gpt-4o",
        provider="openai",
    ),
]

# In-memory conversation store: { conversation_id: [ChatHistoryEntry] }
_conversations: dict[str, list[ChatHistoryEntry]] = defaultdict(list)
_conversations_lock = asyncio.Lock()


def get_agents() -> list[AgentInfo]:
    """Return all available agents."""
    return AGENTS


def get_agent(agent_id: str) -> AgentInfo | None:
    """Look up an agent by id."""
    return next((a for a in AGENTS if a.id == agent_id), None)


async def run_agent(agent_id: str, prompt: str, conversation_id: str | None = None) -> str:
    """Execute an agent with a prompt and return the full response."""
    agent = get_agent(agent_id)
    if agent is None:
        raise ValueError(f"Agent '{agent_id}' not found")

    conv_id = conversation_id or str(uuid.uuid4())
    full_response = ""

    async for token in _stream_agent(agent, prompt, conv_id):
        full_response += token

    return full_response


async def stream_agent(
    agent_id: str,
    prompt: str,
    conversation_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """Stream tokens from an agent for the given prompt."""
    agent = get_agent(agent_id)
    if agent is None:
        raise ValueError(f"Agent '{agent_id}' not found")

    conv_id = conversation_id or str(uuid.uuid4())
    full_response = ""

    async for token in _stream_agent(agent, prompt, conv_id):
        full_response += token
        yield token

    # Persist after streaming complete
    async with _conversations_lock:
        _conversations[conv_id].append(
            ChatHistoryEntry(
                id=str(uuid.uuid4()),
                role="user",
                content=prompt,
                timestamp=datetime.utcnow(),
            )
        )
        _conversations[conv_id].append(
            ChatHistoryEntry(
                id=str(uuid.uuid4()),
                role="assistant",
                content=full_response,
                timestamp=datetime.utcnow(),
            )
        )


async def _stream_agent(agent: AgentInfo, prompt: str, conv_id: str) -> AsyncGenerator[str, None]:
    """Internal: yield text tokens from the appropriate provider."""
    # Build message history for context
    async with _conversations_lock:
        history = list(_conversations[conv_id])

    messages: list[dict] = []
    for entry in history:
        messages.append({"role": entry.role, "content": entry.content})
    messages.append({"role": "user", "content": prompt})

    if agent.provider == "anthropic":
        async for token in _stream_anthropic(agent.model, messages):
            yield token
    elif agent.provider == "openai":
        async for token in _stream_openai(agent.model, messages):
            yield token
    else:
        raise ValueError(f"Unsupported provider: {agent.provider}")


async def _stream_anthropic(model: str, messages: list[dict]) -> AsyncGenerator[str, None]:
    """Stream tokens from Anthropic."""
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    system_prompt = "You are a helpful conversational AI."

    async with client.messages.stream(
        model=model,
        max_tokens=4096,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def _stream_openai(model: str, messages: list[dict]) -> AsyncGenerator[str, None]:
    """Stream tokens from OpenAI."""
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    all_messages = [{"role": "system", "content": "You are a helpful conversational AI."}, *messages]

    stream = await client.chat.completions.create(
        model=model,
        messages=all_messages,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


async def get_conversation_history(conversation_id: str) -> list[ChatHistoryEntry]:
    """Retrieve stored history for a conversation."""
    async with _conversations_lock:
        return list(_conversations.get(conversation_id, []))
