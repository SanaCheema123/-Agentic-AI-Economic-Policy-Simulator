from fastapi import APIRouter, HTTPException, Query

from backend.app.services.preprocessing import (
    prepare_modelling_dataframe,
)


router = APIRouter(
    prefix="/api/preprocessing",
    tags=["Data Preprocessing"],
)


def dataframe_records(df):
    safe_df = df.copy()
    safe_df = safe_df.astype(object).where(
        safe_df.notna(),
        None,
    )
    return safe_df.to_dict(orient="records")


@router.get("/{country}")
def preprocess_country(
    country: str,
    start_year: int = Query(2000, ge=1960, le=2100),
    end_year: int = Query(2025, ge=1960, le=2100),
):
    if start_year > end_year:
        raise HTTPException(
            status_code=400,
            detail="start_year cannot be greater than end_year.",
        )

    try:
        result = prepare_modelling_dataframe(
            country=country,
            start_year=start_year,
            end_year=end_year,
        )

        return {
            "country_code": country.upper(),
            "start_year": start_year,
            "end_year": end_year,
            "rows": len(result["modelling"]),
            "missing_before": dataframe_records(
                result["missing_before"].reset_index(
                    names="variable"
                )
            ),
            "missing_after": dataframe_records(
                result["missing_after"].reset_index(
                    names="variable"
                )
            ),
            "data": dataframe_records(
                result["modelling"]
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc
