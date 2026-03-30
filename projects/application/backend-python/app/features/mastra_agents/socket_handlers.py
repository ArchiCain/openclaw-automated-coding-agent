"""Socket.IO event handlers for mastra-chat and mastra-chat-history namespaces.

Event contract matches the NestJS gateway exactly:

/mastra-chat namespace:
  Client emits: 'send-message'  { message: str }
  Server emits: 'response-chunk' { text: str, chunkIndex: int }  (streaming)
  Server emits: 'response-complete'                               (done)
  Server emits: 'chat-error'    { error: str, details?: str }     (on error)
  Server emits: 'conversation-history' { messages: [...] }        (on connect)

/mastra-chat-history namespace:
  Client emits: 'delete-conversation' { threadId: str }
  Server emits: 'chat-history'  { conversations: [...], type: 'initial'|'update' }
"""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from typing import Any

import socketio

from app.features.auth.keycloak_client import decode_user_profile
from app.features.mastra_agents import agent_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared AsyncServer — created once, referenced by both namespaces
# ---------------------------------------------------------------------------

def create_socket_server(cors_origins: list[str]) -> socketio.AsyncServer:
    """Create and configure the python-socketio AsyncServer with both namespaces."""
    sio = socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins=cors_origins,
        logger=False,
        engineio_logger=False,
    )

    # -------------------------------------------------------------------
    # /mastra-chat namespace
    # -------------------------------------------------------------------
    chat_ns = "/mastra-chat"

    # sid -> { userId, threadId }
    chat_connections: dict[str, dict[str, str]] = {}

    @sio.event(namespace=chat_ns)
    async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:  # type: ignore[misc]
        """Validate auth on connection; load conversation history."""
        # Extract userId and threadId from auth or query string
        query_params = _parse_query(environ.get("QUERY_STRING", ""))
        auth_data: dict = auth or {}

        user_id: str = auth_data.get("userId") or query_params.get("userId", "")
        thread_id: str = auth_data.get("threadId") or query_params.get("threadId", "")

        # Validate JWT from auth cookie header
        access_token = _extract_cookie(environ, "access_token")
        if access_token:
            try:
                profile = decode_user_profile(access_token)
                user_id = user_id or profile.id
            except ValueError:
                logger.warning("Invalid JWT on Socket.IO connect for sid %s", sid)
                raise socketio.exceptions.ConnectionRefusedError("Unauthorized")
        else:
            # Allow connection without JWT only if userId is provided (dev/testing)
            if not user_id:
                raise socketio.exceptions.ConnectionRefusedError("Unauthorized")

        if not user_id or not thread_id:
            logger.warning("Client %s connected without userId or threadId", sid)
            raise socketio.exceptions.ConnectionRefusedError("userId and threadId required")

        chat_connections[sid] = {"userId": user_id, "threadId": thread_id}
        logger.info("mastra-chat client %s connected (user=%s, thread=%s)", sid, user_id, thread_id)

        # Send conversation history on connect
        await _emit_conversation_history(sio, sid, thread_id, chat_ns)

    @sio.event(namespace=chat_ns)
    async def disconnect(sid: str) -> None:  # type: ignore[misc]
        conn = chat_connections.pop(sid, {})
        logger.info("mastra-chat client %s disconnected (user=%s)", sid, conn.get("userId"))

    @sio.on("send-message", namespace=chat_ns)
    async def handle_send_message(sid: str, data: dict) -> dict:  # type: ignore[misc]
        """Stream AI response back to the client token by token."""
        conn = chat_connections.get(sid)
        if not conn:
            await sio.emit("chat-error", {"error": "Connection data not found"}, to=sid, namespace=chat_ns)
            return {"success": False, "error": "Connection data not found"}

        message: str = data.get("message", "") if isinstance(data, dict) else ""
        if not message:
            await sio.emit("chat-error", {"error": "message is required"}, to=sid, namespace=chat_ns)
            return {"success": False, "error": "message is required"}

        # Determine agent from data (default to gpt-agent to match NestJS which uses GPT-4.1)
        agent_id: str = data.get("agentId", "gpt-agent") if isinstance(data, dict) else "gpt-agent"
        thread_id = conn["threadId"]

        logger.info("Streaming chat for user %s, thread %s", conn["userId"], thread_id)

        # Stream in background — acknowledge immediately
        import asyncio
        asyncio.ensure_future(_do_stream(sio, sid, agent_id, message, thread_id, chat_ns))

        return {"success": True}

    # -------------------------------------------------------------------
    # /mastra-chat-history namespace
    # -------------------------------------------------------------------
    history_ns = "/mastra-chat-history"

    # sid -> { userId }
    history_connections: dict[str, dict[str, str]] = {}
    # userId -> set of sids
    user_clients: dict[str, set[str]] = defaultdict(set)

    @sio.event(namespace=history_ns)
    async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:  # type: ignore[misc]
        query_params = _parse_query(environ.get("QUERY_STRING", ""))
        auth_data: dict = auth or {}

        user_id: str = auth_data.get("userId") or query_params.get("userId", "")

        access_token = _extract_cookie(environ, "access_token")
        if access_token:
            try:
                profile = decode_user_profile(access_token)
                user_id = user_id or profile.id
            except ValueError:
                raise socketio.exceptions.ConnectionRefusedError("Unauthorized")
        else:
            if not user_id:
                raise socketio.exceptions.ConnectionRefusedError("Unauthorized")

        if not user_id:
            raise socketio.exceptions.ConnectionRefusedError("userId required")

        history_connections[sid] = {"userId": user_id}
        user_clients[user_id].add(sid)
        logger.info("mastra-chat-history client %s connected (user=%s)", sid, user_id)

        # Send initial conversation list
        await _emit_chat_history(sio, sid, user_id, "initial", history_ns)

    @sio.event(namespace=history_ns)
    async def disconnect(sid: str) -> None:  # type: ignore[misc]
        conn = history_connections.pop(sid, {})
        user_id = conn.get("userId", "")
        if user_id and sid in user_clients.get(user_id, set()):
            user_clients[user_id].discard(sid)
            if not user_clients[user_id]:
                del user_clients[user_id]
        logger.info("mastra-chat-history client %s disconnected (user=%s)", sid, user_id)

    @sio.on("delete-conversation", namespace=history_ns)
    async def handle_delete_conversation(sid: str, data: dict) -> None:  # type: ignore[misc]
        conn = history_connections.get(sid)
        if not conn:
            await sio.emit("chat-error", {"error": "Connection data not found"}, to=sid, namespace=history_ns)
            return

        thread_id: str = data.get("threadId", "") if isinstance(data, dict) else ""
        if not thread_id:
            await sio.emit("chat-error", {"error": "threadId is required"}, to=sid, namespace=history_ns)
            return

        user_id = conn["userId"]
        logger.info("Deleting conversation %s for user %s", thread_id, user_id)

        # Remove from in-memory store
        agent_service._conversations.pop(thread_id, None)

        # Refresh history for all this user's clients
        for client_sid in list(user_clients.get(user_id, set())):
            await _emit_chat_history(sio, client_sid, user_id, "update", history_ns)

    return sio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _do_stream(
    sio: socketio.AsyncServer,
    sid: str,
    agent_id: str,
    message: str,
    thread_id: str,
    namespace: str,
) -> None:
    """Background coroutine: streams tokens to the client."""
    try:
        chunk_index = 0
        async for token in agent_service.stream_agent(agent_id, message, thread_id):
            await sio.emit(
                "response-chunk",
                {"text": token, "chunkIndex": chunk_index},
                to=sid,
                namespace=namespace,
            )
            chunk_index += 1

        await sio.emit("response-complete", {}, to=sid, namespace=namespace)
        logger.info("Streaming complete for client %s", sid)
    except Exception as exc:  # noqa: BLE001
        logger.error("Chat stream error for client %s: %s", sid, exc)
        await sio.emit(
            "chat-error",
            {"error": "Failed to process chat stream", "details": str(exc)},
            to=sid,
            namespace=namespace,
        )


async def _emit_conversation_history(
    sio: socketio.AsyncServer,
    sid: str,
    thread_id: str,
    namespace: str,
) -> None:
    """Emit stored messages for a thread to a client."""
    messages = await agent_service.get_conversation_history(thread_id)
    payload = [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat(),
        }
        for m in messages
    ]
    await sio.emit("conversation-history", {"messages": payload}, to=sid, namespace=namespace)


async def _emit_chat_history(
    sio: socketio.AsyncServer,
    sid: str,
    user_id: str,
    history_type: str,
    namespace: str,
) -> None:
    """Emit conversation list for a user to a client."""
    # Build a list of thread ids this user has conversations in
    # For in-memory store we list all thread_ids (no per-user scoping in demo store)
    # Real impl would scope by user; here we return all known threads
    conversations: list[dict] = []
    for thread_id, entries in agent_service._conversations.items():
        if entries:
            last_ts = max(e.timestamp for e in entries)
            conversations.append(
                {
                    "threadId": thread_id,
                    "title": _derive_title(entries),
                    "updatedAt": last_ts.isoformat(),
                }
            )
    # Sort by updatedAt descending
    conversations.sort(key=lambda c: c["updatedAt"], reverse=True)

    await sio.emit(
        "chat-history",
        {"conversations": conversations, "type": history_type},
        to=sid,
        namespace=namespace,
    )


def _derive_title(entries: list) -> str:
    """Generate a conversation title from the first user message."""
    for entry in entries:
        if entry.role == "user" and entry.content:
            title = entry.content[:60]
            return title + "..." if len(entry.content) > 60 else title
    return "Untitled Conversation"


def _parse_query(query_string: str) -> dict[str, str]:
    """Parse a URL query string into a dict."""
    from urllib.parse import parse_qs
    parsed = parse_qs(query_string)
    return {k: v[0] for k, v in parsed.items() if v}


def _extract_cookie(environ: dict, name: str) -> str | None:
    """Extract a cookie value from the WSGI environ."""
    http_cookie = environ.get("HTTP_COOKIE", "")
    for part in http_cookie.split(";"):
        part = part.strip()
        if part.startswith(f"{name}="):
            return part[len(f"{name}="):]
    return None
