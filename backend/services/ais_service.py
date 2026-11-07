"""AISStream WebSocket Service for live Strait of Hormuz vessel tracking.

Connects to wss://stream.aisstream.io/v0/stream in a background daemon thread,
subscribes to bounding box [24.0, 53.0] to [28.5, 59.5], decodes position & static
reports, maintains thread-safe in-memory vessel store, and evicts entries older than 15 minutes.
"""

import json
import logging
import os
import random
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import websocket

logger = logging.getLogger(__name__)

AISSTREAM_WS_URL = "wss://stream.aisstream.io/v0/stream"
# Strait of Hormuz bounding box: [[SW lat, SW lon], [NE lat, NE lon]]
HORMUZ_BOUNDING_BOX = [[[24.0, 53.0], [28.5, 59.5]]]
STALE_THRESHOLD_SECONDS = 900  # 15 minutes


def normalize_ship_type(type_code: Any) -> str:
    """Normalize numeric AIS ship type code into broad human-readable categories.

    ITU/IMO standard:
    - 80-89: Tanker
    - 70-79: Cargo
    - 60-69: Passenger
    - All others (fishing, tugs, pleasure craft, special, unassigned): Other
    """
    if type_code is None:
        return "Other"
    try:
        code = int(type_code)
        if 80 <= code <= 89:
            return "Tanker"
        if 70 <= code <= 79:
            return "Cargo"
        if 60 <= code <= 69:
            return "Passenger"
        return "Other"
    except (ValueError, TypeError):
        # Fallback if string type provided
        str_code = str(type_code).strip().lower()
        if "tanker" in str_code:
            return "Tanker"
        if "cargo" in str_code or "container" in str_code or "carrier" in str_code:
            return "Cargo"
        if "passenger" in str_code or "ferry" in str_code:
            return "Passenger"
        return "Other"


def is_vessel_underway(sog: Optional[float], nav_status: Optional[int]) -> bool:
    """Determine whether a vessel is underway or stationary.

    Documented threshold:
    - Navigation Status: 0 ("Under way using engine"), 7 ("Engaged in fishing"), 8 ("Under way sailing").
    - If status indicates anchored (1), moored (5), or aground (6), considered stationary.
    - SOG threshold: Speed Over Ground > 0.5 knots indicates active motion.
    """
    if nav_status is not None:
        try:
            status_int = int(nav_status)
            if status_int in (1, 5, 6):  # At anchor, moored, aground
                return False
            if status_int in (0, 7, 8):  # Underway
                return True
        except (ValueError, TypeError):
            pass

    if sog is not None:
        try:
            return float(sog) > 0.5
        except (ValueError, TypeError):
            pass

    return False


class AISService:
    """Thread-safe in-memory AIS vessel tracking service."""

    def __init__(self, ws_url: str = AISSTREAM_WS_URL):
        self.ws_url = ws_url
        self.api_key: Optional[str] = None
        self._vessels: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        self._connected = False
        self._last_message_at: Optional[str] = None
        self._error_message: Optional[str] = None
        self._observed_since_start = 0

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._ws: Optional[websocket.WebSocketApp] = None

    def start(self) -> None:
        """Start the background daemon thread."""
        self.api_key = os.getenv("AISSTREAM_API_KEY", "").strip()
        if not self.api_key:
            self._error_message = "AISSTREAM_API_KEY environment variable is not configured."
            self._connected = False
            logger.info("AISService started in unconfigured state (missing API key).")
            return

        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="AISStreamWorker")
        self._thread.start()
        logger.info("AISService background worker started.")

    def stop(self) -> None:
        """Signal background thread to stop."""
        self._stop_event.set()
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass

    def _run_loop(self) -> None:
        """Main loop with exponential backoff reconnects."""
        backoff = 2
        max_backoff = 60

        while not self._stop_event.is_set():
            try:
                logger.info("Connecting to AISStream at %s...", self.ws_url)
                self._error_message = None

                self._ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                )
                self._ws.run_forever(ping_interval=30, ping_timeout=15)

            except Exception as exc:
                self._connected = False
                self._error_message = f"WebSocket connection error: {str(exc)}"
                logger.warning("AISStream connection failed: %s", exc)

            if self._stop_event.is_set():
                break

            sleep_duration = backoff + random.uniform(0.1, 1.0)
            logger.info("AISStream reconnecting in %.1f seconds...", sleep_duration)
            time.sleep(sleep_duration)
            backoff = min(backoff * 2, max_backoff)

        self._connected = False

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        """Handle connection open and send subscription."""
        self._connected = True
        self._error_message = None
        logger.info("Connected to AISStream. Sending bounding box subscription...")

        subscribe_msg = {
            "APIKey": self.api_key,
            "BoundingBoxes": HORMUZ_BOUNDING_BOX,
            "FilterMessageTypes": [
                "PositionReport",
                "StandardClassBPositionReport",
                "ExtendedClassBPositionReport",
                "ShipStaticData",
            ],
        }
        try:
            ws.send(json.dumps(subscribe_msg))
        except Exception as exc:
            logger.error("Failed to send AISStream subscription: %s", exc)

    def _on_message(self, ws: websocket.WebSocketApp, message: str) -> None:
        """Process incoming AIS JSON message safely."""
        try:
            data = json.loads(message)
            self.process_message(data)
        except json.JSONDecodeError:
            logger.debug("Received non-JSON message from AISStream: %s", message[:100])
        except Exception as exc:
            # Safe catch: malformed messages must never terminate listener
            logger.warning("Error processing AIS message: %s", exc)

    def _on_error(self, ws: websocket.WebSocketApp, error: Any) -> None:
        """Handle WebSocket error."""
        self._connected = False
        self._error_message = str(error)
        logger.warning("AISStream WebSocket error: %s", error)

    def _on_close(self, ws: websocket.WebSocketApp, close_status_code: Any, close_msg: Any) -> None:
        """Handle connection close."""
        self._connected = False
        logger.info("AISStream WebSocket closed (code=%s, msg=%s)", close_status_code, close_msg)

    def process_message(self, data: Dict[str, Any]) -> None:
        """Parse AISStream message structure and update vessel store.

        Defensive against missing keys and varying message types.
        """
        if not isinstance(data, dict):
            return

        msg_type = data.get("MessageType")
        metadata = data.get("MetaData") or {}
        inner_msg = data.get("Message") or {}

        mmsi_raw = metadata.get("MMSI") or (inner_msg.get(msg_type, {}).get("UserID") if msg_type else None)
        if mmsi_raw is None:
            return

        try:
            mmsi = int(mmsi_raw)
        except (ValueError, TypeError):
            return

        now_utc = datetime.now(timezone.utc)
        now_iso = now_utc.isoformat()
        now_ts = now_utc.timestamp()

        with self._lock:
            self._last_message_at = now_iso
            vessel = self._vessels.get(mmsi, {
                "mmsi": mmsi,
                "name": None,
                "latitude": None,
                "longitude": None,
                "sog": None,
                "cog": None,
                "heading": None,
                "ship_type_raw": None,
                "ship_type": "Other",
                "nav_status": None,
                "is_underway": False,
                "last_seen_iso": now_iso,
                "last_seen_ts": now_ts,
            })

            # Check if this is a newly observed vessel
            if mmsi not in self._vessels:
                self._observed_since_start += 1

            # Update Metadata fields
            ship_name = metadata.get("ShipName")
            if ship_name and ship_name.strip():
                vessel["name"] = ship_name.strip()

            meta_lat = metadata.get("latitude")
            meta_lon = metadata.get("longitude")
            if meta_lat is not None and meta_lon is not None:
                try:
                    vessel["latitude"] = round(float(meta_lat), 5)
                    vessel["longitude"] = round(float(meta_lon), 5)
                except (ValueError, TypeError):
                    pass

            # Inspect inner message payload
            if msg_type in ("PositionReport", "StandardClassBPositionReport", "ExtendedClassBPositionReport"):
                payload = inner_msg.get(msg_type) or {}
                if "Latitude" in payload and payload["Latitude"] is not None:
                    try:
                        vessel["latitude"] = round(float(payload["Latitude"]), 5)
                    except (ValueError, TypeError):
                        pass
                if "Longitude" in payload and payload["Longitude"] is not None:
                    try:
                        vessel["longitude"] = round(float(payload["Longitude"]), 5)
                    except (ValueError, TypeError):
                        pass
                if "Sog" in payload and payload["Sog"] is not None:
                    try:
                        vessel["sog"] = round(float(payload["Sog"]), 1)
                    except (ValueError, TypeError):
                        pass
                if "Cog" in payload and payload["Cog"] is not None:
                    try:
                        vessel["cog"] = round(float(payload["Cog"]), 1)
                    except (ValueError, TypeError):
                        pass
                if "TrueHeading" in payload and payload["TrueHeading"] is not None:
                    try:
                        vessel["heading"] = int(payload["TrueHeading"])
                    except (ValueError, TypeError):
                        pass
                if "NavigationalStatus" in payload and payload["NavigationalStatus"] is not None:
                    try:
                        vessel["nav_status"] = int(payload["NavigationalStatus"])
                    except (ValueError, TypeError):
                        pass

            elif msg_type == "ShipStaticData":
                payload = inner_msg.get("ShipStaticData") or {}
                if "Name" in payload and payload["Name"]:
                    vessel["name"] = payload["Name"].strip()
                if "Type" in payload and payload["Type"] is not None:
                    vessel["ship_type_raw"] = payload["Type"]
                    vessel["ship_type"] = normalize_ship_type(payload["Type"])

            # Compute underway flag using updated fields
            vessel["is_underway"] = is_vessel_underway(vessel.get("sog"), vessel.get("nav_status"))
            vessel["last_seen_iso"] = now_iso
            vessel["last_seen_ts"] = now_ts

            self._vessels[mmsi] = vessel

    def prune_stale_vessels(self, max_age_seconds: int = STALE_THRESHOLD_SECONDS) -> int:
        """Evict vessels that haven't sent an update in max_age_seconds (15 minutes)."""
        cutoff = datetime.now(timezone.utc).timestamp() - max_age_seconds
        with self._lock:
            initial_count = len(self._vessels)
            self._vessels = {
                mmsi: v for mmsi, v in self._vessels.items()
                if v.get("last_seen_ts", 0) >= cutoff
            }
            return initial_count - len(self._vessels)

    def get_status(self) -> Dict[str, Any]:
        """Return provider connection health and telemetry."""
        self.prune_stale_vessels()
        with self._lock:
            active_count = len(self._vessels)
            return {
                "connected": self._connected,
                "provider": "AISStream",
                "active_vessels": active_count,
                "last_message_at": self._last_message_at,
                "error": self._error_message,
            }

    def get_active_vessels(self) -> List[Dict[str, Any]]:
        """Return list of vessels active in the last 15 minutes."""
        self.prune_stale_vessels()
        with self._lock:
            return list(self._vessels.values())

    def get_summary(self) -> Dict[str, Any]:
        """Generate aggregated summary of currently active vessels."""
        self.prune_stale_vessels()
        with self._lock:
            active = list(self._vessels.values())
            active_count = len(active)
            underway_count = sum(1 for v in active if v.get("is_underway"))
            stationary_count = active_count - underway_count

            type_counts = {"Tanker": 0, "Cargo": 0, "Passenger": 0, "Other": 0}
            for v in active:
                category = v.get("ship_type", "Other")
                type_counts[category] = type_counts.get(category, 0) + 1

            return {
                "active_vessels": active_count,
                "underway_vessels": underway_count,
                "stationary_vessels": stationary_count,
                "vessel_types": type_counts,
                "observed_since_start": self._observed_since_start,
                "provider": "AISStream",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "freshness": "live" if self._connected else "disconnected",
                "connected": self._connected,
            }


# Global singleton instance
ais_service = AISService()
