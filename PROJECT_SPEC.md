# Competitive AI Radar

## Goal

Build an AI-powered competitive intelligence platform that continuously
monitors public competitor websites and selected public AI/model signals.

The system should:

1. Collect public competitor data using custom Bright Data Scraper Studio
   scrapers.
2. Store structured snapshots of competitor information.
3. Detect meaningful changes between snapshots.
4. Use an LLM to analyze the significance of changes.
5. Monitor selected AI-related queries/signals and analyze competitor
   visibility/perception.
6. Combine competitor activity and AI visibility signals into strategic,
   evidence-backed insights.
7. Detect scraper degradation and use Bright Data's self-healing capability
   to recover broken extraction.
8. Provide a dashboard and conversational interface for users to explore
   current and historical competitive intelligence.

## Important constraints

- Bright Data Scraper Studio must be central to the web-data collection.
- Use custom Scraper Studio scrapers, not only existing Bright Data library
  scrapers.
- Only publicly available web data may be collected.
- Do not scrape login-protected, private, paywalled, or restricted data.
- AI coding assistants may be used, but all generated code must be reviewed,
  tested, and understood.
- Keep the MVP simple and reliable.
- Do not add unnecessary infrastructure.
- RAG is optional and should only be introduced if it provides clear value
  after the core system works.

## Core workflow

User
→ defines company and competitors
→ selects public sources to monitor
→ custom Bright Data scraper collects data
→ data is normalized and stored
→ snapshots are compared
→ meaningful changes are detected
→ AI analyzes changes
→ LLM signals are collected/analyzed
→ signals are combined
→ strategic insights are generated
→ user views insights or asks questions

## Current MVP

The MVP currently focuses on this end-to-end workflow:

User
→ Competitor
→ Public Source
→ Dynamic Bright Data Scraper Studio collector
→ Structured collection
→ Snapshot
→ Deterministic change detection
→ Gemini analysis
→ Evidence-backed insight
→ Dashboard

The initial MVP does NOT require:

- RAG
- conversational interface
- AI/model visibility signals
- notifications
- complex scheduling
- queues
- vector databases

## Future Features

After the core workflow is reliable, consider:

- Scraper self-healing
- Multiple source types
- AI/model visibility signals
- Conversational interface
- Historical retrieval/RAG
- Notifications




# 2. `PROJECT_SPEC.md` → Put the PROJECT INFORMATION here

This is your **complete project context**.

Put the following in your existing `PROJECT_SPEC.md`:

```markdown
# Competitive AI Radar — Project Specification

## 1. Project Overview

Competitive AI Radar is a hackathon project for the Into the Scrape-Verse
hackathon.

The project uses Bright Data Scraper Studio as the core web-data collection
infrastructure and combines it with deterministic snapshot/change detection
and AI-powered competitive intelligence.

### Core idea

A user adds a competitor and one or more public web sources to monitor.

The system:

1. Creates a Bright Data Scraper Studio custom scraper dynamically from a URL
   and extraction description.
2. Runs the Bright Data collector.
3. Stores the collected data as a snapshot.
4. Compares the latest snapshot with the previous snapshot.
5. Detects meaningful changes deterministically.
6. Sends the verified change to Google Gemini.
7. Gemini interprets the change and produces a structured competitive insight.
8. A future frontend displays competitors, sources, changes, insights,
   evidence, and scraper health.
9. A future milestone demonstrates scraper self-healing.

---

# 2. Product Direction

## Competitive Intelligence / Competitor Monitoring

Users can monitor public competitor sources such as:

- product pages
- pricing pages
- product catalogs
- public announcements
- changelogs
- release notes
- public company information

The core product promise is:

> Bright Data collects the web data → our system verifies what changed →
> Gemini explains why it matters.

The MVP should focus on one strong end-to-end workflow rather than many
unrelated features.

---

# 3. Current Architecture

```text
User
  ↓
FastAPI
  ↓
Competitor
  ↓
Source
  ↓
Bright Data Scraper Studio
  ↓
Bright Data Collection API
  ↓
CollectionRun
  ↓
Snapshot
  ↓
Deterministic Change Detection
  ↓
Gemini AI Analysis
  ↓
Insight
  ↓
Future Frontend Dashboard


All current backend functionality lives inside backend/.

There are no separate root-level ai/ or scrappers/ applications.

4. Repository Structure
competitive-ai-radar/
│
├── AGENTS.md
├── PROJECT_SPEC.md
│
└── backend/
    ├── app/
    │   ├── api/
    │   ├── core/
    │   ├── models/
    │   ├── schemas/
    │   └── services/
    │
    ├── tests/
    ├── pyproject.toml
    ├── uv.lock
    ├── README.md
    ├── .env.example
    └── .gitignore

Current backend services include:

backend/app/services/
├── brightdata.py
├── normalization.py
└── change_detection.py

The future Gemini service will be:

backend/app/services/llm_analysis.py
5. Technology Stack
Backend
Python
FastAPI
Pydantic
SQLAlchemy
SQLite
uv
Web Collection
Bright Data Scraper Studio
Bright Data AI Flow API
Bright Data Collection API
AI
Google Gemini API
google-genai
Pydantic structured output
Frontend

Planned later:

React
Vite
TypeScript
6. Competitors and Sources

A Competitor represents the company/entity being monitored.

A Source represents a specific public URL/source belonging to a competitor.

Example:

Competitor:
Acme


Sources:
- Pricing page
- Product page
- News page
- Changelog

A Source contains:

name
URL
extraction description
Bright Data collector ID
active status
7. Extraction Description

The Source contains an extraction_description.

This is the natural-language instruction used when creating the Bright Data
scraper.

Example:

Extract each product's title, price, availability, product URL, and
description.

The extraction description tells Bright Data what structured data to extract.

8. Bright Data Scraper Creation

Implemented in:

backend/app/services/brightdata.py

Endpoint:

POST /sources/{source_id}/scraper

Workflow:

Fetch Source.
Read source URL.
Read extraction description.
Create Bright Data collector template.
Start Bright Data AI Flow.
Poll until AI Flow is complete.
Receive collector ID.
Store collector ID on Source.

Example collector ID:

c_mt1sqeby1n3ul9t0x3

The collector should be reused for subsequent collection runs.

9. Bright Data Collection

Endpoint:

POST /sources/{source_id}/collect

Workflow:

Fetch Source.
Read stored collector ID.
Trigger Bright Data collector.
Wait for collection.
Retrieve structured JSON.
Persist CollectionRun.
Store raw result.
Calculate health.

Collection statuses:

running
succeeded
failed

Health statuses:

healthy
degraded
failed
10. CollectionRun

A CollectionRun represents one collection attempt.

It stores:

source ID
status
start time
finish time
Bright Data collection ID
raw structured result
record count
error message
health status
11. Snapshots

A Snapshot represents the normalized state of a source at a particular time.

Example:

Snapshot 1
T1
data = [...]


Snapshot 2
T2
data = [...]

The system compares snapshots to detect changes.

12. Normalization

Implemented in:

backend/app/services/normalization.py

Normalization makes scraped data deterministic before hashing and comparison.

The purpose is to avoid false changes caused by irrelevant formatting
differences.

Normalization does not use an LLM.

13. Change Detection

Implemented in:

backend/app/services/change_detection.py

Main function:

detect_changes(
    previous_data,
    current_data,
    previous_hash,
    current_hash,
)

Possible change types:

initial
unchanged
added
removed
modified

Identity fields currently include:

product_page_url
url
product_url
id
product_id
sku

If no identity field is available, canonical JSON is used.

Modified records include:

record key
before
after
changed fields

Nested fields are supported.

14. Change Detection Example

Previous:

{
  "product_page_url": "https://example.com/product/1",
  "title": "Pro Plan",
  "price": {
    "value": 29.99,
    "currency": "USD"
  }
}

Current:

{
  "product_page_url": "https://example.com/product/1",
  "title": "Pro Plan",
  "price": {
    "value": 39.99,
    "currency": "USD"
  }
}

Detected:

change_type = modified


changed_fields = [
    "price.value"
]

This verified change is passed to Gemini.

15. Current API Endpoints

Important existing endpoints:

GET /health


POST /competitors
GET /competitors
GET /competitors/{id}


POST /competitors/{id}/sources
GET /sources/{id}


POST /sources/{id}/scraper
POST /sources/{id}/collect
GET /sources/{id}/runs

Snapshot/change endpoints also exist.

Codex must inspect the actual code before assuming exact request/response
schemas.

16. Environment Variables

Existing:

APP_NAME
DATABASE_URL


BRIGHT_DATA_API_KEY
BRIGHT_DATA_API_BASE_URL
BRIGHT_DATA_DELIVERY_JSON
BRIGHT_DATA_TIMEOUT_SECONDS
BRIGHT_DATA_POLL_INTERVAL_SECONDS
BRIGHT_DATA_POLL_TIMEOUT_SECONDS

Future Gemini configuration:

GEMINI_API_KEY
GEMINI_MODEL

Never commit:

.env
*.db

Commit:

.env.example

with placeholders only.

17. Current Test Status

Current full backend test suite:

29 passed

Test files:

backend/tests/test_api.py
backend/tests/test_brightdata_api.py
backend/tests/test_brightdata_client.py
backend/tests/test_change_detection.py

The change detection suite contains 11 tests.

Run:

cd backend
uv run pytest

There is one unrelated Starlette/httpx deprecation warning.

18. Completed Milestones
 FastAPI foundation
 SQLite + SQLAlchemy
 Competitor API
 Source API
 Bright Data dynamic scraper creation
 Bright Data collection
 CollectionRun tracking
 Snapshot persistence
 Normalization
 Deterministic change detection
 Change detection tests
 29 passing tests
19. Current Milestone — Gemini AI Analysis
Goal

Turn verified changes into useful competitive intelligence.

Pipeline:

Detected Change
      ↓
Gemini
      ↓
Structured Insight
      ↓
Database
      ↓
API

Use:

Google Gemini API
google-genai

Do not use OpenAI for this milestone.

20. Gemini Service

Create:

backend/app/services/llm_analysis.py

The service should receive:

competitor information
source information
change type
change summary
diff data
relevant previous/current data
source URL

The FastAPI route should not directly contain Gemini SDK logic.

Use dependency injection so the Gemini service can be mocked in tests.

21. Insight Model

Create:

backend/app/models/insight.py

Expected fields:

id
competitor_id
change_id
title
analysis
competitive_impact
recommendation
confidence
evidence
created_at

Add corresponding schemas.

22. Gemini Structured Output

Expected structure:

{
  "title": "...",
  "analysis": "...",
  "competitive_impact": "...",
  "recommendation": "...",
  "confidence": 0.0,
  "evidence": [
    {
      "source_url": "...",
      "reason": "..."
    }
  ]
}

Validate with Pydantic.

Confidence must be:

0 <= confidence <= 1

Invalid output must not be persisted.

23. Gemini Responsibilities

Gemini should explain:

What changed?
Why might it matter?
What could the competitive impact be?
What should the user consider doing?
How confident is the analysis?
What evidence supports it?

Gemini must distinguish observed facts from interpretation.

Gemini must not invent:

prices
products
dates
URLs
statistics
competitor actions
customer behavior
features
market information

If evidence is insufficient, Gemini should say so.

No web browsing or Google Search grounding is required for this milestone.

The scraped data and detected change are the source of truth.

24. Gemini API Endpoints

Add:

POST /changes/{change_id}/analyze

Workflow:

Fetch Change
    ↓
Fetch Source
    ↓
Fetch Competitor
    ↓
Fetch relevant Snapshots
    ↓
Build analysis payload
    ↓
Gemini
    ↓
Validate output
    ↓
Create Insight
    ↓
Persist Insight
    ↓
Return Insight

Reject:

unchanged
initial

Only analyze:

added
removed
modified

Also add:

GET /insights/{insight_id}
GET /competitors/{competitor_id}/insights
25. Gemini Error Handling

If Gemini fails:

return an appropriate API error
do not create Insight
preserve the Change
preserve existing CollectionRun/Snapshot data

If structured output validation fails:

do not create Insight
return a clear error

If Gemini times out:

do not create Insight
26. Gemini Tests

Do NOT make real Gemini API calls in tests.

Use mocks/fakes/dependency injection.

Test:

Modified change creates insight.
Added change creates insight.
Removed change creates insight.
Unchanged change is rejected.
Initial change is rejected.
Valid structured response is accepted.
Invalid LLM response is rejected.
Gemini failure does not create insight.
Gemini timeout does not create insight.
Evidence is persisted.
Confidence below 0 is rejected.
Confidence above 1 is rejected.
Correct competitor/change relationship is persisted.
Existing 29 tests continue passing.
27. What Is NOT Part of Gemini Milestone

Do not implement:

RAG
vector database
chatbot
frontend
scraper self-healing
queues
Redis
Celery
scheduling
notifications
authentication
microservices

Keep this milestone focused.

28. Future Milestone — Scraper Self-Healing

After Gemini works:

Collection
    ↓
Data Validation
    ↓
Missing/unexpected fields
    ↓
Degraded scraper
    ↓
Bright Data self-healing
    ↓
Re-run
    ↓
Verify recovered data

Possible validation failures:

missing required fields
zero records
unexpected schema
significant record-count drop

Do not claim healing succeeded unless Bright Data actually confirms recovery.

29. Future Milestone — Frontend

After the backend is stable:

Use:

React
Vite
TypeScript

Dashboard should show:

competitors
sources
scraper health
collection runs
recent changes
AI insights
evidence
30. Final Demo Flow

The intended final demo:

Add competitor
      ↓
Add public source
      ↓
Enter extraction description
      ↓
Create Bright Data scraper
      ↓
Run collection
      ↓
Show structured data
      ↓
Store snapshot
      ↓
Run collection again
      ↓
Detect change
      ↓
Show exact changed field
      ↓
Send change to Gemini
      ↓
Show competitive insight
      ↓
Show evidence
      ↓
Demonstrate scraper degradation
      ↓
Demonstrate self-healing
      ↓
Show recovered data
      ↓
Show dashboard

Core narrative:

Bright Data collects it → our system verifies what changed → Gemini explains
why it matters → the system can recover when scraping breaks.

31. Roadmap
[x] Backend foundation
[x] Competitors
[x] Sources
[x] Bright Data scraper creation
[x] Bright Data collection
[x] CollectionRun
[x] Snapshots
[x] Normalization
[x] Change detection
[x] 29 tests


[ ] Gemini AI analysis
[ ] Insight APIs
[ ] Gemini tests


[ ] Scraper health improvements
[ ] Self-healing


[ ] React dashboard
[ ] End-to-end integration
[ ] Final README
[ ] Demo video
[ ] Hackathon submission


## So, final answer: what goes where?


| File | What goes inside |
|---|---|
| **`AGENTS.md`** | **Instructions to Codex** — rules, coding practices, architecture boundaries, current task, testing rules |
| **`PROJECT_SPEC.md`** | **Everything about the project** — idea, architecture, Bright Data flow, database, APIs, completed work, Gemini requirements, roadmap, demo flow |
| **Actual code** | The implementation — Codex must inspect this rather than trusting documentation blindly |


### Your final root should look like:


```text
competitive-ai-radar/
│
├── AGENTS.md          ← paste the SHORT file above
├── PROJECT_SPEC.md    ← paste the DETAILED file above
│
└── backend/
    ├── app/
    ├── tests/
    ├── pyproject.toml
    ├── uv.lock
    ├── README.md
    ├── .env.example
    └── .gitignore