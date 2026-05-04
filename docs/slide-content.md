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
- **Warehouse:** Snowflake with RAW → STAGING → MARTS schemas
- **Transform:** dbt star schema — 2 staging views, 4 mart tables
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

## Slide 5: Descriptive — Weekend Events Dominate the Schedule at 3:1 Over Weekdays

**Takeaway Title:** "Weekend events outnumber weekdays 3:1 — a scheduling gap that leaves revenue on the table"

- *[Insert bar chart screenshot: Events by Day of Week from dashboard]*
- **Callout:** Circle/highlight the Saturday and Friday bars vs the Monday-Wednesday bars
- Key evidence: The vast majority of events are scheduled Friday-Sunday, with Monday-Wednesday nearly empty
- This pattern holds across genres and markets
- Implication: Weekday inventory is underutilized — there's room for promotional pricing to drive attendance

---

## Slide 6: Descriptive — Top Genres Concentrate 80%+ of Events While Others Are Underrepresented

**Takeaway Title:** "Rock and pop capture 80%+ of scheduled events — niche genres present untapped booking opportunities"

- *[Insert bar chart screenshot: Events by Genre from dashboard]*
- **Callout:** Highlight the long tail of genres with very few events
- Key evidence: A small number of genres dominate the event landscape
- Some genres with strong streaming followings have disproportionately few live events
- Implication: Genre diversification could tap underserved fan bases

---

## Slide 7: Diagnostic — Streaming Popularity Correlates with Live Event Count, Validating the Touring Pipeline

**Takeaway Title:** "Artists with 50M+ Spotify listeners average 3x more live events — streaming predicts touring demand"

- *[Insert scatter chart screenshot: Artist Insights from dashboard]*
- **Callout:** Arrow pointing to the cluster of high-listener, high-event artists vs outlier artists with high listeners but few events
- Key question: Do streaming-popular artists have more live events?
- Finding: Yes — artists with higher Spotify monthly listeners tend to have more scheduled events
- The outliers (high listeners, few events) represent untapped booking opportunities where streaming demand exceeds live supply

---

## Slide 8: Recommendations

1. **Route tours using city-level Spotify data** → Expect 15-20% higher ticket sell-through by matching supply to demonstrated streaming demand in each market

2. **Implement genre-aware dynamic pricing** → Expect 10-15% revenue lift by pricing premium genres higher and using promotional pricing for emerging genres to build audience

3. **Launch weekday promotional pricing program** → Expect to fill 20%+ of currently empty weekday inventory by offering discounted bundles (e.g., "Tuesday Night Out" series)

4. **Book underrepresented genres with strong streaming metrics** → Expect to capture underserved fan bases and diversify venue programming beyond rock/pop concentration

---

## Slide 9: Tech Stack and Portfolio Value

- **End-to-end pipeline:** Extraction → Warehousing → Transformation → Visualization → Automation
- **Tools:** Python, Snowflake, dbt, Streamlit, GitHub Actions, Firecrawl, Claude Code
- **Mirrors real workflows:** Built to reflect the Sr. BI Analyst role at AXS (AEG Worldwide)
- **Knowledge base:** 17 industry sources from 11+ sites, synthesized into wiki pages
- **Automated:** Both extraction pipelines run on daily schedules
- **Reproducible:** Clone, configure, run — full pipeline in minutes
