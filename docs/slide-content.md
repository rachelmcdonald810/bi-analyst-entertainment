# Presentation Slide Content

## Slide 1: Title

- **Live Music Analytics Pipeline**
- Rachel McDonald
- ISBA 4715 — Developing Business Applications with SQL

---

## Slide 2: Streaming and Ticketing Data Live in Silos — Costing Promoters Revenue They Can't See

- Ticketing data (events, venues, pricing) and streaming data (listeners, engagement) sit in separate systems
- A third signal — ticketing demand scores — adds depth but also lives in its own silo
- BI analysts at companies like AXS (AEG Worldwide) make booking and pricing decisions without unified demand signals
- Streaming metrics predict ticket demand — but only if someone connects the data across sources

---

## Slide 3: Three Data Sources Feed One Pipeline — 1,968 Events, 30 Spotify Artists, 21 SeatGeek Demand Profiles

- *[Insert pipeline diagram screenshot from README]*
- **Source 1:** Ticketmaster Discovery API — 1,968 live music events with venues, dates, and pricing (where available)
- **Source 2:** Spotify artist pages via Firecrawl — 30 artists with monthly listener counts
- **Source 3:** SeatGeek API — performer popularity scores, demand metrics, and genre data for 21 artists
- **Warehouse:** Snowflake with RAW → STAGING → MARTS schemas
- **Transform:** dbt star schema — 4 staging views with cleaning/type casting, 4 mart tables with 17 tests
- **Automate:** Three GitHub Actions workflows run daily (6AM, 7AM, 8AM UTC)
- **Visualize:** 5-tab interactive Streamlit dashboard with geocoded event map

---

## Slide 4: A Star Schema Joins 1,968 Events to Artists Enriched with Spotify + SeatGeek Demand Signals

- *[Insert ERD screenshot from README]*
- **fact_events:** 1,968 events with pricing, sale status, and dimension keys
- **dim_artists:** 763 artists enriched with Spotify monthly listeners + SeatGeek popularity scores + genre data
- **dim_venues:** 934 venues with city and state for geographic analysis
- **dim_dates:** 198 dates with day of week, month, quarter, and weekend flag
- 12 artists have both Spotify and Ticketmaster data; 21 have SeatGeek demand scores

---

## Slide 5: Descriptive Insight

**Takeaway Title:** "75% of live events fall on Friday–Sunday, leaving 5 weekday nights generating near-zero venue revenue"

- *[Insert screenshot: Events by Day of Week bar chart from dashboard Time Trends tab]*
- **Callout:** Arrow or circle highlighting the Saturday/Friday bars towering over Monday–Wednesday
- **Key evidence:** Across 1,968 events, the vast majority cluster on Friday–Sunday while Monday–Wednesday have nearly empty schedules
- This pattern holds across all genres and markets — it's a systemic industry scheduling gap
- Weekday venue inventory sits idle, representing lost potential revenue for promoters and venues

---

## Slide 6: Diagnostic Insight

**Takeaway Title:** "Three demand signals confirm the same gap — high-streaming artists with strong SeatGeek scores but zero live events"

- *[Insert screenshot: Artist Demand Signals table + Scatter chart from dashboard]*
- **Callout:** Highlight artists like Taylor Swift (0.89 SG score, 101M Spotify listeners, 0 direct events) and Kendrick Lamar (0.88 SG score, 71M listeners, 0 events)
- **Key question:** Do streaming popularity AND ticketing demand predict live event supply?
- **Finding:** When both Spotify listeners and SeatGeek demand scores are high but event count is zero, it signals a supply-demand mismatch that booking teams should investigate
- **Data gap as a finding:** 0% of major artist events expose pricing via public APIs (Ticketmaster and SeatGeek both gate it). The highest-revenue events are the least transparent — itself a signal that premium data access is worth the investment

---

## Slide 7: Four Data-Backed Actions to Capture Untapped Live Music Revenue

1. **Book high-demand, low-supply artists into open markets** → Artists with 50M+ Spotify listeners and 0.7+ SeatGeek scores but few scheduled events represent proven demand with no current supply. Booking them fills venue dates with pre-built audiences.

2. **Launch weekday promotional pricing ("Tuesday Night Out")** → With 75% of events on weekends, 5 weeknights sit empty. Discounted weekday bundles could fill 20%+ of idle inventory, converting dead capacity into revenue.

3. **Route tours using multi-signal demand data** → Combine city-level Spotify listeners, SeatGeek market popularity, and Ticketmaster event density to identify markets where demand exceeds supply. Expect 15–20% higher sell-through vs gut-instinct routing.

4. **Invest in premium API access for major act pricing** → Public APIs return $0 pricing data for stadium-tier artists. The data blind spot covers the highest-revenue segment. Premium access or scraping infrastructure would close this gap for pricing optimization.

---

## Slide 8: A Data Gap Is Still a Finding — Dynamic Pricing Creates a Blind Spot for the Highest-Revenue Events

**Takeaway Title:** "0% of major artist events expose ticket pricing through public APIs — the biggest revenue drivers are the least transparent"

- *[Insert screenshot: Artist detail card showing "Dynamic Pricing" for Bruno Mars or Metallica]*
- **Callout:** Highlight the "Dynamic Pricing" label where avg ticket price should be
- **Key evidence:** Across all 12 Spotify-matched artists (Bruno Mars, Metallica, Ed Sheeran, etc.), zero events returned pricing from either Ticketmaster or SeatGeek public APIs
- Meanwhile, 24% of smaller/niche act events DO have pricing — the transparency gap is inversely correlated with revenue
- **Why it matters:** BI teams optimizing ticket pricing for top acts are flying blind without premium data partnerships. This is the strongest argument for investing in paid data infrastructure.

---

## Slide 9: Built with the Same Stack a BI Team Uses in Production — Three Sources, Automated Daily

- **End-to-end pipeline:** 3 extraction scripts → Snowflake warehouse → dbt transformation → Streamlit dashboard
- **Three data sources:** Ticketmaster (events), Spotify (streaming), SeatGeek (ticketing demand)
- **Tools:** Python, Snowflake, dbt, Streamlit, GitHub Actions, Firecrawl, Claude Code
- **Quality:** 17 dbt tests, staging models with cleaning/deduplication/type casting
- **Automated:** Three GitHub Actions workflows on daily schedules with secrets management
- **Knowledge base:** 17 industry sources from 11+ sites, synthesized into queryable wiki
- **Mirrors real workflows:** Built to reflect the Sr. BI Analyst role at AXS (AEG Worldwide)
- **Reproducible:** Clone, configure credentials, run — full pipeline works end to end
