from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import ScenarioRun

router = APIRouter(prefix="/api/scenarios", tags=["Scenario History"])

@router.get("")
def list_scenarios(limit: int = Query(25, ge=1, le=100), country: str | None = None, db: Session = Depends(get_db)):
    q = db.query(ScenarioRun)
    if country:
        q = q.filter(ScenarioRun.country == country.upper())
    rows = q.order_by(ScenarioRun.created_at.desc()).limit(limit).all()
    return {"count": len(rows), "scenarios": [{"id": r.id, "country": r.country, "policy_variable": r.policy_variable, "change_percent": r.change_percent, "horizon": r.horizon, "created_at": r.created_at} for r in rows]}

@router.get("/{scenario_id}")
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    r = db.get(ScenarioRun, scenario_id)
    if not r:
        raise HTTPException(404, "Scenario not found")
    return {"id": r.id, "country": r.country, "policy_variable": r.policy_variable, "change_percent": r.change_percent, "horizon": r.horizon, "result": r.result, "created_at": r.created_at}
