from typing import Literal

from pydantic import BaseModel, Field


PolicyVariable = Literal[
    "investment",
    "fdi",
    "government_consumption",
    "exports",
    "imports",
    "household_consumption",
]


class PolicyQuery(BaseModel):

    country: str = Field(
        description=(
            "ISO-3 country code such as SAU, PAK, ARE, USA."
        )
    )

    policy_variable: PolicyVariable

    change_percent: float = Field(
        gt=-100,
        le=100,
        description=(
            "Relative percentage change in the policy variable."
        ),
    )

    horizon: int = Field(
        default=5,
        ge=1,
        le=10,
    )

    language: Literal[
        "en",
        "ar",
    ] = "en"
