"""Flask Application for Strait of Hormuz Intelligence Monitor.

Serves REST endpoints for live vessel traffic (AISStream) and Brent crude spot prices (U.S. EIA).
Strictly in-memory: no database.
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

from backend.services.ais_service import ais_service
from backend.services.brent_service import fetch_brent_data, BrentServiceError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("hormuz-backend")


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)
    CORS(app)

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "service": "hormuz-monitor-api",
            "status": "ok"
        }), 200

    @app.route("/api/vessels/status", methods=["GET"])
    def vessels_status():
        """Current AISStream WebSocket connection status and vessel count."""
        status = ais_service.get_status()
        return jsonify(status), 200

    @app.route("/api/vessels", methods=["GET"])
    def list_vessels():
        """Active vessels observed in the Strait of Hormuz in the last 15 minutes."""
        vessels = ais_service.get_active_vessels()
        return jsonify({
            "vessels": vessels,
            "total": len(vessels),
            "provider": "AISStream",
            "fetched_at": ais_service.get_summary()["fetched_at"],
        }), 200

    @app.route("/api/vessels/summary", methods=["GET"])
    def vessels_summary():
        """Aggregated breakdown of active vessels, underway vs stationary, and ship types."""
        summary = ais_service.get_summary()
        return jsonify(summary), 200

    @app.route("/api/brent", methods=["GET"])
    def brent_price():
        """Latest Europe Brent Spot Price FOB (RBRTE) from U.S. EIA API v2."""
        force = request.args.get("refresh", "").lower() in ("1", "true", "yes")
        try:
            data = fetch_brent_data(force_refresh=force)
            return jsonify(data), 200
        except BrentServiceError as exc:
            logger.error("Brent service error: %s (detail: %s)", exc.message, exc.detail)
            return jsonify({
                "error": exc.message,
                "detail": exc.detail,
                "provider": "U.S. EIA"
            }), exc.status_code
        except Exception as exc:
            logger.exception("Unexpected error fetching Brent data: %s", exc)
            return jsonify({
                "error": "Brent price temporarily unavailable",
                "detail": str(exc),
                "provider": "U.S. EIA"
            }), 503

    return app


app = create_app()


def start_server():
    """Start background workers and run server."""
    ais_service.start()
    port = int(os.getenv("FLASK_PORT", 5000))
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    logger.info("Starting Flask server on http://%s:%s", host, port)
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    start_server()
