# CLAUDE.md

## Project Overview
This repository contains my project, **Live Music Analytics Pipeline**, developed for a course in developing business applications with SQL. The goal of the project is to build a data pipeline that combines ticketing and streaming data to generate business intelligence insights relevant to the live entertainment industry.

The project is inspired by the Sr. BI Analyst role at AXS (AEG Worldwide), particularly the job requirement to use SQL and analytics tools to generate business insights. This repository is intended to function both as a class project and as a portfolio piece for music and entertainment analytics roles.

## Project Goals
The main goals of this project are to:
- Collect data from live music and streaming-related APIs such as Ticketmaster and Spotify
- Store and organize the data in a structured relational format
- Use SQL to transform raw data into business insights
- Analyze metrics such as event sales velocity, artist popularity, venue performance, and audience engagement
- Create a clean, organized repository that demonstrates technical and analytical skills

## Repository Structure
- `src/` contains Python scripts for data extraction (Ticketmaster API, Spotify via Firecrawl)
- `dbt_project/` contains dbt models for staging and mart transformations in Snowflake
- `streamlit_app.py` is the interactive dashboard connected to Snowflake mart tables
- `knowledge/` contains the knowledge base (raw sources and wiki pages)
- `.github/workflows/` contains GitHub Actions pipelines for automated extraction
- `docs/` contains project documentation including the proposal and slide content

## Tools and Technologies
- Python (extraction scripts)
- Snowflake (cloud data warehouse)
- dbt (data transformation — staging views + mart tables)
- Streamlit (interactive dashboard, deployed on Community Cloud)
- GitHub Actions (automated daily extraction pipelines)
- Firecrawl (web scraping for Spotify artist data)

## Development Notes
When contributing code or making suggestions:
- Keep the repository organized by function
- Prefer clear and readable Python and SQL
- Do not commit secrets such as API keys or `.env` files
- Maintain professional naming conventions for files and folders

## Querying the Knowledge Base
The `knowledge/` directory contains research on why combining streaming and live performance data matters for the entertainment industry.

**How to query the knowledge base:**
1. Start with `knowledge/index.md` for the full inventory of sources and wiki pages
2. For high-level questions about the industry, refer to the wiki pages in `knowledge/wiki/`:
   - `overview.md` — Industry landscape and why streaming + live data convergence matters
   - `key-entities.md` — Major companies (AEG/AXS, Live Nation, Spotify, Chartmetric, Luminate)
   - `themes.md` — Key trends (streaming-to-touring pipeline, dynamic pricing, fan segmentation)
3. For detailed evidence or specific facts, search the raw sources in `knowledge/raw/` (17 files from 11+ sites including Pollstar, Billboard, Forbes, Spotify, IFPI)
4. When answering questions about the knowledge base:
   - Always cite which source file(s) the answer comes from
   - Synthesize across multiple sources when possible rather than quoting a single source
   - Connect findings back to the project's goal of demonstrating BI analyst workflows for live entertainment

**Example queries this knowledge base can answer:**
- "Why should entertainment companies combine streaming and ticketing data?"
- "How does Spotify listener data help with tour routing decisions?"
- "What is AXS's approach to ticketing technology and fan data?"
- "How has live music revenue changed since the pandemic?"
- "What role does dynamic pricing play in the concert industry?"

## Context for AI Assistance
If using Claude to assist with this project:
- Prioritize clean SQL workflows and reproducible data pipelines
- Suggest directory and file organization that would make sense for a BI or analytics portfolio
- Keep recommendations aligned with live music, ticketing, streaming, and entertainment analytics use cases
- Favor practical business insight generation over overly theoretical solutions
