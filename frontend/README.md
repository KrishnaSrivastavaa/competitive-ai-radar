# Competitive AI Radar frontend

React, Vite, and TypeScript frontend for the FastAPI backend.

## Run locally

Start the API from `backend/` first:

```powershell
uv run uvicorn app.main:app --reload
```

Then configure and run the frontend from this directory:

```powershell
Copy-Item .env.example .env
pnpm install
pnpm dev
```

`VITE_API_BASE_URL` defaults to `http://localhost:8000`. The backend accepts the
Vite development origins by default; customize `CORS_ORIGINS` in `backend/.env`
if you serve the frontend from a different origin.

Build the production bundle with `pnpm run build`.
