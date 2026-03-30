"""REST endpoints for the mastra_agents feature."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.features.auth.dependencies import get_current_user
from app.features.auth.models import UserProfile
from app.features.mastra_agents import agent_service
from app.features.mastra_agents.models import AgentInfo, ChatRequest

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentInfo])
async def list_agents(
    _current_user: UserProfile = Depends(get_current_user),
) -> list[AgentInfo]:
    """Return all available AI agents."""
    return agent_service.get_agents()


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    body: ChatRequest,
    _current_user: UserProfile = Depends(get_current_user),
) -> dict:
    """Execute an agent with a prompt and return the full response."""
    agent = agent_service.get_agent(agent_id)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found",
        )

    try:
        response = await agent_service.run_agent(
            agent_id=agent_id,
            prompt=body.prompt,
            conversation_id=body.conversation_id,
        )
        return {"response": response, "agentId": agent_id}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution failed: {exc}",
        ) from exc
