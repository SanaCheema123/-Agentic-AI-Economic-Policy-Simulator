import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from backend.app.services.forecasting import prepare_series, choose_lags


def _supervised(values, lags):
    X, y = [], []
    for i in range(lags, len(values)):
        X.append(values[i-lags:i])
        y.append(values[i])
    return np.asarray(X, dtype=float), np.asarray(y, dtype=float)


def run_xgboost_forecast(country: str, indicator: str, start_year=1990, end_year=2025, horizon=5):
    if not 1 <= horizon <= 10:
        raise ValueError("Forecast horizon must be between 1 and 10 years.")
    df = prepare_series(country, indicator, start_year, end_year)
    values = df[indicator].astype(float).to_numpy()
    lags = choose_lags(len(values))
    X, y = _supervised(values, lags)
    if len(X) < 8:
        raise ValueError("Insufficient observations for XGBoost forecasting.")
    test_size = max(3, min(5, len(X)//5))
    model = XGBRegressor(n_estimators=250, max_depth=2, learning_rate=0.03, subsample=0.9, colsample_bytree=1.0, objective="reg:squarederror", random_state=42)
    model.fit(X[:-test_size], y[:-test_size])
    pred = model.predict(X[-test_size:])
    actual = y[-test_size:]
    mae = float(mean_absolute_error(actual, pred))
    rmse = float(np.sqrt(mean_squared_error(actual, pred)))
    r2 = float(r2_score(actual, pred)) if len(actual) > 1 else None
    model.fit(X, y)
    history = list(values)
    future = []
    last_year = int(df.year.max())
    for step in range(1, horizon + 1):
        row = np.asarray(history[-lags:], dtype=float).reshape(1, -1)
        value = float(model.predict(row)[0])
        history.append(value)
        future.append({"year": last_year + step, "baseline": round(value, 6)})
    validation_years = df.year.iloc[-test_size:].astype(int).tolist()
    validation = [{"year": y_, "actual": round(float(a), 6), "predicted": round(float(p), 6)} for y_, a, p in zip(validation_years, actual, pred)]
    return {"country_code": country.upper(), "indicator": indicator, "model": "XGBoost autoregressive", "horizon_years": horizon, "validation": {"mae": round(mae,4), "rmse": round(rmse,4), "r2": round(r2,4) if r2 is not None else None, "predictions": validation}, "forecast": future, "disclaimer": "Forecasts are model estimates based on historical observations and are not guarantees."}
