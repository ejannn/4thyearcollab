<!-- .github/copilot-instructions.md - guidance for AI coding agents -->
# Project summary

This repository is a small FastAPI-based sensor-monitoring service with a lightweight HTML dashboard. A Raspberry Pi (future) will POST sensor JSON to the API, which stores readings in PostgreSQL via SQLAlchemy. The UI polls a GET endpoint for live/simulated data.

Key files
- `main.py` — FastAPI app, endpoints: `GET /api/sensor` (simulated live data) and `POST /api/sensor` (store reading). Also serves the dashboard at `/` using Jinja2 templates.
- `models.py` — SQLAlchemy ORM model `SensorReading` and table schema.
- `schemas.py` — Pydantic schemas: `SensorData`, `Pzem004tData`, `Dht11Data` used for request validation.
- `database.py` — DB engine and `SessionLocal` factory. Note: `DATABASE_URL` is hard-coded here for local Postgres.
- `init_db.py` — helper script that creates the database (via psycopg2) and runs SQLAlchemy `Base.metadata.create_all`.
- `templates/dashboard.html` — single-page dashboard using Chart.js and polling `/api/sensor` every 2s.

High-level architecture and flow
- Inbound data flow: Raspberry Pi -> POST /api/sensor (JSON validated by Pydantic) -> SQLAlchemy `Session` -> `sensor_readings` table.
- Read path for UI: Browser -> GET / (serves HTML) -> client JS polls GET /api/sensor for the latest reading. Currently the GET endpoint simulates changes using an in-memory `latest_data` object until Pi is integrated.
- Persistence: `SensorReading` stores one reading per POST; timestamp is recorded by model default.

Project-specific conventions & patterns for AI contributors
- Database sessions: `get_db()` yields a `SessionLocal()` and always closes in finally. Use `Depends(get_db)` for route handlers that touch the DB.
- Models vs Schemas: Use Pydantic `schemas.py` for request/response validation and SQLAlchemy `models.py` for persistence — convert fields explicitly (see `main.py:update_sensor_data`).
- Hard-coded credentials: `database.py` and `init_db.py` have example credentials (`postgres:nieljhon1@localhost`). Do not change credentials in production — instead, follow the repository pattern of editing `database.py` or use environment variables (not currently implemented).
- Frontend polling: dashboard uses simple polling (2s). If adding a websocket or server-sent events, update `templates/dashboard.html` and `main.py` routing accordingly.

How to run locally (discovered from files)
1. Ensure PostgreSQL is running locally and credentials match `init_db.py`/`database.py`.
2. Create DB and tables (one-time):
   - Run `python init_db.py` (this will create the database `sensor_db` if missing and create tables).
3. Start app (development):
   - Recommended: use Uvicorn from the workspace root: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`.
4. Open browser to `http://localhost:8000/` to view the dashboard. The dashboard polls `/api/sensor`.

Important examples and patterns to reference when editing
- Converting Pydantic -> ORM (from `main.py`):
  - Create ORM instance explicitly: `SensorReading(device_name=data.deviceName, voltage=data.pzem004t.voltage, ...)`
  - Add/commit/refresh using the session passed by `Depends(get_db)`.
- Template usage: `templates = Jinja2Templates(directory="templates")` and `TemplateResponse("dashboard.html", {"request": request})`.

Edge-cases and behaviour to preserve
- GET `/api/sensor` currently mutates an in-memory `latest_data` for simulation — when connecting the Pi, replace the GET handler with a DB-backed read (or keep simulation behind a feature flag).
- `init_db.py` connects to the `postgres` database first and creates `sensor_db` if missing. Keep this approach if adding an automated environment setup script.

Testing, linting and build
- No tests or CI found in repo. For quick manual checks:
  - Run `python -m pip install -r requirements.txt` if you add one (none exists currently).
  - Start the app with `uvicorn` and exercise endpoints with `curl` or browser.

Security & operational notes for AI edits
- Never commit real secrets. The codebase currently contains example plaintext credentials — replace with environment variables and document the change.
- Keep CORS middleware as-is for development (`allow_origins=["*"]`). For production tighten origins.

When making changes, reference these files for context: `main.py`, `models.py`, `schemas.py`, `database.py`, `init_db.py`, and `templates/dashboard.html`.

If you need clarification from the repo owner
- Which Postgres credentials/environment are preferred (env vars vs editing `database.py`)?
- Should the GET `/api/sensor` remain simulated when Pi is available, or switch to DB-backed reads?

If you made edits, run these quick checks
- `python init_db.py` -> should print database/tables created or indicate they exist.
- `uvicorn main:app --reload` -> open `http://localhost:8000/` and confirm dashboard loads and charts update.

Thanks — ask the maintainer about preferred secrets/storage pattern before committing credential changes.
