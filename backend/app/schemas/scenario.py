from pydantic import BaseModel, Field


class ScenarioRequest(BaseModel):
    country: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="ISO-3 country code, e.g. SAU, PAK, ARE.",
    )

    policy_variable: str = Field(
        ...,
        description=(
            "Policy variable such as investment, fdi, "
            "government_consumption, exports, imports, "
            "or household_consumption."
        ),
    )

    change_percent: float = Field(
        ...,
        gt=-100,
        le=100,
        description="Relative percentage change from baseline.",
    )

    start_year: int = Field(
        default=1990,
        ge=1960,
        le=2100,
    )

    end_year: int = Field(
        default=2025,
        ge=1960,
        le=2100,
    )

    horizon: int = Field(
        default=5,
        ge=1,
        le=10,
    )
