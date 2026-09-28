from typing import Any
from backend.app.core.indicators import INDICATORS
from backend.app.services.world_bank import get_indicator_data

SECTOR_INDICATORS = [
    "agriculture_value_added",
    "industry_value_added",
    "manufacturing_value_added",
    "services_value_added",
]

# Transparent, non-causal scenario elasticities used only to translate a policy shock
# into an illustrative sector sensitivity layer. The economic ML targets remain data-trained.
POLICY_SECTOR_SENSITIVITY = {
    "investment": {"agriculture_value_added": 0.35, "industry_value_added": 0.80, "manufacturing_value_added": 1.00, "services_value_added": 0.55},
    "fdi": {"agriculture_value_added": 0.20, "industry_value_added": 0.90, "manufacturing_value_added": 1.10, "services_value_added": 0.70},
    "government_consumption": {"agriculture_value_added": 0.20, "industry_value_added": 0.45, "manufacturing_value_added": 0.35, "services_value_added": 0.80},
    "exports": {"agriculture_value_added": 0.55, "industry_value_added": 0.85, "manufacturing_value_added": 0.95, "services_value_added": 0.65},
    "imports": {"agriculture_value_added": -0.20, "industry_value_added": -0.50, "manufacturing_value_added": -0.60, "services_value_added": -0.25},
    "household_consumption": {"agriculture_value_added": 0.35, "industry_value_added": 0.55, "manufacturing_value_added": 0.50, "services_value_added": 0.80},
}

def _latest(country: str, indicator: str, start_year: int, end_year: int):
    payload = get_indicator_data(country, indicator, start_year, end_year)
    observations = [o for o in payload.get("observations", []) if o.get("value") is not None]
    return observations[-1] if observations else None

def simulate_sector_impacts(country: str, policy_variable: str, change_percent: float, start_year: int, end_year: int) -> dict[str, Any]:
    sensitivities = POLICY_SECTOR_SENSITIVITY.get(policy_variable)
    if not sensitivities:
        raise ValueError(f"Unsupported policy variable: {policy_variable}")
    rows = []
    for indicator in SECTOR_INDICATORS:
        latest = _latest(country, indicator, start_year, end_year)
        if not latest:
            continue
        base = float(latest["value"])
        sensitivity = float(sensitivities[indicator])
        estimated_change = base * (change_percent / 100.0) * sensitivity
        rows.append({
            "indicator": indicator,
            "sector": INDICATORS[indicator]["name"].replace(" Value Added", ""),
            "baseline_share_gdp": round(base, 4),
            "estimated_change_pp": round(estimated_change, 4),
            "scenario_share_gdp": round(base + estimated_change, 4),
            "unit": INDICATORS[indicator]["unit"],
            "year": latest.get("year"),
            "sensitivity": sensitivity,
        })
    return {
        "country_code": country.upper(),
        "policy_variable": policy_variable,
        "change_percent": change_percent,
        "sectors": rows,
        "method": "Historical sector shares plus transparent policy-sensitivity assumptions",
        "note": "Sector impacts are scenario sensitivities, not causal estimates. Sensitivity coefficients are explicit model assumptions and should be calibrated with country-specific sector data before policy use.",
    }
