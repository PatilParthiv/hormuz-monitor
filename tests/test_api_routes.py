"""Tests for Flask API routes and frontend client resilience."""

from unittest.mock import MagicMock, patch
import pytest

from backend.app import create_app
from backend.cache import brent_cache
from frontend.app import (
    get_vessel_status,
    get_vessel_summary,
    get_active_vessels,
    get_brent_data,
)


@pytest.fixture
def client():
    """Create Flask test client."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_health_endpoint_returns_200(client):
    """GET /api/health must return HTTP 200 with service and status."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["service"] == "hormuz-monitor-api"
    assert data["status"] == "ok"


def test_vessels_status_endpoint(client):
    """GET /api/vessels/status returns provider, connection status, and vessel count."""
    resp = client.get("/api/vessels/status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["provider"] == "AISStream"
    assert "connected" in data
    assert "active_vessels" in data


def test_vessels_summary_endpoint(client):
    """GET /api/vessels/summary returns normalized summary structure."""
    resp = client.get("/api/vessels/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "active_vessels" in data
    assert "underway_vessels" in data
    assert "stationary_vessels" in data
    assert "vessel_types" in data
    assert "Tanker" in data["vessel_types"]
    assert "Cargo" in data["vessel_types"]


def test_brent_endpoint_503_when_unconfigured(client, monkeypatch):
    """GET /api/brent returns HTTP 503 structured JSON when EIA key is missing and cache empty."""
    brent_cache.clear()
    monkeypatch.delenv("EIA_API_KEY", raising=False)

    resp = client.get("/api/brent")
    assert resp.status_code == 503
    data = resp.get_json()
    assert data["error"] == "Brent price temporarily unavailable"
    assert "detail" in data
    assert data["provider"] == "U.S. EIA"


def test_brent_endpoint_200_when_cached(client):
    """GET /api/brent returns HTTP 200 with expected structure when data is available."""
    brent_cache.set("brent_crude_rbrte", {
        "series": "RBRTE",
        "name": "Europe Brent Spot Price FOB",
        "unit": "Dollars per Barrel",
        "latest": 82.41,
        "previous": 81.96,
        "change": 0.45,
        "change_percent": 0.55,
        "history": [
            {"date": "2026-09-17", "value": 81.96},
            {"date": "2026-09-18", "value": 82.41},
        ],
        "provider": "U.S. EIA",
        "fetched_at": "2026-09-20T12:00:00Z",
        "freshness": "latest_daily",
        "stale": False,
    })

    resp = client.get("/api/brent")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["latest"] == 82.41
    assert data["change"] == 0.45
    assert len(data["history"]) == 2


def test_frontend_api_helper_handles_timeout_and_errors():
    """Streamlit frontend API helpers must not crash or throw when backend is unreachable."""
    # Clear streamlit cache to test direct helper call
    get_vessel_status.clear()
    get_vessel_summary.clear()
    get_active_vessels.clear()
    get_brent_data.clear()

    # Simulate connection error
    with patch("requests.get", side_effect=Exception("Connection refused")):
        assert get_vessel_status() is None
        assert get_vessel_summary() is None
        assert get_active_vessels() is None
        assert get_brent_data() is None
