# Live Music Analytics Pipeline

An end-to-end data pipeline that combines ticketing and streaming data to generate business intelligence insights for the live entertainment industry. Built to mirror the analytical workflows of a Sr. BI Analyst at AXS (AEG Worldwide).

## Data Pipeline Diagram

```
+---------------------+       +------------------------+
|  Ticketmaster API   |       |  Spotify Artist Pages  |
|  (Discovery v2)     |       |  (via Firecrawl)       |
+--------+------------+       +-----------+------------+
         |                                |
         | Python extraction              | Python + Firecrawl SDK
         | (scheduled daily via           | (manual / on-demand)
         |  GitHub Actions)               |
         |                                |
         v                                v
+-----------------------------------------------------+
|              Snowflake  -  RAW Schema                |
|  +-------------------------+  +--------------------+ |
|  | RAW_TICKETMASTER_EVENTS |  | RAW_SPOTIFY_ARTISTS| |
|  | 200 events per run      |  | 15 artists         | |
|  +-------------------------+  +--------------------+ |
+------------------------+----------------------------+
                         |
                         | dbt (staging + marts)
                         v
+-----------------------------------------------------+
|           Snowflake  -  STAGING Schema               |
|  +-------------------------+  +--------------------+ |
|  | stg_ticketmaster_events |  | stg_spotify_artists| |
|  +-------------------------+  +--------------------+ |
+------------------------+----------------------------+
                         |
                         | dbt (star schema)
                         v
+-----------------------------------------------------+
|            Snowflake  -  MARTS Schema                |
|                                                     |
|  +-------------+  +------------+  +-----------+     |
|  | dim_artists  |  | dim_venues |  | dim_dates |     |
|  | (+ Spotify)  |  |            |  |           |     |
|  +------+------+  +-----+------+  +-----+-----+     |
|         |                |               |           |
|         +-------+--------+-------+-------+           |
|                 |                                    |
|          +------+------+                             |
|          | fact_events  |                             |
|          +-------------+                             |
+-----------------------------------------------------+
```

## Project Structure

```
bi-analyst-entertainment/
+-- src/
|   +-- extract_ticketmaster.py    # Source 1: Ticketmaster API -> Snowflake
|   +-- extract_spotify_firecrawl.py  # Source 2: Spotify via Firecrawl -> Snowflake
+-- dbt_project/
|   +-- models/
|   |   +-- staging/               # Cleaned views of raw data
|   |   +-- marts/                 # Star schema (fact + dimensions)
|   +-- dbt_project.yml
|   +-- profiles.yml
|   +-- packages.yml
+-- .github/workflows/
|   +-- extract_ticketmaster.yml   # Daily scheduled extraction
+-- data/                          # Local data files
+-- docs/                          # Proposal + job posting
+-- requirements.txt
+-- .env.example                   # Template for credentials
```

## Setup

1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your credentials
4. Run extractions:
   - `python src/extract_ticketmaster.py`
   - `python src/extract_spotify_firecrawl.py`
5. Run dbt models:
   - `cd dbt_project && dbt deps && dbt run`

## Data Sources

| Source | Type | Data | Script |
|--------|------|------|--------|
| Ticketmaster Discovery API | REST API | Live music events, venues, pricing | `src/extract_ticketmaster.py` |
| Spotify artist pages | Web scrape (Firecrawl) | Artist popularity, monthly listeners | `src/extract_spotify_firecrawl.py` |

## Star Schema

- **fact_events** - One row per event with pricing, sale status, and foreign keys
- **dim_artists** - Artist details joined with Spotify streaming metrics
- **dim_venues** - Venue name, city, and state
- **dim_dates** - Date attributes (day of week, month, quarter, weekend flag)
