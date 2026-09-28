from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import ScenarioRun

from backend.app.core.scenario_config import (
    POLICY_VARIABLES,
    TARGET_VARIABLES,
)
from backend.app.schemas.scenario import ScenarioRequest
from backend.app.schemas.scenario_compare import ScenarioCompareRequest
from backend.app.services.sector_simulator import simulate_sector_impacts
from backend.app.services.scenario_simulator import (
    ScenarioSimulationError,
    run_policy_scenario,
)


router = APIRouter(
    prefix="/api/scenario",
    tags=["Policy Scenario Simulation"],
)


@router.get("/variables")
def scenario_variables():
    """
    Return policy variables and economic target variables
    supported by the simulator.
    """
    return {
        "policy_variables": POLICY_VARIABLES,
        "target_variables": TARGET_VARIABLES,
    }


@router.post("/simulate")
def simulate_policy(request: ScenarioRequest, db: Session = Depends(get_db)):
    """
    Run a model-based economic policy scenario simulation.
    """

    country = request.country.strip().upper()
    policy_variable = request.policy_variable.strip().lower()

    if request.start_year >= request.end_year:
        raise HTTPException(
            status_code=400,
            detail="start_year must be smaller than end_year.",
        )

    if policy_variable not in POLICY_VARIABLES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported policy variable: {policy_variable}. "
                f"Available variables: "
                f"{', '.join(POLICY_VARIABLES.keys())}"
            ),
        )

    try:
        result = run_policy_scenario(
            country=country,
            policy_variable=policy_variable,
            change_percent=request.change_percent,
            start_year=request.start_year,
            end_year=request.end_year,
            horizon=request.horizon,
        )

        record = ScenarioRun(
            country=country, policy_variable=policy_variable,
            change_percent=request.change_percent, horizon=request.horizon,
            result=result,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "status": "success",
            "scenario_id": record.id,
            "request": {
                "country": country,
                "policy_variable": policy_variable,
                "change_percent": request.change_percent,
                "start_year": request.start_year,
                "end_year": request.end_year,
                "horizon": request.horizon,
            },
            "result": result,
        }

    except ScenarioSimulationError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Scenario simulation failed. "
                f"{str(exc)}"
            ),
        ) from exc


@router.post("/compare")
def compare_policy_scenarios(request: ScenarioCompareRequest):
    """Run 2-6 scenarios through the same simulation engine for side-by-side comparison."""
    results = []
    for scenario in request.scenarios:
        try:
            result = run_policy_scenario(
                country=scenario.country,
                policy_variable=scenario.policy_variable,
                change_percent=scenario.change_percent,
                start_year=scenario.start_year,
                end_year=scenario.end_year,
                horizon=scenario.horizon,
            )
            results.append({"request": scenario.model_dump(), "result": result})
        except ScenarioSimulationError as exc:
            results.append({"request": scenario.model_dump(), "error": str(exc)})
    return {"status": "success", "count": len(results), "scenarios": results, "disclaimer": "Scenario comparisons are model-based estimates and not policy recommendations."}

@router.post("/sector-impact")
def sector_policy_impact(request: ScenarioRequest):
    try:
        return {"status": "success", "result": simulate_sector_impacts(request.country, request.policy_variable, request.change_percent, request.start_year, request.end_year)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
