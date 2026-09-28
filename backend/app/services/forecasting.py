import math
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
)
from statsmodels.tsa.ar_model import AutoReg

from backend.app.services.preprocessing import (
    fetch_country_dataframe,
    clean_economic_dataframe,
)


SUPPORTED_FORECAST_INDICATORS = [
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


class ForecastingError(Exception):
    """Raised when a reliable baseline forecast cannot be produced."""


def calculate_metrics(actual, predicted):

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    mae = mean_absolute_error(actual, predicted)

    rmse = math.sqrt(
        mean_squared_error(actual, predicted)
    )

    nonzero = actual != 0

    if nonzero.any():
        mape = np.mean(
            np.abs(
                (actual[nonzero] - predicted[nonzero])
                / actual[nonzero]
            )
        ) * 100
    else:
        mape = None

    return {
        "mae": round(float(mae), 4),
        "rmse": round(float(rmse), 4),
        "mape_percent": (
            round(float(mape), 4)
            if mape is not None
            else None
        ),
    }


def prepare_series(
    country: str,
    indicator: str,
    start_year: int,
    end_year: int,
):

    if indicator not in SUPPORTED_FORECAST_INDICATORS:
        raise ForecastingError(
            f"Unsupported forecast indicator: {indicator}"
        )

    df = fetch_country_dataframe(
        country=country,
        indicators=[indicator],
        start_year=start_year,
        end_year=end_year,
    )

    df = clean_economic_dataframe(df)

    series_df = df[
        ["year", indicator]
    ].dropna().copy()

    series_df = series_df.sort_values(
        "year"
    ).reset_index(drop=True)

    if len(series_df) < 10:
        raise ForecastingError(
            "At least 10 usable annual observations are "
            "required for baseline forecasting."
        )

    return series_df


def choose_lags(n_observations: int) -> int:
    if n_observations >= 30:
        return 3
    if n_observations >= 20:
        return 2
    return 1


def evaluate_baseline(
    series_df: pd.DataFrame,
    indicator: str,
):

    n = len(series_df)

    test_size = max(
        3,
        min(5, n // 5),
    )

    train_df = series_df.iloc[:-test_size]
    test_df = series_df.iloc[-test_size:]

    train_values = train_df[
        indicator
    ].astype(float).to_numpy()

    test_values = test_df[
        indicator
    ].astype(float).to_numpy()

    lags = choose_lags(len(train_values))

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            model = AutoReg(
                train_values,
                lags=lags,
                trend="ct",
            )

            fitted = model.fit()

            predictions = fitted.predict(
                start=len(train_values),
                end=(
                    len(train_values)
                    + len(test_values)
                    - 1
                ),
                dynamic=False,
            )

    except Exception as exc:
        raise ForecastingError(
            f"Baseline model evaluation failed: {exc}"
        ) from exc

    metrics = calculate_metrics(
        test_values,
        predictions,
    )

    validation = []

    for year, actual, predicted in zip(
        test_df["year"],
        test_values,
        predictions,
    ):
        validation.append({
            "year": int(year),
            "actual": round(float(actual), 6),
            "predicted": round(float(predicted), 6),
        })

    return {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "lags": lags,
        "metrics": metrics,
        "validation": validation,
    }


def forecast_future(
    series_df: pd.DataFrame,
    indicator: str,
    horizon: int = 5,
):

    values = series_df[
        indicator
    ].astype(float).to_numpy()

    lags = choose_lags(len(values))

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            model = AutoReg(
                values,
                lags=lags,
                trend="ct",
            )

            fitted = model.fit()

            future_values = fitted.predict(
                start=len(values),
                end=len(values) + horizon - 1,
                dynamic=False,
            )

    except Exception as exc:
        raise ForecastingError(
            f"Future forecasting failed: {exc}"
        ) from exc

    last_year = int(
        series_df["year"].max()
    )

    forecast = []

    for index, value in enumerate(
        future_values,
        start=1,
    ):
        forecast.append({
            "year": last_year + index,
            "baseline": round(float(value), 6),
        })

    return {
        "lags": lags,
        "forecast": forecast,
    }


def run_baseline_forecast(
    country: str,
    indicator: str,
    start_year: int = 1990,
    end_year: int = 2025,
    horizon: int = 5,
):

    if horizon < 1 or horizon > 10:
        raise ForecastingError(
            "Forecast horizon must be between 1 and 10 years."
        )

    series_df = prepare_series(
        country=country,
        indicator=indicator,
        start_year=start_year,
        end_year=end_year,
    )

    evaluation = evaluate_baseline(
        series_df=series_df,
        indicator=indicator,
    )

    future = forecast_future(
        series_df=series_df,
        indicator=indicator,
        horizon=horizon,
    )

    return {
        "country_code": country.upper(),
        "indicator": indicator,
        "model": "AutoReg",
        "historical_start_year": int(
            series_df["year"].min()
        ),
        "historical_end_year": int(
            series_df["year"].max()
        ),
        "observations": len(series_df),
        "validation_method": (
            "Chronological holdout using the latest observations"
        ),
        "train_rows": evaluation["train_rows"],
        "test_rows": evaluation["test_rows"],
        "lags": future["lags"],
        "metrics": evaluation["metrics"],
        "validation": evaluation["validation"],
        "forecast": future["forecast"],
        "warning": (
            "Baseline forecasts are statistical projections "
            "from historical data and are not guaranteed "
            "economic outcomes."
        ),
    }


