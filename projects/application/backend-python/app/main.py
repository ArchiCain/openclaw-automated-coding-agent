from contextlib import asynccontextmanager
from typing import AsyncGenerator

import socketio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.features.database.engine import close_engine, init_engine
from app.features.mastra_agents.socket_handlers import create_socket_server


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: handles startup and shutdown events."""
    # Startup
    await init_engine()
    yield
    # Shutdown
    await close_engine()


def create_app() -> socketio.ASGIApp:
    """FastAPI + Socket.IO application factory.

    Returns an ``socketio.ASGIApp`` that wraps the FastAPI app so that both
    HTTP requests and Socket.IO WebSocket connections are handled by the same
    process.  Uvicorn should be pointed at the ``socket_app`` exported at
    module level.
    """
    fastapi_app = FastAPI(
        title="Backend Python",
        description="FastAPI backend replicating the NestJS backend API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handlers
    @fastapi_app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"statusCode": 500, "message": "Internal server error"},
        )

    # Feature routers
    from app.features.health.router import router as health_router
    from app.features.auth.router import router as auth_router
    from app.features.theme.router import router as theme_router
    from app.features.user_management.router import router as users_router
    from app.features.mastra_agents.router import router as agents_router

    fastapi_app.include_router(health_router)
    fastapi_app.include_router(auth_router)
    # theme_router registers /users/me/preferences — must come before users_router
    # so FastAPI matches the more specific path first
    fastapi_app.include_router(theme_router)
    fastapi_app.include_router(users_router)
    fastapi_app.include_router(agents_router)

    # Socket.IO setup — wrap FastAPI with socketio.ASGIApp so that both HTTP
    # and WebSocket/Socket.IO traffic are handled by the same uvicorn process.
    sio = create_socket_server(settings.allowed_origins_list)
    combined_app = socketio.ASGIApp(sio, fastapi_app)

    # Attach sio to fastapi_app so it's accessible if needed
    fastapi_app.state.sio = sio

    return combined_app


# ``socket_app`` is the ASGI entry-point for uvicorn.
# ``app`` is kept as an alias for backwards compatibility with any tooling that
# references it directly (e.g. alembic, pytest fixtures).
socket_app = create_app()
# Expose the inner FastAPI app for tooling that needs it
app = socket_app.other_asgi_app  # type: ignore[attr-defined]
