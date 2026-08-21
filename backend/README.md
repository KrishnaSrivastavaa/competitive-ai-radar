# Competitive AI Radar backend

## Local setup

Run the API from this directory:

```powershell
uv run uvicorn app.main:app --reload
```

Run the tests (they mock Bright Data and never make network calls):

```powershell
uv run pytest
```

The default local database is `sqlite:///./competitive_ai_radar.db`.

## Bright Data Scraper Studio configuration

Copy `.env.example` to `.env` and fill in your Bright Data credentials. The backend loads `backend/.env` on startup. Environment variables already set in your shell take precedence over `.env` values.

```powershell
Copy-Item .env.example .env
```

Install the official Bright Data CLI (Node.js 20 or newer is required):

```powershell
npm install -g @brightdata/cli
```

The application passes `BRIGHT_DATA_API_KEY` to the CLI as its documented `BRIGHTDATA_API_KEY` child-process environment variable. The same key is used as a Bearer token for the Collection API. It is never added to the CLI command line.

Optional settings are `BRIGHT_DATA_API_BASE_URL` (defaults to `https://api.brightdata.com`), `BRIGHT_DATA_TIMEOUT_SECONDS` (30), `BRIGHT_DATA_POLL_INTERVAL_SECONDS` (5), `BRIGHT_DATA_POLL_TIMEOUT_SECONDS` (300), `BRIGHT_DATA_CLI_COMMAND` (defaults to `brightdata`), and `BRIGHT_DATA_CLI_TIMEOUT_SECONDS` (600).

## Implemented Bright Data workflow

The integration uses Bright Data's Scraper Studio CLI for creation and the Collection API for runs:

1. `brightdata scraper create <url> <description> --name <name> --timeout 600 --json` creates and waits for an AI-generated collector.
2. The CLI returns a JSON envelope containing `collector_id` and `status`; the backend saves the ID only when status is `done`.
3. `POST /dca/trigger?collector={collector_id}&queue_next=1` runs the collector with `[ { "url": source_url } ]` and returns `collection_id` (`j_...`).
4. `GET /dca/dataset?id={collection_id}` is polled until it returns a JSON array. A JSON status object means the dataset is still building.

The CLI and API calls wait synchronously only up to their configured timeouts; there are deliberately no queues, background workers, or scheduling in this milestone. The current integration assumes the AI-generated collector accepts Bright Data's default `url` input schema. If you later customize its input schema, this endpoint must be updated to submit matching input objects.

## API sequence

With the API running at `http://127.0.0.1:8000`, create a competitor and source. `extraction_description` is required before a custom scraper can be created.

```powershell
curl.exe -X POST http://127.0.0.1:8000/competitors -H "Content-Type: application/json" -d '{"name":"Example Co","website_url":"https://example.com"}'
curl.exe -X POST http://127.0.0.1:8000/competitors/1/sources -H "Content-Type: application/json" -d '{"name":"Example updates","url":"https://example.com/news","extraction_description":"Extract each update title, publication date, summary, and URL."}'
```

Create the custom scraper. A successful response has the Bright Data collector ID:

```powershell
curl.exe -X POST http://127.0.0.1:8000/sources/1/scraper
# {"collector_id":"c_...","status":"done"}
```

Run it. The endpoint waits for Bright Data and persists the returned structured array:

```powershell
curl.exe -X POST http://127.0.0.1:8000/sources/1/collect
curl.exe http://127.0.0.1:8000/sources/1/runs
```

An example successful collection response is:

```json
{
  "id": 1,
  "source_id": 1,
  "status": "succeeded",
  "record_count": 1,
  "health_status": "healthy",
  "bright_data_collection_id": "j_...",
  "raw_result": [{"title": "Example update"}],
  "error_message": null
}
```

`collection_runs` stores the source, lifecycle timestamps, local run status, Bright Data collection ID, unmodified structured result, record count, error detail, and deterministic health status. Health is `healthy` for a successful non-empty array, `degraded` for an empty array or unexpected non-array JSON, and `failed` for an API, authentication, transport, or timeout error.
