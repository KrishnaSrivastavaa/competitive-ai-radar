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

## Primary MVP

The MVP must support:

- Adding competitors
- Monitoring at least one public competitor source
- Custom Bright Data Scraper Studio collector
- Structured output
- Snapshot storage
- Change detection
- AI-powered change analysis
- Dashboard showing competitor activity
- Evidence behind insights
- Scraper health detection
- Bright Data self-healing demonstration

## Secondary features

If time permits:

- Multiple competitor sources
- LLMWatch
- Conversational interface
- Historical retrieval/RAG
- Notifications