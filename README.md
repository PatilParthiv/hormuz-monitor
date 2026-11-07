# Strait of Hormuz — Intelligence & Disruption Monitor

An editorial intelligence dashboard monitoring maritime transit activity, conflict risk, and crude oil markets around the Strait of Hormuz chokepoint. Built with Streamlit, powered by a lightweight, database-free Flask backend streaming live vessel telemetry from AISStream and official daily Europe Brent Spot Prices from the U.S. Energy Information Administration (EIA) API v2.

---

## Architecture Overview

```
hormuz-monitor/
├── backend/
│   ├── __init__.py
│   ├── app.py                   # Flask API entry point & routes (/api/health, /api/vessels/*, /api/brent)
│   ├── cache.py                 # Thread-safe in-memory TTL cache (no database)
│   └── services/
│       ├── __init__.py
│       ├── ais_service.py       # AISStream WebSocket daemon thread with auto-reconnect & 15m pruning
│       └── brent_service.py     # U.S. EIA API v2 client with 30m cache & stale fallback
├── frontend/
│   ├── app.py                   # Preserved Streamlit frontend with resilient requests-based API helper
│   └── hormuz_port.jpg          # Editorial port visual hero asset
├── tests/
│   ├── __init__.py
│   ├── test_ais_service.py      # Tests for AIS decoding, normalization, and pruning
│   ├── test_brent_service.py    # Tests for EIA schema normalization, math calculations, and caching
│   └── test_api_routes.py       # Tests for API endpoints and client resilience
├── .env                         # Local environment variables
├── .env.example                 # Template for environment configuration
├── .gitignore                   # Ignores credentials and virtual environments
├── requirements.txt             # Pinned package requirements
└── README.md                    # Setup and execution guide
```

---

## Prerequisites

- **Python 3.10+** (Tested on Python 3.14)
- **Windows PowerShell**

---

## Installation & Setup

1. Open Windows PowerShell and navigate to the project directory:

```powershell
cd "C:\Users\Mrudula\.gemini\antigravity\scratch\hormuz-monitor"
```

2. Create and activate a Python virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

3. Install required packages:

```powershell
python -m pip install -r requirements.txt
```

4. Configure environment variables:

Copy `.env.example` to `.env` and configure your API keys (optional; application operates in clean fallback mode if keys are omitted):

```powershell
Copy-Item .env.example .env
```

Edit `.env`:
```env
AISSTREAM_API_KEY=your_aisstream_api_key_here
EIA_API_KEY=your_eia_api_key_here
FLASK_API_URL=http://127.0.0.1:5000
FLASK_PORT=5000
```

---

## Running the Application

### 1. Start the Flask Backend

In the first terminal window:

```powershell
cd "C:\Users\Mrudula\.gemini\antigravity\scratch\hormuz-monitor"
.venv\Scripts\Activate.ps1
python -m backend.app
```

Verify backend health in your browser or terminal:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health"
```

### 2. Start the Streamlit Frontend

In a second terminal window:

```powershell
cd "C:\Users\Mrudula\.gemini\antigravity\scratch\hormuz-monitor"
.venv\Scripts\Activate.ps1
python -m streamlit run frontend/app.py --server.port 8501
```

---

## Service URLs

| Component | URL | Description |
| :--- | :--- | :--- |
| **Frontend UI** | [http://localhost:8501](http://localhost:8501) | Streamlit Intelligence Dashboard |
| **Backend Health** | [http://127.0.0.1:5000/api/health](http://127.0.0.1:5000/api/health) | API health check |
| **Vessel Status** | [http://127.0.0.1:5000/api/vessels/status](http://127.0.0.1:5000/api/vessels/status) | AIS connection state and active count |
| **Vessel Summary** | [http://127.0.0.1:5000/api/vessels/summary](http://127.0.0.1:5000/api/vessels/summary) | Aggregated vessel categories & motion |
| **Active Vessels** | [http://127.0.0.1:5000/api/vessels](http://127.0.0.1:5000/api/vessels) | Current positions for map overlay |
| **Brent Crude** | [http://127.0.0.1:5000/api/brent](http://127.0.0.1:5000/api/brent) | Latest Europe Brent daily price from EIA |

---

## Running Automated Tests

Run the complete test suite (using mocked responses; no API keys required):

```powershell
cd "C:\Users\Mrudula\.gemini\antigravity\scratch\hormuz-monitor"
.venv\Scripts\Activate.ps1
python -m pytest -v
```

---

## Key Design Principles & Boundaries

- **Zero Database**: No SQLite, MySQL, or PostgreSQL. Memory structures and thread-safe TTL caches are used exclusively.
- **Strict Metric Integrity**: Only verified live signals (active vessels, underway/stationary counts, ship types, EIA spot prices) are marked live. Queue counts, daily baseline throughput, and transit totals not provided by raw AIS remain explicitly identified as baseline/sample estimates.
- **Fault-Tolerant Operation**: If external feeds are offline or unconfigured, the application runs without crashing or displaying stack traces.
