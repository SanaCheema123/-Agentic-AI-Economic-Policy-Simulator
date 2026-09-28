from fastapi import APIRouter, HTTPException, Query

from backend.app.services.ml_forecasting import run_xgboost_forecast

from backend.app.services.forecasting import (
    ForecastingError,
    SUPPORTED_FORECAST_INDICATORS,
    run_baseline_forecast,
)


router = APIRouter(
    prefix="/api/forecast",
    tags=["Economic Forecasting"],
)


@router.get("/indicators")
def forecast_indicators():
    return {
        "count": len(SUPPORTED_FORECAST_INDICATORS),
        "indicators": SUPPORTED_FORECAST_INDICATORS,
    }


@router.get("/{country}/{indicator}")
def baseline_forecast(
    country: str,
    indicator: str,
    start_year: int = Query(
        1990,
        ge=1960,
        le=2100,
    ),
    end_year: int = Query(
        2025,
        ge=1960,
        le=2100,
    ),
    horizon: int = Query(
        5,
        ge=1,
        le=10,
    ),
    model: str = Query("autoreg", pattern="^(autoreg|xgboost)$"),
):

    if start_year >= end_year:
        raise HTTPException(
            status_code=400,
            detail=(
                "start_year must be smaller "
                "than end_year."
            ),
        )

    try:
        if model == "xgboost":
            return run_xgboost_forecast(
                country=country, indicator=indicator, start_year=start_year,
                end_year=end_year, horizon=horizon,
            )

        return run_baseline_forecast(
            country=country,
            indicator=indicator,
            start_year=start_year,
            end_year=end_year,
            horizon=horizon,
        )

    except ForecastingError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
