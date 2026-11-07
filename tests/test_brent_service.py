"""Tests for U.S. EIA API v2 Brent Crude Service."""

from unittest.mock import MagicMock, patch
import pytest

from backend.cache import brent_cache
from backend.services.brent_service import (
    BrentServiceError,
    fetch_brent_data,
    normalize_eia_response,
    CACHE_KEY,
)


@pytest.fixture(autouse=True)
def clear_brent_cache():
    """Ensure cache is reset before each test."""
    brent_cache.clear()
    yield
    brent_cache.clear()


def test_normalize_eia_response_valid():
    """Verify raw EIA v2 schema normalization, date ordering, and calculation."""
    # Descending input from EIA API
    raw_eia = {
        "response": {
            "total": 3,
            "dateFormat": "YYYY-MM-DD",
            "frequency": "daily",
            "data": [
                {"period": "2026-09-18", "value": "82.41", "series": "RBRTE"},
                {"period": "2026-09-17", "value": 81.96, "series": "RBRTE"},
                {"period": "2026-09-16", "value": 80.00, "series": "RBRTE"},
            ]
        }
    }

    history, latest, previous, change, change_percent = normalize_eia_response(raw_eia)

    # Must be sorted chronologically ascending
    assert len(history) == 3
    assert history[0]["date"] == "2026-09-16"
    assert history[0]["value"] == 80.00
    assert history[-1]["date"] == "2026-09-18"
    assert history[-1]["value"] == 82.41

    assert latest == 82.41
    assert previous == 81.96
    assert change == 0.45
    # (82.41 - 81.96) / 81.96 * 100 = 0.549... -> 0.55%
    assert change_percent == 0.55


def test_normalize_eia_response_null_and_invalid_filtering():
    """Defensive parsing must discard nulls and non-numeric values."""
    raw_eia = {
        "response": {
            "data": [
                {"period": "2026-09-18", "value": 85.00},
                {"period": "2026-09-17", "value": None},
                {"period": "2026-09-16", "value": "N/A"},
                {"period": "2026-09-15", "value": 80.00},
            ]
        }
    }

    history, latest, previous, change, change_percent = normalize_eia_response(raw_eia)
    assert len(history) == 2
    assert history[0]["date"] == "2026-09-15"
    assert history[1]["date"] == "2026-09-18"
    assert latest == 85.00
    assert previous == 80.00
    assert change == 5.00
    assert change_percent == 6.25


def test_normalize_eia_response_empty_raises_error():
    """Empty data rows must raise BrentServiceError."""
    with pytest.raises(BrentServiceError):
        normalize_eia_response({"response": {"data": []}})

    with pytest.raises(BrentServiceError):
        normalize_eia_response({"invalid": "structure"})


def test_eia_cache_used(monkeypatch):
    """Successful API response must be cached and not re-queried within TTL."""
    monkeypatch.setenv("EIA_API_KEY", "dummy_test_key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": {
            "data": [
                {"period": "2026-09-18", "value": 82.41},
                {"period": "2026-09-17", "value": 81.96},
            ]
        }
    }

    with patch("requests.get", return_value=mock_response) as mock_get:
        # First call fetches from API
        res1 = fetch_brent_data()
        assert res1["latest"] == 82.41
        assert res1["stale"] is False
        assert mock_get.call_count == 1

        # Second call must hit memory cache
        res2 = fetch_brent_data()
        assert res2["latest"] == 82.41
        assert mock_get.call_count == 1


def test_eia_failure_returns_stale_data_if_cached(monkeypatch):
    """Network failure on refresh must return cached data marked stale: true."""
    monkeypatch.setenv("EIA_API_KEY", "dummy_test_key")

    # Prime cache with successful data
    brent_cache.set(CACHE_KEY, {
        "series": "RBRTE",
        "name": "Europe Brent Spot Price FOB",
        "latest": 82.41,
        "previous": 81.96,
        "change": 0.45,
        "change_percent": 0.55,
        "history": [{"date": "2026-09-18", "value": 82.41}],
        "provider": "U.S. EIA",
        "freshness": "latest_daily",
        "stale": False,
    })

    # Clear active TTL to force refresh
    brent_cache._cache.clear()

    # Next call fails with connection error
    with patch("requests.get", side_effect=Exception("Connection timed out")):
        res = fetch_brent_data(force_refresh=True)
        assert res["stale"] is True
        assert "Refresh failed" in res.get("error", "")
        assert res["latest"] == 82.41


def test_eia_missing_key_or_failure_no_cache(monkeypatch):
    """When no cache exists and EIA key is missing or call fails, raise HTTP 503 error."""
    monkeypatch.delenv("EIA_API_KEY", raising=False)

    with pytest.raises(BrentServiceError) as exc_info:
        fetch_brent_data()
    assert exc_info.value.status_code == 503
    assert "EIA_API_KEY" in exc_info.value.detail
