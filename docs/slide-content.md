# Presentation Slide Content

## Slide 1: Title

- **Live Music Analytics Pipeline**
- Rachel McDonald
- ISBA 4715 — Developing Business Applications with SQL

---

## Slide 2: Problem Statement

- Entertainment companies need to connect streaming popularity with live event performance
- Ticketing data (events, venues, pricing) and streaming data (listeners, engagement) live in silos
- BI analysts at companies like AXS (AEG Worldwide) need unified views to make data-driven booking, pricing, and marketing decisions
- Streaming metrics are a leading indicator of ticket demand — but only if you can combine the data

---

## Slide 3: Solution — Data Pipeline

- *[Insert pipeline diagram screenshot from README]*
- **Sources:** Ticketmaster Discovery API (200 events) + Spotify artist pages via Firecrawl (15 artists)
- **Warehouse:** Snowflake with RAW, STAGING, and MARTS schemas
- **Transform:** dbt star schema — 2 staging views, 4 mart tables (fact_events, dim_artists, dim_venues, dim_dates)
- **Automate:** GitHub Actions runs both extraction pipelines daily
- **Visualize:** Interactive Streamlit dashboard deployed on Community Cloud

---

## Slide 4: Star Schema Design

- *[Insert ERD screenshot from README]*
- **fact_events:** 200 events with pricing, sale status, and dimension keys
- **dim_artists:** 146 artists with Ticketmaster metadata joined to Spotify monthly listeners
- **dim_venues:** 184 venues with city and state
- **dim_dates:** Temporal attributes — day of week, month, quarter, weekend flag

---

## Slide 5: Descriptive Insights

- *[Insert screenshots from dashboard — Event Overview and Pricing Analytics sections]*
- Events are concentrated in a small number of genres — potential diversification opportunity
- Ticket prices vary significantly by genre — supports genre-specific pricing strategies
- Events cluster geographically in major metro areas (CA, NY, TX, FL)
- Weekend events dominate the schedule — weekday events are underrepresented

---

## Slide 6: Diagnostic Insights

- *[Insert scatter chart screenshot from dashboard — Artist Insights section]*
- **Key question:** Do streaming-popular artists have more live events?
- Artists with higher Spotify monthly listeners tend to have more scheduled events
- This validates the streaming-to-touring pipeline — streaming popularity is a leading indicator for live demand
- Some high-listener artists have few events, suggesting untapped booking opportunities
- Weekend vs weekday patterns suggest promotional pricing could drive incremental weekday attendance

---

## Slide 7: Recommendations

1. **Use streaming data as a booking signal:** City-level Spotify listener counts should inform tour routing decisions — where listeners are concentrated, demand for live events is likely
2. **Implement genre-aware dynamic pricing:** Price variation across genres suggests that pricing models should account for genre-specific demand elasticity
3. **Target mid-tier markets:** Geographic clustering in major metros means smaller markets may be underserved — streaming data can identify demand in these areas
4. **Promote weekday events:** Weekend dominance indicates an opportunity to use promotional pricing or bundling to fill weekday inventory
5. **Integrate streaming trends into dashboards:** BI teams should track streaming growth as a leading indicator, not just trailing ticket sales

---

## Slide 8: Tech Stack and Portfolio Value

- **End-to-end pipeline:** Extraction, warehousing, transformation, visualization, automation
- **Tools:** Python, Snowflake, dbt, Streamlit, GitHub Actions, Firecrawl, Claude Code
- **Mirrors real workflows:** Built to reflect the Sr. BI Analyst role at AXS (AEG Worldwide)
- **Knowledge base:** 17 industry sources synthesized into wiki — demonstrates research depth
- **Automated:** Both extraction pipelines run on daily schedules via GitHub Actions
- **Reproducible:** Anyone can clone the repo, configure credentials, and run the full pipeline
