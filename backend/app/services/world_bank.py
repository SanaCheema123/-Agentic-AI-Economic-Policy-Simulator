from typing import Any

import requests

from backend.app.core.indicators import INDICATORS


BASE_URL = "https://api.worldbank.org/v2"


class WorldBankAPIError(Exception):
    """Raised when World Bank data cannot be retrieved or parsed."""


def get_indicator_data(
    country: str,
    indicator: str,
    start_year: int = 2000,
    end_year: int = 2025
) -> dict[str, Any]:

    country = country.strip().upper()
    indicator_key = indicator.strip().lower()

    if indicator_key not in INDICATORS:
        raise ValueError(
            f"Unknown indicator '{indicator}'. "
            f"Available indicators: {', '.join(INDICATORS.keys())}"
        )

    indicator_info = INDICATORS[indicator_key]
    indicator_code = indicator_info["code"]

    url = (
        f"{BASE_URL}/country/{country}"
        f"/indicator/{indicator_code}"
    )

    params = {
        "format": "json",
        "date": f"{start_year}:{end_year}",
        "per_page": 1000
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        payload = response.json()

    except requests.RequestException as exc:
        raise WorldBankAPIError(
            f"World Bank API request failed: {exc}"
        ) from exc

    except ValueError as exc:
        raise WorldBankAPIError(
            "World Bank API returned invalid JSON."
        ) from exc

    if not isinstance(payload, list) or len(payload) < 2:
        raise WorldBankAPIError(
            "Unexpected response from World Bank API."
        )

    records = payload[1]

    if not records:
        return {
            "country": country,
            "indicator": indicator_key,
            "indicator_code": indicator_code,
            "indicator_name": indicator_info["name"],
            "unit": indicator_info["unit"],
            "start_year": start_year,
            "end_year": end_year,
            "observations": []
        }

    observations = []

    for record in records:
        value = record.get("value")

        if value is not None:
            observations.append({
                "year": int(record["date"]),
                "value": value
            })

    observations.sort(key=lambda item: item["year"])

    country_name = records[0].get(
        "country", {}
    ).get("value", country)

    return {
        "country_code": country,
        "country": country_name,
        "indicator": indicator_key,
        "indicator_code": indicator_code,
        "indicator_name": indicator_info["name"],
        "unit": indicator_info["unit"],
        "start_year": start_year,
        "end_year": end_year,
        "observations": observations
    }
