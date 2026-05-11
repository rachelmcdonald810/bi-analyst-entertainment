# What I'm Prepared to Defend in the Final Interview

## Business Problem & Stakeholder

* Business framing — built as a hypothetical analytics platform for AXS / AEG Worldwide inspired by a Sr. BI Analyst role focused on SQL-driven live entertainment insights
* Stakeholder — hypothetical AXS business intelligence team responsible for pricing strategy, artist demand analysis, venue performance, market opportunity identification, and touring insights
* Core business problem — live entertainment demand signals are fragmented across ticketing systems, streaming platforms, secondary-market ecosystems, and public tour reporting sources
* Pipeline objective — centralize Ticketmaster, Spotify, SeatGeek, and verified tour revenue signals into one analytics platform for live entertainment decision-making

---

# Extraction Layer

## Ticketmaster API extraction

* File: `src/extract_ticketmaster.py`
* Purpose — extracts structured live event supply data from the Ticketmaster Discovery API into Snowflake RAW tables
* Key fields extracted — event_id, artist_name, venue_name, event_date, event_time, ticket pricing, city/state, genre, sale_status
* API request pattern — Python `requests.get()` with parameter dictionary containing API key, `classificationName="Music"`, `countryCode="US"`, sorting, and size controls
* Nested JSON traversal — parsed `_embedded.events`, `_embedded.venues`, `_embedded.attractions`, `dates.start`, and `priceRanges`
* Flattening logic — transformed nested API JSON into one relational tuple per live event
* Why this approach — APIs provide structured JSON that is more reliable than scraping
* Realistic failure mode — missing nested fields, invalid API responses, rate limits, or empty `_embedded.events`
* Improvement ideas — pagination, retries, incremental loading, better error logging
* Downstream flow — `RAW_TICKETMASTER_EVENTS` → `stg_ticketmaster_events` → `fact_events`, `dim_artists`, `dim_venues`, `dim_dates`

## Spotify / Firecrawl extraction

* File: `src/extract_spotify_firecrawl.py`
* Purpose — extracts Spotify monthly listener data as a streaming-demand signal
* Firecrawl explanation — web scraping API that converts web pages into structured markdown instead of raw HTML
* Why Firecrawl — Spotify monthly listeners are visible publicly but not easily accessible through the standard Spotify API
* Extraction flow — Spotify artist URLs → `scrape_url(..., formats=["markdown"])` → markdown text → regex extraction → Snowflake rows
* Regex logic — searches for patterns like `85,000,000 monthly listeners`, removes commas, converts to integer
* Key fields extracted — artist_name, spotify_url, monthly_listeners, metadata, raw_markdown, loaded_at
* Why it matters — monthly listeners became a leading indicator of artist demand
* Realistic failure mode — Spotify page structure changes could break regex extraction
* Improvement ideas — dynamic URL generation, validation checks, retry logic, stronger entity resolution
* Downstream flow — `RAW_SPOTIFY_ARTISTS` → `stg_spotify_artists` → `dim_artists` → pricing and artist analytics

## SeatGeek enrichment extraction

* File: `src/extract_seatgeek.py`
* Purpose — enriches artists with ticket-market demand signals
* Key fields — sg_performer_id, sg_score, sg_popularity, sg_upcoming_events, sg_genres
* Extraction pattern — artist name search → SeatGeek API request → nested performer parsing → flatten performer metrics
* Why SeatGeek mattered — Spotify reflects digital listening behavior while SeatGeek reflects ticket-market popularity and touring momentum
* Why this belongs in `dim_artists` — metrics describe performers rather than individual events
* Realistic failure mode — incorrect artist matching or incomplete performer metadata
* Improvement ideas — fuzzy matching, external artist identifiers, confidence scoring
* Downstream flow — SeatGeek enrichment → `dim_artists`

## Verified tour revenue extraction

* File: `src/extract_verified_tour_revenue.py`
* Purpose — adds benchmark commercial outcome data from public reporting sources
* Table — `stg_tour_revenue`
* Key fields — gross_revenue, tickets_sold, avg_ticket_price, shows, tour_year
* Why it matters — validates whether demand signals translate into real touring performance
* Why not part of the star schema — grain mismatch (`fact_events` = one row per event, tour revenue = one row per tour)
* Why direct-to-dashboard — benchmark analytical layer rather than operational event layer
* Realistic failure mode — inconsistent public source formatting or incomplete reporting coverage
* Improvement ideas — automated ingestion pipelines, stronger validation, structured third-party providers
* Downstream flow — `stg_tour_revenue` → Streamlit benchmark and revenue analysis

---

# Loading Layer (Python → Snowflake)

## Snowflake raw loading

* Files: `src/extract_ticketmaster.py`, `src/extract_spotify_firecrawl.py`
* Purpose — loads parsed Python tuples into Snowflake RAW tables
* Snowflake connection — `snowflake.connector.connect(...)` using environment variables and GitHub secrets
* Why environment variables — prevents credentials from being hardcoded into source code
* RAW schema strategy — preserve untouched source-level data before transformation
* Table creation pattern — `CREATE DATABASE IF NOT EXISTS`, `CREATE SCHEMA IF NOT EXISTS`, `CREATE TABLE IF NOT EXISTS`
* Insert strategy — `executemany()` batches parsed tuples into Snowflake rows
* Why not load directly into marts — marts require deduplication, joins, surrogate keys, and business logic handled in dbt
* Importance of `loaded_at` — enables freshness tracking and downstream deduplication
* Realistic failure mode — schema mismatch, credential failure, warehouse suspension, invalid source data types
* Improvement ideas — audit tables, merge/upsert logic, stronger monitoring and alerts
* Downstream flow — RAW Snowflake tables → dbt staging models

---

# Transformation Layer (dbt + Snowflake)

## dbt architecture

* Folder: `dbt_project/models/`
* Purpose — transform raw Snowflake data into analytics-ready dimensional models
* Why dbt — modular SQL transformations, dependency management, testing, lineage, and reusable business logic
* Core architecture philosophy — Python handles extraction/loading while dbt handles cleaning and modeling
* Transformation flow:

```text
RAW TABLES
↓
STAGING MODELS (views)
↓
MARTS MODELS (tables)
↓
STREAMLIT DASHBOARD
```

## Staging layer

* Files:

  * `models/staging/stg_ticketmaster_events.sql`
  * `models/staging/stg_spotify_artists.sql`
  * `models/staging/schema.yml`
* Purpose — clean and standardize source-level raw data
* Transformations performed:

  * trim whitespace
  * standardize casing
  * cast prices/dates/listeners
  * rename columns
  * validate fields with dbt tests
* Why staging models are views — lightweight transformations that avoid unnecessary storage duplication
* Why `ref()` matters — creates dependency graph and model lineage
* Realistic failure mode — bad source values causing failed casts or broken joins
* Improvement ideas — freshness tests, accepted value tests, stronger validation logic
* Downstream flow — staging models feed marts models

## Mart layer / star schema

* Files:

  * `models/marts/fact_events.sql`
  * `models/marts/dim_artists.sql`
  * `models/marts/dim_venues.sql`
  * `models/marts/dim_dates.sql`
  * `models/marts/schema.yml`
* Purpose — build business-ready dimensional models for analytics
* Star schema structure:

```text
fact_events
   ↕
dim_artists
dim_venues
dim_dates
```

### fact_events

* Grain — one row per live event
* Why grain matters — prevents incorrect aggregation and defines analytical meaning of each row
* Deduplication logic — `row_number()` partitioned by `event_id` ordered by `loaded_at`
* Surrogate keys — generated with `dbt_utils.generate_surrogate_key()`
* Realistic failure mode — duplicate events or mismatched joins
* Downstream flow — central fact source for Streamlit analytics

### dim_artists

* Purpose — centralize performer-level enrichment across Ticketmaster, Spotify, and SeatGeek
* Join logic — normalized artist-name matching using `lower(artist_name)`
* Why this matters — combines streaming demand, event presence, and ticket-market popularity into one reusable dimension
* Weakness to admit — name-based entity matching is imperfect
* Improvement ideas — fuzzy matching, aliases, external artist identifiers

### dim_venues

* Purpose — reusable venue/location attributes for geographic analysis
* Key fields — venue_name, city, state
* Why separate dimension — prevents repeated venue metadata in the fact table

### dim_dates

* Purpose — reusable time analytics layer
* Key fields — day_name, quarter, month_name, is_weekend
* Why it matters — supports seasonality and temporal trend analysis

---

# Automation Layer

## GitHub Actions scheduling

* Files:

  * `.github/workflows/extract_ticketmaster.yml`
  * `.github/workflows/extract_spotify.yml`
* Purpose — automate extraction workflows through scheduled or manual GitHub Actions runs
* Workflow features:

  * `workflow_dispatch` for manual execution
  * scheduled cron execution
  * repository secrets for credentials
* Why automation matters — converts one-time scripts into reproducible pipelines
* Realistic failure mode — missing secrets, dependency installation failures, API outages
* Improvement ideas — alerting, retries, logging, orchestration expansion
* Downstream flow — automated extraction refreshes RAW Snowflake tables

---

# Knowledge Base Layer

## Knowledge base architecture

* Folders:

  * `knowledge/raw/`
  * `knowledge/wiki/`
  * `CLAUDE.md`
* Purpose — create an industry research layer that justifies the business logic behind the analytics pipeline
* Wiki structure:

  * `overview.md`
  * `key-entities.md`
  * `themes.md`
  * `index.md`

## Core thesis of the KB

* Streaming platforms, ticketing systems, audience analytics, and live-event economics are converging into one analytics ecosystem

## Key evidence-backed themes

### Streaming → touring convergence

* Source: `knowledge/raw/10-streaming-platforms-live-event-discovery.md`
* Spotify concert discovery and ticketing integrations support the use of monthly listeners as a demand signal

### AXS analytics ecosystem

* Source: `knowledge/raw/07-aeg-axs-ticketing-data-strategy.md`
* AXS uses fan identity systems, Mobile ID, and analytics infrastructure to support ticketing operations

### Identity resolution challenges

* Source: `knowledge/raw/15-audience-segmentation-luminate.md`
* Luminate / Quansic maintain millions of artist and asset identifiers, reinforcing the challenge of cross-platform entity matching

### Dynamic pricing and market demand

* Ticketing and live-event sources explain why pricing analytics and demand forecasting matter in entertainment BI

## Why the KB matters

* The KB explains WHY the pipeline exists, not just HOW it works
* It supports verbal defense of pricing analytics, artist enrichment, geography analysis, and streaming-demand integration
* Realistic failure mode — wiki synthesis missing important raw-source facts
* Improvement ideas — stronger citations and richer schema definitions

---

# Presentation / Consumption Layer

## Streamlit dashboard

* File: `streamlit_app.py`
* Purpose — presentation layer that turns Snowflake marts into interactive business insights
* Architecture:

```text
Snowflake MARTS
↓
Snowflake connector
↓
SQL query into pandas DataFrame
↓
Streamlit tabs/components
↓
Business insights
```

* Why Streamlit — rapid Python-native BI prototyping with flexible Snowflake integration
* Why query marts instead of RAW — marts are already cleaned, deduplicated, and business-ready
* Why denormalize into pandas — improves dashboard responsiveness and interactive filtering

## Dashboard sections

### Overview

* Executive KPI layer
* Metrics:

  * total events
  * unique artists
  * unique venues
  * average ticket price

### Pricing Analytics

* Explores relationship between artist popularity and pricing power
* Includes:

  * genre pricing
  * listener vs ticket-price scatterplots
  * pricing distributions

### Artist Insights

* Performer-level diagnostics
* Includes untapped opportunities logic:

  * high monthly listeners + low event count

### Venues & Geography

* Geographic concentration analysis
* Includes hotspot maps, venue rankings, market distributions

### Time Trends

* Temporal analysis layer
* Includes weekday/weekend and seasonal behavior

## Geocoding layer

* Local city/state coordinate dictionary with helper function
* Why local instead of API — fewer dependencies and faster dashboard performance

## Realistic dashboard limitations

* Entire dataset currently loads into pandas
* Some aggregations should be pushed back into Snowflake
* Static geocoding approach is not fully scalable

## Final downstream outcome

* Business users can interactively analyze artist demand, pricing strategy, market opportunity, venue performance, and touring insights through a unified entertainment analytics platform
