# Prophet Labs – Government-Grade Forecasting & Monitoring Platform

Prophet Labs is a secure, LAN-first analytics stack built on top of the NeuralProphet time-series engine. It ingests Australian public datasets and vetted OSINT feeds, enriches them with news/signals intelligence, trains NeuralProphet models, tracks forecast accuracy over time, and serves dashboards and APIs for decision-makers inside sensitive government networks.

## Key Capabilities
- **Secure, offline-ready operations:** Runs entirely on hardened Linux hosts without cloud dependencies; supports air-gapped deployments with optional controlled gateways.
- **Unified data ingestion:** Scheduled pipelines for Australian public data plus OSINT/news feeds, normalized into a common time-series schema with provenance metadata.
- **News & Signals Intelligence (NSI):** RSS/JSON feed ingestion, NLP enrichment (topics/entities/sentiment/risk), and aggregation into forecastable news-intensity metrics.
- **Forecast history & accuracy:** Every forecast is recorded, evaluated when actuals arrive, and labeled `happened=true/false` with tolerance rules; accuracy metrics are exposed via API/UI.
- **Government-style UI:** React/TypeScript console with dashboards, metric drilldowns, news panels, and accuracy/forecast-history views.
- **Structured logging & audit:** Per-domain rotating logs under `logs/` plus audit trails for administrative actions and startup events.

## Repository Layout
- `prophet_labs/` – Backend services (ingestion, modelling, tagging, reports, UI API, jobs) and NSI modules.
- `frontend/prophet-labs-console/` – React + Vite console.
- `ops/` – Diagnostics, LAN discovery, bootstrap helpers, shell runners, and deployment templates.
- `config/` – Environment templates and accuracy thresholds.
- `data/`, `models/`, `outputs/`, `logs/` – Default runtime storage locations (created as needed).
- `tests/` – Upstream NeuralProphet tests (may require packaged installation to run).

## Prerequisites
- Python 3.10+ with virtualenv support
- Node.js 18+ and npm
- SQLite (default) or PostgreSQL for production
- Optional: Redis for caching/queues; GPU drivers if using accelerated training

## Bootstrapping & Environment Setup
1. **Install system deps (optional automation):**
   ```bash
   bash ops/shell/install_dependencies.sh
   ```
   The script checks OS family and installs Python/Node/DB/Redis if available.

2. **Create/update environment file:**
   ```bash
   python -m ops.bootstrap --environment dev --yes
   ```
   Flags let you override ports, DB/Redis URLs, and force regeneration. The tool writes `.env` and prints recommended worker sizing.

3. **Diagnostics only (optional):**
   ```bash
   python -m ops.diagnostics
   ```
   Generates an environment report (CPU, RAM, disk, Redis/Postgres presence).

## Running the Platform
- **Development (API + UI with hot reload):**
  ```bash
  bash ops/shell/run_dev.sh
  ```
  Starts FastAPI (Uvicorn) on `${API_PORT:-8000}` and Vite dev server on `${FRONTEND_PORT:-3000}`, printing both localhost and LAN URLs.

- **Production preview (build + serve):**
  ```bash
  bash ops/shell/run_prod.sh
  ```
  Builds the frontend, starts Uvicorn with configured workers, and serves the built UI via `npm run preview`. Systemd unit templates live in `ops/templates/systemd/` and an nginx reverse-proxy example in `ops/templates/nginx/`.

- **Scheduled jobs:**
  Background tasks (ingestion, training, news fetch, forecast evaluation, report generation) are defined in `prophet_labs/jobs/tasks.py` and can be wired to APScheduler/Celery depending on configuration.

## Configuration
- **App settings:** `prophet_labs/config/settings.py` (env-backed) governs DB/Redis URLs, API host/port, job backends, caching, and feature flags.
- **Data sources:** `prophet_labs/config/sources.yaml` and `prophet_labs/news_ingestion/sources.yaml` enumerate structured and news/OSINT feeds.
- **Tagging thresholds:** `prophet_labs/config/thresholds.yaml` for core metrics; `config/accuracy_thresholds.yaml` for forecast tolerances.
- **News/NLP:** `prophet_labs/news_ingestion/nsi_config.yaml` controls language, topic/domain mappings, and NLP heuristics.

## Logging & Audit
- Logs are written to `logs/` with per-domain files: `app.log`, `ingestion.log`, `forecast.log`, `accuracy.log`, `ui.log`, `audit.log`, and `startup.log` (rotation configurable via env).
- Initialize logging once at process start via `prophet_labs.utils.logging_config.init_logging` if you launch custom entrypoints.
- Audit-sensitive actions (config changes, manual retrains, evaluation triggers) should log to `audit.log` with user and correlation identifiers.

## Forecast History & Accuracy
- Forecast issuance/evaluation models and utilities live under `prophet_labs/forecast_history/`.
- Every forecast is persisted with model version, horizon, bounds, and status. Pending forecasts are evaluated when actuals land using tolerances from `config/accuracy_thresholds.yaml`, marking `happened=true/false`.
- Accuracy aggregations (overall and by horizon buckets) are exposed via the API and surfaced in the UI’s metric detail views.

## News & Signals Intelligence (NSI)
- RSS/Atom/JSON feeds are defined in `prophet_labs/news_ingestion/sources.yaml` and fetched by `fetcher.py` using `rss_client.py` with ETag/Last-Modified support and size limits.
- NLP enrichment in `nsi_pipeline.py` performs language filtering, NER, topic/domain classification, sentiment, and risk scoring (offline/local models only).
- Aggregated daily news-intensity metrics are built in `prophet_labs/news_aggregation/aggregation.py` and treated like regular metrics for forecasting and tagging.

## Security Posture
- LAN-only by default; no external SaaS dependencies.
- Secrets and credentials are loaded from `.env` (or environment variables) and never hard-coded.
- Ingestion/OSINT connectors are pull-only and can be sandboxed behind organization-controlled gateways; no direct dark web access is embedded.
- Logs and audit trails provide provenance and traceability; enable SELinux/AppArmor and auditd on hosts per agency policy.

## Troubleshooting
- **Python imports for ops tools:** Run with `python -m ops.bootstrap` / `python -m ops.diagnostics` from the repo root so package imports resolve.
- **Frontend build issues:** Ensure Node 18+; reinstall deps via `npm install` inside `frontend/prophet-labs-console/` if needed.
- **Tests:** Upstream tests expect `neuralprophet` to be installed as a package; if running locally, install editable mode (`pip install -e .`) and ensure optional deps are present.

## License
This repository extends the NeuralProphet project (MIT License). See `LICENSE` for details.
