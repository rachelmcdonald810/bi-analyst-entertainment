# Live Music Analytics Pipeline — Project Completion Spec

## Overview

Complete all remaining deliverables for the Live Music Analytics Pipeline course project. The pipeline already has working extraction scripts (Ticketmaster API, Spotify via Firecrawl), a dbt star schema in Snowflake (2 staging views, 4 mart tables), and one GitHub Actions workflow. This spec covers finishing the remaining deliverables and polishing the repo for portfolio use.

## Phase 1: Strengthen the Foundation

### 1A. dbt Staging Tests (Deliverable 6, 15 pts)

Add `dbt_project/models/staging/schema.yml` with tests:

**stg_ticketmaster_events:**
- `event_id`: unique, not_null
- `event_name`: not_null
- `event_date`: not_null
- `venue_name`: not_null

**stg_spotify_artists:**
- `artist_name`: unique, not_null
- `monthly_listeners`: not_null

Run `dbt test` to confirm all pass.

### 1B. GitHub Actions for Spotify (Deliverable 8, 5 pts)

New file: `.github/workflows/extract_spotify.yml`
- Trigger: cron `0 7 * * *` (7 AM UTC, 1 hour after Ticketmaster) + `workflow_dispatch`
- Runs on: `ubuntu-latest`, Python 3.12
- Steps: checkout, setup Python, install requirements, run `src/extract_spotify_firecrawl.py`
- Secrets: `FIRECRAWL_API_KEY`, `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_WAREHOUSE`, `SNOWFLAKE_DATABASE`, `SNOWFLAKE_SCHEMA`

User action required: Add `FIRECRAWL_API_KEY` to GitHub repo secrets.

## Phase 2: Build New Deliverables

### 2A. Streamlit Dashboard (Deliverable 7, 15 pts)

**File:** `streamlit_app.py` at repo root

**Connection:** `snowflake-connector-python` using `st.secrets` (for deployment) with `.env` fallback (for local dev).

**Layout — 5 sections:**

1. **Event Overview** — KPI cards (total events, unique artists, unique venues, avg ticket price). Bar chart of events by genre.
2. **Pricing Analytics** (descriptive) — Avg/min/max price by genre bar chart. Price distribution histogram.
3. **Artist Insights** (diagnostic) — Scatter plot: Spotify monthly listeners vs event count per artist. Answers "do streaming-popular artists have more live events?"
4. **Venue & Geography** — Events by state bar chart. Top 10 venues table.
5. **Time Trends** — Events by day of week bar chart. Weekend vs weekday split.

**Interactivity:** Sidebar filters for genre, state, price range.

**Deployment:**
- Streamlit Community Cloud, connected to GitHub repo
- Snowflake credentials in Streamlit Cloud secrets dashboard
- Add `streamlit` to `requirements.txt`
- Add `.streamlit/config.toml` for theme if needed

### 2B. Knowledge Base (Deliverable 11, 8 pts)

**Structure:**
```
knowledge/
  raw/          # 15+ source files (.md or .txt)
  wiki/         # Claude Code-generated wiki pages
    index.md
    overview.md
    key-entities.md
    themes.md
```

**Raw sources (15+ from 3+ sites):** Focus on why combining streaming and live performance data matters for the entertainment industry. Topics:
- Streaming-to-touring pipeline (how streaming popularity drives ticket demand)
- Live music revenue economics (post-pandemic boom, touring as primary artist revenue)
- Data-driven entertainment analytics (dynamic pricing, fan segmentation, booking optimization)
- Industry players: AEG/AXS, Live Nation, Spotify for Artists, Pollstar

Source sites: Billboard, Music Business Worldwide, Pollstar, Rolling Stone, Forbes, Spotify blog, company press releases, earnings transcripts, research reports.

Each raw file: markdown with source URL, title, author, date, and scraped/summarized content.

**Wiki pages:**
- `overview.md` — Industry landscape: why streaming + live data convergence is the key trend
- `key-entities.md` — Major companies, platforms, stakeholders and their roles
- `themes.md` — Key trends: streaming-to-touring pipeline, data-driven booking, dynamic pricing, fan engagement analytics
- `index.md` — Table of contents linking all wiki pages + inventory of raw sources

### 2C. Pipeline Diagram (Deliverable 9, 5 pts)

Mermaid LR flowchart embedded in README. Layers:
- **Sources**: Ticketmaster Discovery API, Spotify (Firecrawl)
- **Raw**: Snowflake RAW schema (raw_ticketmaster_events, raw_spotify_artists)
- **Staging**: dbt views (stg_ticketmaster_events, stg_spotify_artists)
- **Marts**: dbt tables (fact_events, dim_artists, dim_venues, dim_dates)
- **Outputs**: Streamlit Dashboard, Knowledge Base (Claude Code)

Every tool labeled. GitHub Actions shown as the orchestration layer for extraction.

### 2D. ERD (Deliverable 13, 3 pts)

Mermaid ER diagram generated from dbt mart models. Shows:
- `fact_events` (PK: event_key, FKs: artist_key, venue_key, date_key, measures: price_min, price_max, price_avg, sale_status)
- `dim_artists` (PK: artist_key, artist_name, genre, monthly_listeners, spotify_url)
- `dim_venues` (PK: venue_key, venue_name, city, state)
- `dim_dates` (PK: date_key, event_date, day_name, month_name, year, quarter, is_weekend)

Relationships: fact_events }o--|| dim_artists, dim_venues, dim_dates

Embedded in README.

## Phase 3: Polish

### 3A. README (Deliverable 12, 5 pts)

Rewrite using course template. Sections:
- Project Overview
- Tech Stack
- Pipeline Setup (how to clone, install, configure, run)
- Data Sources table
- ERD (Mermaid, inline)
- Pipeline Diagram (Mermaid, inline)
- Insights Summary (key findings from dashboard)
- Knowledge Base description

### 3B. Repo Cleanup (Deliverable 14, 2 pts)

- Remove `dbt_project/.user.yml` from tracking
- Remove `dbt_project/logs/` from tracking
- Remove empty `data/` directory (raw data lives in Snowflake)
- Update `.gitignore` to cover `dbt_project/.user.yml` and `dbt_project/logs/`
- Verify `.env` not committed
- Standardize naming (all lowercase, hyphens)
- Final check: no scratch files, test outputs, credentials, or personal notes

### 3C. Presentation Slide Content (Deliverable 10, 7 pts)

Draft bullet points for slides covering:
- Project overview and motivation
- Descriptive insights from the data
- Diagnostic insights (streaming vs live correlations)
- Recommendations for entertainment analytics teams
- User builds the actual PDF in Google Slides/PowerPoint

## Out of Scope

- Deploying to Streamlit Cloud (user does this manually with their account)
- Adding `FIRECRAWL_API_KEY` to GitHub secrets (user action)
- Final PDF creation for slides
