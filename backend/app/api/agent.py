from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from backend.app.agents.economic_agent import (
    run_agent,
)


router = APIRouter(
    prefix="/api/agent",
    tags=["Agentic AI"],
)


class AgentRequest(BaseModel):
    query: str = Field(
        min_length=5,
        max_length=1000,
    )


@router.post("/query")
def agent_query(
    request: AgentRequest,
):

    try:
        result = run_agent(
            request.query
        )

        return {
            "query": request.query,
            "parsed_query": result.get(
                "parsed_query"
            ),
            "simulation": result.get(
                "simulation_result"
            ),
            "summary": result.get(
                "summary"
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
