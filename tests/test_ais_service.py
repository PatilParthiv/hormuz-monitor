"""Tests for the AISStream WebSocket service."""

import time
from datetime import datetime, timezone
import pytest

from backend.services.ais_service import (
    AISService,
    normalize_ship_type,
    is_vessel_underway,
)


def test_missing_ais_key_behavior(monkeypatch):
    """Missing AISSTREAM_API_KEY must not crash service and must mark connected: false."""
    monkeypatch.delenv("AISSTREAM_API_KEY", raising=False)
    service = AISService()
    service.start()

    status = service.get_status()
    assert status["connected"] is False
    assert "AISSTREAM_API_KEY" in (status["error"] or "")
    assert status["active_vessels"] == 0


def test_ais_messages_update_in_memory_vessel_state():
    """PositionReport and ShipStaticData messages must update in-memory vessel store."""
    service = AISService()

    # 1. Position report for MMSI 123456789
    pos_msg = {
        "MessageType": "PositionReport",
        "MetaData": {
            "MMSI": 123456789,
            "ShipName": "OCEAN STAR",
            "latitude": 26.54321,
            "longitude": 56.12345,
            "time_utc": "2026-09-20 12:00:00.000 +0000 UTC",
        },
        "Message": {
            "PositionReport": {
                "UserID": 123456789,
                "Latitude": 26.54321,
                "Longitude": 56.12345,
                "Sog": 14.2,
                "Cog": 182.5,
                "TrueHeading": 180,
                "NavigationalStatus": 0,
            }
        }
    }
    service.process_message(pos_msg)

    vessels = service.get_active_vessels()
    assert len(vessels) == 1
    v = vessels[0]
    assert v["mmsi"] == 123456789
    assert v["name"] == "OCEAN STAR"
    assert v["latitude"] == 26.54321
    assert v["longitude"] == 56.12345
    assert v["sog"] == 14.2
    assert v["cog"] == 182.5
    assert v["heading"] == 180
    assert v["is_underway"] is True

    # 2. Static data report for same MMSI providing Tanker type code 80
    static_msg = {
        "MessageType": "ShipStaticData",
        "MetaData": {
            "MMSI": 123456789,
            "ShipName": "OCEAN STAR",
        },
        "Message": {
            "ShipStaticData": {
                "Name": "OCEAN STAR",
                "Type": 80,
            }
        }
    }
    service.process_message(static_msg)

    vessels = service.get_active_vessels()
    assert len(vessels) == 1
    assert vessels[0]["ship_type"] == "Tanker"


def test_stale_vessels_are_removed():
    """Vessels older than 15 minutes (900s) must be pruned from active vessel store."""
    service = AISService()

    # Add active vessel
    service.process_message({
        "MessageType": "PositionReport",
        "MetaData": {"MMSI": 111111111, "ShipName": "ACTIVE SHIP"},
        "Message": {"PositionReport": {"UserID": 111111111, "Sog": 10.0}}
    })

    # Add stale vessel by modifying timestamp to 20 minutes ago
    service.process_message({
        "MessageType": "PositionReport",
        "MetaData": {"MMSI": 999999999, "ShipName": "STALE SHIP"},
        "Message": {"PositionReport": {"UserID": 999999999, "Sog": 0.0}}
    })

    with service._lock:
        service._vessels[999999999]["last_seen_ts"] = time.time() - 1200  # 20 min ago

    # Run pruning
    pruned = service.prune_stale_vessels(max_age_seconds=900)
    assert pruned == 1

    active = service.get_active_vessels()
    assert len(active) == 1
    assert active[0]["mmsi"] == 111111111


def test_malformed_ais_messages_ignored_safely():
    """Malformed or partial messages must not crash the service or corrupt state."""
    service = AISService()

    # None and empty
    service.process_message(None)
    service.process_message({})
    service.process_message("not a dict")

    # Missing MMSI
    service.process_message({"MessageType": "PositionReport", "Message": {}})

    # Non-numeric lat/lon
    service.process_message({
        "MessageType": "PositionReport",
        "MetaData": {"MMSI": 222222222, "latitude": "invalid", "longitude": None},
        "Message": {"PositionReport": {"UserID": 222222222, "Sog": "fast"}}
    })

    # Service must continue working cleanly
    active = service.get_active_vessels()
    assert len(active) == 1
    assert active[0]["mmsi"] == 222222222
    assert active[0]["latitude"] is None


def test_vessel_summary_normalized_categories():
    """Summary must categorize Tanker, Cargo, Passenger, Other and underway status."""
    service = AISService()

    # Tanker (Type 84, SOG 12.0 -> Underway)
    service.process_message({
        "MessageType": "ShipStaticData",
        "MetaData": {"MMSI": 100},
        "Message": {"ShipStaticData": {"Type": 84}}
    })
    service.process_message({
        "MessageType": "PositionReport",
        "MetaData": {"MMSI": 100},
        "Message": {"PositionReport": {"UserID": 100, "Sog": 12.0}}
    })

    # Cargo (Type 70, SOG 0.2, nav_status 1 -> Stationary)
    service.process_message({
        "MessageType": "ShipStaticData",
        "MetaData": {"MMSI": 200},
        "Message": {"ShipStaticData": {"Type": 70}}
    })
    service.process_message({
        "MessageType": "PositionReport",
        "MetaData": {"MMSI": 200},
        "Message": {"PositionReport": {"UserID": 200, "Sog": 0.2, "NavigationalStatus": 1}}
    })

    # Passenger (Type 65, SOG 18.0 -> Underway)
    service.process_message({
        "MessageType": "ShipStaticData",
        "MetaData": {"MMSI": 300},
        "Message": {"ShipStaticData": {"Type": 65}}
    })
    service.process_message({
        "MessageType": "PositionReport",
        "MetaData": {"MMSI": 300},
        "Message": {"PositionReport": {"UserID": 300, "Sog": 18.0}}
    })

    # Other (Type 30 / Fishing, SOG 0.1 -> Stationary)
    service.process_message({
        "MessageType": "ShipStaticData",
        "MetaData": {"MMSI": 400},
        "Message": {"ShipStaticData": {"Type": 30}}
    })
    service.process_message({
        "MessageType": "PositionReport",
        "MetaData": {"MMSI": 400},
        "Message": {"PositionReport": {"UserID": 400, "Sog": 0.1}}
    })

    summary = service.get_summary()
    assert summary["active_vessels"] == 4
    assert summary["underway_vessels"] == 2
    assert summary["stationary_vessels"] == 2
    assert summary["vessel_types"]["Tanker"] == 1
    assert summary["vessel_types"]["Cargo"] == 1
    assert summary["vessel_types"]["Passenger"] == 1
    assert summary["vessel_types"]["Other"] == 1
    assert summary["observed_since_start"] == 4
    assert summary["provider"] == "AISStream"


def test_ship_type_and_underway_helpers():
    """Unit tests for standalone helper functions."""
    assert normalize_ship_type(80) == "Tanker"
    assert normalize_ship_type("89") == "Tanker"
    assert normalize_ship_type(72) == "Cargo"
    assert normalize_ship_type(60) == "Passenger"
    assert normalize_ship_type(31) == "Other"
    assert normalize_ship_type(None) == "Other"
    assert normalize_ship_type("unknown") == "Other"

    # Underway checks
    assert is_vessel_underway(12.5, None) is True
    assert is_vessel_underway(0.2, None) is False
    assert is_vessel_underway(0.5, None) is False  # threshold is > 0.5
    assert is_vessel_underway(0.51, None) is True
    assert is_vessel_underway(None, 0) is True  # NavStatus 0 = underway engine
    assert is_vessel_underway(10.0, 1) is False  # NavStatus 1 = at anchor
    assert is_vessel_underway(None, 5) is False  # NavStatus 5 = moored
