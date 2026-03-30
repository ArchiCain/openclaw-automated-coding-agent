"""Tests for GET /health."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(app_client: AsyncClient) -> None:
    """Health endpoint must return HTTP 200."""
    response = await app_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_returns_ok_status(app_client: AsyncClient) -> None:
    """Health response body must contain ``status: ok``."""
    response = await app_client.get("/health")
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_returns_service_name(app_client: AsyncClient) -> None:
    """Health response should include the service name."""
    response = await app_client.get("/health")
    data = response.json()
    assert data["service"] == "backend-python"


@pytest.mark.asyncio
async def test_health_returns_timestamp(app_client: AsyncClient) -> None:
    """Health response must include an ISO-8601 timestamp."""
    response = await app_client.get("/health")
    data = response.json()
    assert "timestamp" in data
    assert isinstance(data["timestamp"], str)
    assert len(data["timestamp"]) > 0


@pytest.mark.asyncio
async def test_health_is_public(app_client: AsyncClient) -> None:
    """Health endpoint must be accessible without authentication cookies."""
    response = await app_client.get("/health")
    # Must not return 401 / 403
    assert response.status_code not in (401, 403)
