from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler

from backend.app.core.scenario_config import (
    POLICY_VARIABLES,
    TARGET_VARIABLES,
)
from backend.app.services.preprocessing import (
    clean_economic_dataframe,
    fetch_country_dataframe,
)
from backend.app.services.forecasting import (
    run_baseline_forecast,
)


class ScenarioSimulationError(Exception):
    """Raised when a policy scenario cannot be estimated."""


def _safe_r2(actual, predicted):
    if len(actual) < 2:
        return None

    try:
        value = r2_score(actual, predicted)
        if not np.isfinite(value):
            return None
        return round(float(value), 4)
    except Exception:
        return None


def _build_training_frame(
    country: str,
    policy_variable: str,
    target: str,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:

    df = fetch_country_dataframe(
        country=country,
        indicators=[
            policy_variable,
            target,
        ],
        start_year=start_year,
        end_year=end_year,
    )

    df = clean_economic_dataframe(df)

    # Predict next year's target using:
    # current target + current policy variable.
    df[f"{target}_next"] = df[target].shift(-1)

    model_df = df[
        [
            "year",
            target,
            policy_variable,
            f"{target}_next",
        ]
    ].dropna().copy()

    if len(model_df) < 12:
        raise ScenarioSimulationError(
            f"Insufficient usable observations for "
            f"{policy_variable} -> {target}. "
            f"Only {len(model_df)} observations are available."
        )

    return model_df


def _fit_policy_model(
    model_df: pd.DataFrame,
    policy_variable: str,
    target: str,
) -> dict[str, Any]:

    feature_columns = [
        target,
        policy_variable,
    ]

    X = model_df[feature_columns].astype(float)
    y = model_df[f"{target}_next"].astype(float)

    # Chronological holdout: latest observations remain unseen.
    test_size = max(
        3,
        min(5, len(model_df) // 5),
    )

    train_X = X.iloc[:-test_size]
    test_X = X.iloc[-test_size:]

    train_y = y.iloc[:-test_size]
    test_y = y.iloc[-test_size:]

    scaler = StandardScaler()

    train_X_scaled = scaler.fit_transform(train_X)
    test_X_scaled = scaler.transform(test_X)

    validation_model = Ridge(alpha=1.0)
    validation_model.fit(
        train_X_scaled,
        train_y,
    )

    validation_predictions = validation_model.predict(
        test_X_scaled
    )

    mae = mean_absolute_error(
        test_y,
        validation_predictions,
    )

    validation_r2 = _safe_r2(
        test_y.to_numpy(),
        validation_predictions,
    )

    # Refit using all historical observations after validation.
    full_scaler = StandardScaler()
    X_scaled = full_scaler.fit_transform(X)

    final_model = Ridge(alpha=1.0)
    final_model.fit(
        X_scaled,
        y,
    )

    validation = []

    for year, actual, predicted in zip(
        model_df.iloc[-test_size:]["year"],
        test_y,
        validation_predictions,
    ):
        validation.append({
            "year": int(year) + 1,
            "actual": round(float(actual), 6),
            "predicted": round(float(predicted), 6),
        })

    return {
        "model": final_model,
        "scaler": full_scaler,
        "feature_columns": feature_columns,
        "mae": round(float(mae), 4),
        "r2": validation_r2,
        "validation": validation,
        "observations": len(model_df),
    }


def _forecast_policy_baseline(
    country: str,
    policy_variable: str,
    start_year: int,
    end_year: int,
    horizon: int,
) -> list[dict]:

    result = run_baseline_forecast(
        country=country,
        indicator=policy_variable,
        start_year=start_year,
        end_year=end_year,
        horizon=horizon,
    )

    return result["forecast"]


def _latest_target_value(
    country: str,
    target: str,
    start_year: int,
    end_year: int,
) -> tuple[int, float]:

    df = fetch_country_dataframe(
        country=country,
        indicators=[target],
        start_year=start_year,
        end_year=end_year,
    )

    df = clean_economic_dataframe(df)

    available = df[
        ["year", target]
    ].dropna()

    if available.empty:
        raise ScenarioSimulationError(
            f"No usable observations found for {target}."
        )

    latest = available.iloc[-1]

    return (
        int(latest["year"]),
        float(latest[target]),
    )


def _predict_next(
    fitted: dict,
    target_value: float,
    policy_value: float,
) -> float:

    input_df = pd.DataFrame(
        [[target_value, policy_value]],
        columns=fitted["feature_columns"],
    )

    scaled = fitted["scaler"].transform(
        input_df
    )

    prediction = fitted["model"].predict(
        scaled
    )[0]

    return float(prediction)


def simulate_target(
    country: str,
    policy_variable: str,
    target: str,
    change_percent: float,
    start_year: int,
    end_year: int,
    horizon: int,
) -> dict:

    model_df = _build_training_frame(
        country=country,
        policy_variable=policy_variable,
        target=target,
        start_year=start_year,
        end_year=end_year,
    )

    fitted = _fit_policy_model(
        model_df=model_df,
        policy_variable=policy_variable,
        target=target,
    )

    policy_forecast = _forecast_policy_baseline(
        country=country,
        policy_variable=policy_variable,
        start_year=start_year,
        end_year=end_year,
        horizon=horizon,
    )

    latest_year, latest_target = _latest_target_value(
        country=country,
        target=target,
        start_year=start_year,
        end_year=end_year,
    )

    baseline_target = latest_target
    scenario_target = latest_target

    results = []

    for step, policy_row in enumerate(
        policy_forecast,
        start=1,
    ):
        baseline_policy = float(
            policy_row["baseline"]
        )

        scenario_policy = (
            baseline_policy
            * (1.0 + change_percent / 100.0)
        )

        baseline_target = _predict_next(
            fitted=fitted,
            target_value=baseline_target,
            policy_value=baseline_policy,
        )

        scenario_target = _predict_next(
            fitted=fitted,
            target_value=scenario_target,
            policy_value=scenario_policy,
        )

        impact = (
            scenario_target - baseline_target
        )

        results.append({
            "year": latest_year + step,
            "baseline_policy_value": round(
                baseline_policy,
                6,
            ),
            "scenario_policy_value": round(
                scenario_policy,
                6,
            ),
            "baseline_target": round(
                baseline_target,
                6,
            ),
            "scenario_target": round(
                scenario_target,
                6,
            ),
            "estimated_impact": round(
                impact,
                6,
            ),
        })

    return {
        "target": target,
        "target_name": TARGET_VARIABLES[target]["name"],
        "unit": TARGET_VARIABLES[target]["unit"],
        "model": "Ridge autoregressive scenario model",
        "observations": fitted["observations"],
        "validation": {
            "mae": fitted["mae"],
            "r2": fitted["r2"],
            "predictions": fitted["validation"],
        },
        "results": results,
    }


def run_policy_scenario(
    country: str,
    policy_variable: str,
    change_percent: float,
    start_year: int = 1990,
    end_year: int = 2025,
    horizon: int = 5,
) -> dict:

    country = country.strip().upper()
    policy_variable = policy_variable.strip().lower()

    if policy_variable not in POLICY_VARIABLES:
        raise ScenarioSimulationError(
            f"Unsupported policy variable: {policy_variable}. "
            f"Available variables: "
            f"{', '.join(POLICY_VARIABLES.keys())}"
        )

    if change_percent <= -100:
        raise ScenarioSimulationError(
            "change_percent must be greater than -100."
        )

    if abs(change_percent) > 100:
        raise ScenarioSimulationError(
            "For the initial simulator, policy changes "
            "are limited to -100% to +100%."
        )

    if horizon < 1 or horizon > 10:
        raise ScenarioSimulationError(
            "Forecast horizon must be between 1 and 10 years."
        )

    target_results = {}
    skipped_targets = {}

    for target in TARGET_VARIABLES:
        try:
            target_results[target] = simulate_target(
                country=country,
                policy_variable=policy_variable,
                target=target,
                change_percent=change_percent,
                start_year=start_year,
                end_year=end_year,
                horizon=horizon,
            )
        except Exception as exc:
            skipped_targets[target] = str(exc)

    if not target_results:
        raise ScenarioSimulationError(
            "No target could be simulated with the available data."
        )

    return {
        "country_code": country,
        "policy_variable": policy_variable,
        "policy_name": POLICY_VARIABLES[
            policy_variable
        ]["name"],
        "change_percent": change_percent,
        "horizon_years": horizon,
        "method": (
            "Historical time-aware Ridge autoregressive "
            "scenario modelling"
        ),
        "interpretation": (
            "The scenario changes the projected policy variable "
            "relative to its baseline and estimates how target "
            "trajectories differ under historical relationships."
        ),
        "targets": target_results,
        "skipped_targets": skipped_targets,
        "disclaimer": (
            "These are model-based scenario estimates, not causal "
            "guarantees or policy recommendations. Results depend "
            "on historical data, model specification, and the "
            "assumption that estimated relationships remain relevant."
        ),
    }
