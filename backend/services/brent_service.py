"""U.S. EIA API v2 Service for Brent Crude Spot Price (RBRTE).

Queries Europe Brent Spot Price FOB daily series, normalizes observations,
computes change metrics, and caches responses in memory for 30 minutes.
Handles API failures gracefully by returning stale data if available,
or raising structured exceptions for 503 responses.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from backend.cache import brent_cache

logger = logging.getLogger(__name__)

EIA_API_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
CACHE_KEY = "brent_crude_rbrte"


class BrentServiceError(Exception):
    """Base exception for Brent service errors."""
    def __init__(self, message: str, status_code: int = 503, detail: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail or message


def normalize_eia_response(raw_data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], float, float, float, float]:
    """Verify schema and extract sorted history, latest, previous, change, and change_percent.

    Defensive against missing keys, non-numeric values, nulls, and schema variations.
    """
    if not isinstance(raw_data, dict):
        raise BrentServiceError("Invalid EIA response format: expected JSON object")

    response_obj = raw_data.get("response")
    if not isinstance(response_obj, dict):
        raise BrentServiceError("Invalid EIA response: missing 'response' container")

    data_rows = response_obj.get("data")
    if not isinstance(data_rows, list):
        raise BrentServiceError("Invalid EIA response: missing 'data' list")

    parsed_history: List[Dict[str, Any]] = []
    for row in data_rows:
        if not isinstance(row, dict):
            continue
        period = row.get("period")
        val = row.get("value")

        if not period or val is None:
            continue

        try:
            numeric_val = round(float(val), 2)
        except (ValueError, TypeError):
            continue

        parsed_history.append({
            "date": str(period),
            "value": numeric_val,
        })

    if not parsed_history:
        raise BrentServiceError("No valid price observations found in EIA response")

    # Sort into chronological ascending order by date
    parsed_history.sort(key=lambda x: x["date"])

    # Limit to latest 45 observations if more were returned
    if len(parsed_history) > 45:
        parsed_history = parsed_history[-45:]

    latest = parsed_history[-1]["value"]
    if len(parsed_history) >= 2:
        previous = parsed_history[-2]["value"]
    else:
        previous = latest

    change = round(latest - previous, 2)
    if previous > 0:
        change_percent = round(((latest - previous) / previous) * 100, 2)
    else:
        change_percent = 0.0

    return parsed_history, latest, previous, change, change_percent


def fetch_brent_data(force_refresh: bool = False) -> Dict[str, Any]:
    """Retrieve Brent crude spot price data from memory cache or U.S. EIA API v2.

    Returns structured dict matching API specification.
    If network/API fails, returns last successful cache with stale: true.
    If no cached data exists, raises BrentServiceError (HTTP 503).
    """
    if not force_refresh:
        cached = brent_cache.get(CACHE_KEY)
        if cached:
            return cached

    api_key = os.getenv("EIA_API_KEY", "").strip()
    if not api_key:
        # Check if fallback cached data exists
        last_success = brent_cache.get_last_successful(CACHE_KEY)
        if last_success:
            stale_copy = dict(last_success)
            stale_copy["stale"] = True
            stale_copy["error"] = "EIA_API_KEY not configured. Serving cached data."
            return stale_copy
        raise BrentServiceError(
            "Brent price temporarily unavailable",
            status_code=503,
            detail="EIA_API_KEY environment variable is not configured."
        )

    params = {
        "api_key": api_key,
        "frequency": "daily",
        "data[0]": "value",
        "facets[series][]": "RBRTE",
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "length": 45,
    }

    try:
        resp = requests.get(EIA_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        raw_json = resp.json()

        # EIA API might return an error message inside 200 JSON
        if "error" in raw_json:
            err_msg = str(raw_json.get("error"))
            raise BrentServiceError(f"EIA API returned error: {err_msg}", detail=err_msg)

        history, latest, previous, change, change_percent = normalize_eia_response(raw_json)

        payload = {
            "series": "RBRTE",
            "name": "Europe Brent Spot Price FOB",
            "unit": "Dollars per Barrel",
            "latest": latest,
            "previous": previous,
            "change": change,
            "change_percent": change_percent,
            "history": history,
            "provider": "U.S. EIA",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "freshness": "latest_daily",
            "stale": False,
        }

        brent_cache.set(CACHE_KEY, payload)
        return payload

    except Exception as exc:
        logger.warning("Failed to refresh Brent data from EIA: %s", exc)
        last_success = brent_cache.get_last_successful(CACHE_KEY)
        if last_success:
            stale_copy = dict(last_success)
            stale_copy["stale"] = True
            stale_copy["error"] = f"Refresh failed: {str(exc)}. Serving last successful data."
            return stale_copy

        if isinstance(exc, BrentServiceError):
            raise exc
        raise BrentServiceError(
            "Brent price temporarily unavailable",
            status_code=503,
            detail=f"Unable to reach EIA API or parse response: {str(exc)}"
        )
