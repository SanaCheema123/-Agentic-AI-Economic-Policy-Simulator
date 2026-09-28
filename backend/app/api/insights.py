from fastapi import APIRouter, HTTPException, Query
from backend.app.core.indicators import INDICATORS
from backend.app.services.world_bank import get_indicator_data, WorldBankAPIError
from backend.app.services.sector_simulator import simulate_sector_impacts
from backend.app.schemas.scenario import ScenarioRequest

router = APIRouter(prefix="/api/insights", tags=["Regional and Sector Insights"])
SECTORS = ["agriculture_value_added", "industry_value_added", "manufacturing_value_added", "services_value_added"]


def _latest(country, indicator, start_year, end_year):
    payload = get_indicator_data(country, indicator, start_year, end_year)
    obs = payload.get("observations", [])
    latest = obs[-1] if obs else None
    return {"country_code": country.upper(), "country": payload.get("country", country), "indicator": indicator, "indicator_name": INDICATORS[indicator]["name"], "unit": INDICATORS[indicator]["unit"], "latest": latest}

@router.get("/regional-comparison")
def regional_comparison(countries: str = Query(..., description="Comma-separated ISO-3 codes, e.g. SAU,ARE,QAT"), indicator: str = "gdp_growth", start_year: int = 2000, end_year: int = 2025):
    codes = [c.strip().upper() for c in countries.split(",") if c.strip()]
    if not 2 <= len(codes) <= 12:
        raise HTTPException(400, "Provide between 2 and 12 country codes.")
    if indicator not in INDICATORS:
        raise HTTPException(400, f"Unknown indicator: {indicator}")
    try:
        return {"indicator": indicator, "comparison": [_latest(c, indicator, start_year, end_year) for c in codes], "source": "World Bank API"}
    except WorldBankAPIError as exc:
        raise HTTPException(502, str(exc)) from exc

@router.get("/sector-comparison/{country}")
def sector_comparison(country: str, start_year: int = 2000, end_year: int = 2025):
    try:
        return {"country_code": country.upper(), "sectors": [_latest(country, s, start_year, end_year) for s in SECTORS], "source": "World Bank sector value-added indicators", "note": "Sector comparison represents sector value added as a share of GDP; it does not claim causal policy impact by sector."}
    except WorldBankAPIError as exc:
        raise HTTPException(502, str(exc)) from exc


@router.post("/sector-policy-impact")
def sector_policy_impact(request: ScenarioRequest):
    try:
        return simulate_sector_impacts(request.country, request.policy_variable, request.change_percent, request.start_year, request.end_year)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
