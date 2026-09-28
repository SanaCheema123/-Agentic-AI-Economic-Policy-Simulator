from typing import Iterable

import numpy as np
import pandas as pd

from backend.app.core.indicators import INDICATORS
from backend.app.services.world_bank import get_indicator_data


DEFAULT_INDICATORS = [
    "gdp_growth",
    "inflation",
    "unemployment",
    "investment",
    "fdi",
    "government_consumption",
    "household_consumption",
    "exports",
    "imports",
]


def fetch_country_dataframe(
    country: str,
    indicators: Iterable[str] | None = None,
    start_year: int = 2000,
    end_year: int = 2025,
) -> pd.DataFrame:

    selected = list(indicators or DEFAULT_INDICATORS)

    invalid = [
        indicator
        for indicator in selected
        if indicator not in INDICATORS
    ]

    if invalid:
        raise ValueError(
            f"Unknown indicators: {', '.join(invalid)}"
        )

    merged_df = None

    for indicator in selected:
        result = get_indicator_data(
            country=country,
            indicator=indicator,
            start_year=start_year,
            end_year=end_year,
        )

        observations = result["observations"]

        indicator_df = pd.DataFrame(
            observations,
            columns=["year", "value"],
        )

        if indicator_df.empty:
            indicator_df = pd.DataFrame({
                "year": range(start_year, end_year + 1),
                indicator: np.nan,
            })
        else:
            indicator_df = indicator_df.rename(
                columns={"value": indicator}
            )

        if merged_df is None:
            merged_df = indicator_df
        else:
            merged_df = pd.merge(
                merged_df,
                indicator_df,
                on="year",
                how="outer",
            )

    if merged_df is None:
        return pd.DataFrame()

    all_years = pd.DataFrame({
        "year": range(start_year, end_year + 1)
    })

    merged_df = pd.merge(
        all_years,
        merged_df,
        on="year",
        how="left",
    )

    merged_df = merged_df.sort_values("year").reset_index(drop=True)

    numeric_columns = [
        column
        for column in merged_df.columns
        if column != "year"
    ]

    for column in numeric_columns:
        merged_df[column] = pd.to_numeric(
            merged_df[column],
            errors="coerce",
        )

    return merged_df


def missing_value_report(df: pd.DataFrame) -> pd.DataFrame:

    total_rows = len(df)

    report = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "available_count": df.notna().sum(),
    })

    if total_rows:
        report["missing_percent"] = (
            report["missing_count"] / total_rows * 100
        ).round(2)
    else:
        report["missing_percent"] = 0.0

    return report


def clean_economic_dataframe(
    df: pd.DataFrame,
    interpolation_limit: int = 2,
) -> pd.DataFrame:

    cleaned = df.copy()

    value_columns = [
        column
        for column in cleaned.columns
        if column != "year"
    ]

    for column in value_columns:
        cleaned[column] = cleaned[column].interpolate(
            method="linear",
            limit=interpolation_limit,
            limit_area="inside",
        )

    return cleaned


def add_features(df: pd.DataFrame) -> pd.DataFrame:

    featured = df.copy()

    source_columns = [
        "gdp_growth",
        "inflation",
        "unemployment",
        "investment",
        "fdi",
    ]

    for column in source_columns:
        if column not in featured.columns:
            continue

        featured[f"{column}_lag1"] = featured[column].shift(1)

        featured[f"{column}_change"] = (
            featured[column] -
            featured[column].shift(1)
        )

    return featured


def prepare_modelling_dataframe(
    country: str,
    start_year: int = 2000,
    end_year: int = 2025,
) -> dict:

    raw_df = fetch_country_dataframe(
        country=country,
        start_year=start_year,
        end_year=end_year,
    )

    missing_before = missing_value_report(raw_df)

    cleaned_df = clean_economic_dataframe(raw_df)

    missing_after = missing_value_report(cleaned_df)

    modelling_df = add_features(cleaned_df)

    return {
        "raw": raw_df,
        "cleaned": cleaned_df,
        "modelling": modelling_df,
        "missing_before": missing_before,
        "missing_after": missing_after,
    }
