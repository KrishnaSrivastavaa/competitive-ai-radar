# RivalSignal

> **AI-powered competitive intelligence from live public web data.**

RivalSignal helps businesses monitor competitor websites, collect structured public data, detect meaningful changes, and use AI to turn those changes into evidence-backed competitive insights.

---

## 🌐 Live Demo

**Coming soon**

---

## 🚀 What is RivalSignal?

Competitive research is often repetitive and manual.

Teams have to:

- Visit competitor websites repeatedly
- Track product and pricing changes
- Compare current information with previous data
- Identify what actually changed
- Determine whether a change matters
- Research the implications

**RivalSignal brings this workflow into one platform.**

```text
Competitor
    ↓
Public Website
    ↓
Bright Data Scraper Studio
    ↓
Structured Data
    ↓
Snapshot Storage
    ↓
Deterministic Change Detection
    ↓
Gemini AI Analysis
    ↓
Competitive Insights
    ↓
AI Analyst
```

The goal is not simply to scrape websites.

The goal is to transform continuously collected public data into **useful, explainable, evidence-backed competitive intelligence.**

---

# ✨ Key Features

## 🔎 Custom Competitor Monitoring

Add a competitor and define a public website source to monitor.

RivalSignal creates a custom **Bright Data Scraper Studio** scraper for the selected source and uses it to collect structured information.

---

## 📊 Structured Web Data

Collected data is normalized and stored as structured snapshots.

This allows RivalSignal to maintain a historical representation of what was observed during each collection.

---

## ⚡ Deterministic Change Detection

RivalSignal does **not** ask an LLM whether data changed.

Changes are detected deterministically by comparing snapshots.

Supported states:

- `initial`
- `unchanged`
- `added`
- `removed`
- `modified`

For modified records, nested field-level changes can also be identified.

Record identity prefers stable fields such as:

- `product_page_url`
- `url`
- related URL/ID fields
- canonical JSON as a final fallback

This keeps the core comparison process predictable and reproducible.

---

## 🧠 Gemini-Powered Competitive Analysis

Once a meaningful change is detected, Gemini can analyze the verified change and produce a structured insight.

The AI is given:

- Competitor information
- Source information
- Deterministic change information
- Relevant collected snapshots

The AI is **not given external browsing or web-search capabilities**.

This keeps the analysis grounded in the data collected by RivalSignal.

---

## 💬 AI Analyst

Every competitor has an AI Analyst where users can ask questions about the competitor's collected data.

Example questions:

```text
What products are currently available?

What are their current prices?

What changed recently?

Which products have discounts?

Summarize their current offering.

What are the major changes in their latest data?
```

The Analyst uses stored competitor data rather than triggering a new scrape.

For historical questions, relevant deterministic change records can also be included as context.

---

## 🛡️ Evidence-Backed Answers

RivalSignal is designed to minimize unsupported AI claims.

The AI Analyst:

- Uses stored database context
- Does not browse the internet
- Does not perform external web searches
- Validates structured responses
- Validates returned evidence URLs against stored source URLs
- Rejects invented evidence URLs
- Does not modify collected data while answering questions

---

## 🧹 Bright Data Resource Cleanup

Deleting a competitor also cleans up its associated local data and attempts to delete the corresponding Bright Data Scraper Studio scraper.

This prevents abandoned test/development scrapers from accumulating in the Bright Data account.

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │      React UI        │
                         │  Vite + TypeScript   │
                         └──────────┬───────────┘
                                    │
                                  REST
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │       Backend        │
                         └──────────┬───────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
       ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
       │   Bright Data  │  │     SQLite     │  │     Gemini     │
       │ Scraper Studio │  │    Database    │  │      API       │
       └───────┬────────┘  └────────────────┘  └────────────────┘
               │
               ▼
       Public Competitor
           Websites
```

---

# 🔄 Core Workflow

### 1. Add Competitor

The user provides competitor information and a public source.

### 2. Create Custom Scraper

RivalSignal uses Bright Data Scraper Studio to create a custom scraper for the source.

### 3. Collect Data

The scraper is triggered through the Bright Data Collection API.

### 4. Store Snapshot

The returned structured data is normalized and persisted as a snapshot.

### 5. Detect Changes

The new snapshot is deterministically compared against the previous snapshot.

### 6. Analyze Changes

Meaningful changes can be passed to Gemini for structured competitive analysis.

### 7. Ask Questions

Users can use the AI Analyst to ask questions about the stored competitor data.

---

# 🧰 Tech Stack

## Frontend

- React
- TypeScript
- Vite
- CSS
- pnpm

## Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- uv

## AI

- Google Gemini
- Official `google-genai` SDK
- Pydantic structured output validation

## Web Data

- Bright Data Scraper Studio
- Bright Data Collection API
- Bright Data CLI

## Deployment

- Vercel — Frontend
- Railway — Backend
- Railway Volume — Persistent SQLite storage

---

# 📁 Project Structure

```text
competitive-ai-radar/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   │
│   ├── tests/
│   ├── pyproject.toml
│   └── uv.lock
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── pages/
│   │
│   ├── package.json
│   └── pnpm-lock.yaml
│
└── README.md
```

---

# 🔌 API Highlights

## Competitors

```http
POST   /competitors
GET    /competitors
GET    /competitors/{competitor_id}
DELETE /competitors/{competitor_id}
```

## Sources & Collection

```http
GET  /competitors/{competitor_id}/sources
POST /competitors/{competitor_id}/sources
POST /sources/{source_id}/scraper
POST /sources/{source_id}/collect
```

## Snapshots & Changes

```http
GET /sources/{id}/snapshots
GET /sources/{id}/changes
GET /changes/{id}
```

## AI Analysis

```http
POST /changes/{change_id}/analyze
GET  /insights/{insight_id}
GET  /competitors/{competitor_id}/insights
```

## AI Analyst

```http
POST /competitors/{competitor_id}/ask
```

---

# 🧪 Testing

The backend contains automated tests covering:

- Competitor and source APIs
- Collection behavior
- Snapshot persistence
- Deterministic change detection
- Added / removed / modified changes
- Gemini analysis
- Invalid structured AI responses
- Provider failures and timeouts
- Grounded AI Analyst behavior
- Evidence URL validation
- Missing data and error handling
- Competitor deletion

Current verification:

```text
37 tests passed
```

Frontend production build:

```bash
cd frontend
pnpm run build
```

---

# 💻 Local Development

## Prerequisites

Install:

- Python
- uv
- Node.js
- pnpm

You will also need:

- Bright Data API credentials
- Gemini API credentials

---

## 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd competitive-ai-radar
```

---

## 2. Configure Backend

```bash
cd backend
```

Create the environment file.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

Configure:

```env
BRIGHT_DATA_API_KEY=your_bright_data_api_key
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

Install dependencies:

```bash
uv sync
```

Start the backend:

```bash
uv run uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

---

## 3. Configure Frontend

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
pnpm install
```

Start the development server:

```bash
pnpm dev
```

Frontend:

```text
http://127.0.0.1:5173
```

If the backend runs on a different origin, configure:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

and configure the backend CORS settings accordingly.

---

# 🔐 Environment Variables

### Backend

```env
BRIGHT_DATA_API_KEY=
GEMINI_API_KEY=
GEMINI_MODEL=
DATABASE_URL=
CORS_ORIGINS=
```

### Frontend

```env
VITE_API_BASE_URL=
```

**Never commit real API keys or secrets to the repository.**

---

# 🧠 Design Philosophy

## Deterministic First, AI Second

RivalSignal separates **data verification** from **AI interpretation**.

Instead of asking an LLM:

> "Did something change?"

the system deterministically compares snapshots first.

Only after a verified change exists does AI answer:

> "What could this change mean?"

This makes the AI layer easier to validate and keeps the core comparison logic predictable.

---

## Evidence Over Speculation

Gemini receives collected competitor data rather than unrestricted web access.

The system is designed around:

```text
Collected Data
      ↓
Verified Change
      ↓
AI Interpretation
      ↓
Evidence-backed Insight
```

rather than:

```text
Question
   ↓
LLM guesses/searches the web
   ↓
Unverified answer
```

---

## Simple MVP Architecture

The project intentionally avoids unnecessary infrastructure.

The MVP does not require:

- Redis
- Kafka
- Celery
- Kubernetes
- Separate worker services
- Vector databases
- Authentication
- RAG pipelines

The focus is on building a reliable end-to-end competitive intelligence workflow first.

---

# 🎯 Current MVP Scope

## Included

- Competitor management
- Public source monitoring
- Custom Bright Data Scraper Studio collectors
- Collection run tracking
- Scraper health classification
- Snapshot persistence
- Deterministic change detection
- Gemini-powered analysis
- Evidence-backed insights
- Grounded AI Analyst
- Competitor deletion
- Bright Data scraper cleanup
- React dashboard
- Competitor workspace

## Intentionally Out of Scope

- User authentication
- Multi-user workspace isolation
- Persistent chat history
- RAG / embeddings
- Background scheduling
- Notifications
- Multiple-source creation through the current UI workflow
- Autonomous external web research

These can be added as future extensions rather than complicating the hackathon MVP.

---

# 🚀 Future Improvements

Potential future improvements include:

- Multiple monitored sources per competitor
- User authentication and workspace isolation
- Persistent conversational history
- Semantic retrieval / RAG for larger datasets
- Scheduled collections
- Alerts and notifications
- Advanced competitor comparison
- Improved handling of pagination and interactive web pages
- More historical analytics
- Automated monitoring schedules

---

# ⚠️ Data Collection & Responsible Use

RivalSignal is designed to collect **publicly available web data only**.

Do not use the platform to collect:

- Login-protected data
- Private data
- Paywalled or restricted content
- Personal information that should not be collected

Users are responsible for ensuring that the sources they monitor and their use of collected data comply with applicable website terms, laws, and policies.

---

# 🏆 Hackathon Summary

RivalSignal combines:

**Bright Data + deterministic data engineering + Gemini + conversational AI**

to create a competitive intelligence workflow that goes beyond basic web scraping.

The system can:

```text
Monitor competitors
       ↓
Collect public web data
       ↓
Store historical snapshots
       ↓
Detect verified changes
       ↓
Interpret changes with AI
       ↓
Answer competitor questions
       ↓
Provide evidence-backed intelligence
```

### The core idea

> **Don't just scrape what competitors are doing. Understand what changed, why it matters, and let users ask questions about the evidence.**

---

## License

This project was created as a hackathon project.
