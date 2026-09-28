from fastapi import APIRouter, HTTPException, Query

from backend.app.core.indicators import INDICATORS
from backend.app.services.world_bank import (
    WorldBankAPIError,
    get_indicator_data,
)


router = APIRouter(
    prefix="/api/economy",
    tags=["Economic Data"]
)


@router.get("/indicators")
def list_indicators():
    return {
        "count": len(INDICATORS),
        "indicators": INDICATORS
    }


@router.get("/{country}/{indicator}")
def economic_indicator(
    country: str,
    indicator: str,
    start_year: int = Query(2000, ge=1960, le=2100),
    end_year: int = Query(2025, ge=1960, le=2100)
):
    if start_year > end_year:
        raise HTTPException(
            status_code=400,
            detail="start_year cannot be greater than end_year."
        )

    try:
        return get_indicator_data(
            country=country,
            indicator=indicator,
            start_year=start_year,
            end_year=end_year
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except WorldBankAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        ) from exc
