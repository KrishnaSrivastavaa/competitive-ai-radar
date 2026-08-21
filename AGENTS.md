# Competitive AI Radar — Codex Instructions

## Read First

Before making any changes:

1. Read `PROJECT_SPEC.md` completely.
2. Inspect the existing repository and backend implementation.
3. Check `git status`.
4. Run the existing test suite.
5. Understand the existing architecture before modifying it.

`PROJECT_SPEC.md` contains the detailed project requirements, architecture,
current implementation, and roadmap.

---

## Repository Structure

All current application logic lives inside `backend/`.

```text
competitive-ai-radar/
├── AGENTS.md
├── PROJECT_SPEC.md
└── backend/
    ├── app/
    │   ├── api/
    │   ├── core/
    │   ├── models/
    │   ├── schemas/
    │   └── services/
    ├── tests/
    ├── pyproject.toml
    └── uv.lock


Do NOT create separate root-level ai/, scrappers/, or backend Git
repositories.

Bright Data, snapshot, normalization, change detection, and AI logic
belongs inside backend/app/.

Development Rules
Use uv for Python dependency management.
Reuse the existing architecture and patterns.
Do not rewrite working code unnecessarily.
Every new feature must have tests.
Never remove or weaken tests just to make them pass.
Tests must not make real external API calls.
Use dependency injection/mocks for Bright Data and Gemini.
Run the complete test suite after every milestone.

Run:

cd backend
uv run pytest

The existing test suite must remain green.

Architecture Rules
Bright Data

Bright Data Scraper Studio is a core part of the project.

Do not replace Bright Data with another scraping framework unless explicitly
requested.

Change Detection

Change detection is deterministic Python logic.

Do NOT use Gemini to determine whether a change occurred.

The system determines:

added records
removed records
modified records
changed fields

Gemini interprets an already-detected change.

AI

Gemini must only interpret verified scraped data and detected changes.

Gemini must not invent facts, prices, products, dates, URLs, statistics, or
other information that is not supported by the supplied evidence.

Simplicity

Do not introduce unnecessary:

microservices
Redis
Celery
queues
vector databases
RAG
chatbot infrastructure
authentication
notifications
scheduling

unless explicitly requested.

Security

Never commit:

.env
API keys
credentials
secrets
local .db files

Use .env.example for placeholders.

Never expose secrets in logs, API responses, screenshots, or documentation.

Current Task

The current milestone is:

Gemini AI Analysis

Implement:

Detected Change
      ↓
Gemini
      ↓
Validated Structured Insight
      ↓
Database
      ↓
API

Use the official google-genai Python SDK.

Gemini-specific service code belongs in:

backend/app/services/llm_analysis.py

Do not implement RAG, chatbot, frontend, or scraper self-healing during
this milestone.

Before Starting Any Task

Read:

AGENTS.md
PROJECT_SPEC.md
Existing implementation
Existing tests

Then run:

cd backend
uv run pytest

Only then begin implementation.

After implementation:

Run the full test suite.
Verify existing functionality still works.
Report files changed.
Report test results.
Report any assumptions or limitations.

