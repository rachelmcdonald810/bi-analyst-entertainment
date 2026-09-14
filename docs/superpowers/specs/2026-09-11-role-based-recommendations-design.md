# Role-Based Recommendations, Artist Career Arc & Financial Modeling — Design Spec
**Date:** 2026-09-13 (updated from 2026-09-11)
**Project:** Live Music Analytics Pipeline
**Status:** Approved for implementation

---

## Overview

This spec covers three major additions to the Streamlit dashboard:

1. **Role-Based Recommendations** — Transform the existing Recommendations tab into a role-aware experience with a selector that switches between four views: Booking Agent, Promoter, Artist Manager, and Label Executive.
2. **Artist Career Arc** — A new section inside the Artist Insights tab that tracks and compares an artist's growth trajectory over time.
3. **Financial Modeling Layer** — Embedded inside the Artist Manager tour builder (Step 5) and surfaced as a portfolio-level summary in the Label Executive view. Covers forward revenue projection, target gap analysis, comp analysis, venue/touring company splits, itemized cost breakdown, and ROI.

All additions depend on two new data sources: historical Spotify listener accumulation and venue capacity enrichment.

---

## 1. New Data Sources

### 1.1 Release Schedule Scraper
**Script:** `src/scrape_spotify_releases.py`
**Destination:** `RAW_STAGING.STG_SPOTIFY_RELEASES`

| Column | Type | Description |
|---|---|---|
| ARTIST_NAME | VARCHAR | Matched to STG_SPOTIFY_ARTISTS |
| LATEST_RELEASE_TITLE | VARCHAR | Album or single name |
| RELEASE_TYPE | VARCHAR | 'single' or 'album' |
| RELEASE_DATE | DATE | Date of latest release |
| LOADED_AT | TIMESTAMP | Pipeline run time |

Scraped via Firecrawl from each artist's Spotify page URL (already stored in `STG_SPOTIFY_ARTISTS.SPOTIFY_URL`). Runs daily via existing GitHub Actions workflow. Overwrites previous record per artist (we only need the latest release, not history).

**Classification logic in dashboard:**
- **Recently released:** `RELEASE_DATE` within last 90 days
- **No recent release:** `RELEASE_DATE` older than 90 days or NULL

### 1.2 Historical Listener Accumulation
**Destination:** `RAW_STAGING.STG_SPOTIFY_ARTISTS` (schema change — stop overwriting, append instead)

Add a unique constraint on `(ARTIST_NAME, LOADED_AT::DATE)` so each daily pipeline run appends a new row rather than updating. This creates a time series of listener counts per artist.

**Growth rate computation (in dashboard Python):**
```
growth_rate = (listeners_now - listeners_30d_ago) / listeners_30d_ago
```
Requires at least 30 days of data to produce a signal. Before that, growth rate shows as "Insufficient data."

**Artist Tier Classification:**

| Tier | Criteria |
|---|---|
| Proven | SG score >0.75 AND monthly listeners >1M AND tour revenue exists |
| Emerging | Listener growth >15% MoM OR recent release with listeners 100K–1M |
| Experimental | Listeners <100K OR no SG score OR no tour history |

Tier is computed per artist at dashboard load time and used across all three role views.

### 1.3 Venue Capacity Enrichment
**Script:** `src/scrape_venue_capacity.py`
**Destination:** `RAW_STAGING.STG_VENUE_CAPACITY`

| Column | Type | Description |
|---|---|---|
| VENUE_NAME | VARCHAR | Matched to DIM_VENUES |
| CITY | VARCHAR | |
| STATE | VARCHAR | |
| CAPACITY | INT | Max capacity |
| VENUE_TIER | VARCHAR | 'club' / 'theater' / 'amphitheater' / 'arena' |
| LOADED_AT | TIMESTAMP | |

Scraped via Firecrawl from SeatGeek venue pages. Venue tier bucketing:
- Club: <1,000
- Theater: 1,000–5,000
- Amphitheater: 5,000–20,000
- Arena: >20,000

---

## 2. Role-Based Recommendations Tab

### 2.1 Role Selector
At the top of the existing Recommendations tab, replace the current header with:

```python
role = st.radio("I am a:", ["👔 Booking Agent", "📣 Promoter", "🎤 Artist Manager", "🏷️ Label Executive"],
                horizontal=True)
```

The content below the selector renders conditionally based on `role`.

---

### 2.2 Booking Agent View

**Panel 1 — Artist Pitch List**

Combines: Spotify listeners, listener growth rate, release schedule, SeatGeek events, TM events.

Artists are grouped into four tiers displayed as color-coded sections:

| Badge | Criteria | Pitch Angle |
|---|---|---|
| 🟢 Rising Fast | Growth >15% MoM | "Momentum play — book before price goes up" |
| 🟡 Pre-Tour Buildup | Recent release (<90d), no events | "Just dropped, no dates yet — pitch now" |
| 🔴 Genuine Gap | No recent release, no events, stable listeners | "Strong audience, no live strategy" |
| ⚪ Deprioritize | Declining listeners | "Audience shrinking — wait and watch" |

Each row shows: Artist, Monthly Listeners, 30d Growth, Latest Release, SG Score, Artist Tier, Pitch Badge.

**Panel 2 — Underpriced Shows**
Unchanged from current implementation. Artist tier label added as a column.

**Panel 3 — Market Expansion Signals**
For each artist in Panel 1, show:
- Top 3 current markets (by SeatGeek event concentration)
- 2–3 adjacent states with high genre listener density but no events
- Logic: join events+genre+state data, find states where same genre has high event volume but this artist has zero presence, prioritize states geographically adjacent to artist's top markets

---

### 2.3 Promoter View

**Panel 1 — Market Opportunity Score**

For each city in `CITY_COORDS`, compute:
```
opportunity_score = (
    0.4 × normalized_listener_demand +
    0.4 × normalized_supply_gap +
    0.2 × genre_fit_score
)
```
- `listener_demand`: sum of Spotify listeners for artists with no TM events in that city
- `supply_gap`: 1 - (tm_events / max_tm_events_any_city), normalized 0–1
- `genre_fit_score`: ratio of genre-matched events historically in that city

Displayed as a ranked table with genre and region filters. Cities scored 0–100.

**Panel 2 — Deal Benchmarking**

Inputs (st.selectbox): market (city), artist tier.

Outputs:
- Peer avg ticket price in that market for that tier
- Recommended venue capacity range
- Estimated gross revenue range: `capacity × price × sellthrough_rate`
  - Sellthrough rates by tier: Proven=90%, Emerging=70%, Experimental=50%
- Day-of-week recommendation: Proven → Fri/Sat, Emerging → Thu/Fri, Experimental → Tue–Thu

**Panel 3 — Risk Flags**

Artists where:
- Listener growth is negative (declining MoM)
- SG score dropped (requires historical SG data — flag as "score data unavailable" if not yet accumulated)
- High listeners but very low SG score (streaming audience not converting to ticket buyers)

Displayed as a warning table with risk type labeled per artist.

---

### 2.4 Artist Manager View — Interactive Tour Builder

**Step 1 — Artist Snapshot** (auto-populated)
- Monthly listeners + 30d growth rate + growth trend arrow
- Latest release title, type, date + days since release
- Artist tier badge (Proven / Emerging / Experimental)
- Top 5 states by listener concentration (horizontal bar)
- SeatGeek score + upcoming events count
- Pricing signal (Underpriced / Fair / Overpriced vs peers)

**Step 2 — Tour Constraints** (manager inputs)

| Input | Widget | Options |
|---|---|---|
| Tour length | st.slider | 2–16 weeks |
| Target regions | st.multiselect | Northeast, Southeast, Midwest, South, West, Northwest |
| Min venue capacity | st.number_input | Default by tier |
| Max venue capacity | st.number_input | Default by tier |
| Pricing tier | st.radio | Budget-friendly / Mid-tier / Premium |
| Include opener | st.checkbox | Yes/No |
| Opener genre filter | st.multiselect (if opener=Yes) | From SeatGeek genres |
| Opener SG score max | st.slider (if opener=Yes) | 0.0–headliner score |

**Step 3 — Generated Tour Route**

Algorithm:
1. Filter cities by selected regions and venue capacity range
2. Score each city: listener demand × genre fit × supply gap
3. Select top N cities (N = tour_length_weeks × 0.75, rounded)
4. Order cities by geographic proximity using lat/lon from `CITY_COORDS` (nearest-neighbor routing starting from artist's top market)
5. Assign shows per city: 1 show default, 2 if city is top-3 market, 3 if it's the artist's #1 market
6. Assign venue tier per city based on listener density and capacity constraints
7. Assign ticket price range per city: venue capacity tier × peer benchmarking × pricing tier preference
8. Flag day-of-week per city based on artist tier

Output as an interactive table + map. Map uses existing `scatter_geo` pattern with route lines connecting cities in order.

**Market Expansion Flags** (inline with route):
- Cities outside artist's current top-5 states that appear on the route get a 🌱 flag
- Tooltip explains: "Your listeners are concentrated in [State]. This market shows strong [Genre] genre demand — good expansion target."
- Adjacent state logic: precomputed state adjacency list hardcoded in app

**Step 4 — Opener Recommendations**

For each city on the route, query `STG_SEATGEEK_EVENTS` for performers who:
- Match selected genre(s)
- Have SG score < headliner's SG score
- Have at least 1 event in that city or adjacent cities

Display as expandable section per city: "Suggested openers for [City]" → table of 2–3 artists with their SG score, genre, and city event count.

Manager can override genre filter and score threshold via sliders that re-filter the table live.

**Step 5 — Financial Model** (inside `st.expander("📊 Financial Model", expanded=False)`)

This step takes the tour route from Step 3 as its input. All fields are pre-filled with industry benchmarks and editable by the manager.

**5a — Forward Projection**

Inputs (pre-filled, all editable):

| Input | Default | Source |
|---|---|---|
| Avg venue capacity | From STG_VENUE_CAPACITY per city | Scraped |
| Sellthrough rate | Proven=90%, Emerging=70%, Experimental=50% | Tier-based |
| Avg ticket price | From peer benchmarking × pricing tier | Computed |
| Venue/touring co. split % | Arena=20%, Amphitheater=15%, Theater=10%, Club=8% | Tier default |
| User override per city | st.number_input per row | Manual |

Outputs per city and tour total:
- **Gross revenue** = capacity × sellthrough × avg ticket price
- **Venue/touring co. take** = gross × split %
- **Net to artist** = gross − venue take
- **Projected total tour gross** = sum across all cities

Displayed as an editable table (one row per city) + summary metric cards at top:
`Total Gross | Total Venue Take | Net to Artist | Avg per Show`

**5b — Revenue Target Gap Analysis**

```python
revenue_target = st.number_input("Label revenue target ($)", value=0, step=100_000)
```

If target > 0, show:
- **Gap** = target − projected net to artist
- **Gap as % of projection**
- **Scenarios to close the gap** (auto-computed):
  - Add N more shows at average net per show
  - Increase avg ticket price by $X
  - Increase sellthrough rate by X%
  - Combination: +2 shows + +$10 ticket price + +5% sellthrough

Displayed as a callout box: "To hit your $50M target, you need one of: 8 more shows, $18 higher avg ticket price, or 12% more sellthrough."

Streaming informs projection inputs contextually: an artist with 30-day listener growth >15% gets a tooltip on sellthrough rate: "Growing audience — consider adjusting sellthrough upward."

**5c — Comp Analysis**

Two sub-sections side by side:

*Own History (left):*
- Revenue per show over prior tours (from STG_TOUR_REVENUE)
- Avg ticket price over prior tours
- Venue tier progression
- Sellthrough trend (estimated from tickets_sold / capacity where available)

*Peer Benchmarks (right):*
- For same artist tier: avg gross per show, avg ticket price, avg venue capacity
- Peer artists listed by name with their tour stats from STG_TOUR_REVENUE
- "You are projecting $X per show vs. peer avg of $Y — [above/below] benchmark by Z%"

**5d — Itemized Cost Breakdown**

Pre-filled industry benchmarks (editable via st.number_input, expressed as % of gross or flat $):

| Cost Bucket | Default | Type |
|---|---|---|
| Production (staging, lighting, sound) | 25% of gross | % |
| Artist guarantee (if applicable) | 0 | Flat $ |
| Marketing & promotion | 8% of gross | % |
| Travel & logistics | 5% of gross | % |
| Crew & staffing | 7% of gross | % |
| Miscellaneous / contingency | 3% of gross | % |

Outputs:
- **Total costs** = sum of all buckets applied to projected gross
- **Net tour profit** = net to artist − total costs
- **ROI** = net tour profit / total costs × 100
- **Break-even shows** = total fixed costs / avg net per show

Displayed as:
1. A donut chart showing revenue allocation (venue take, each cost bucket, net profit)
2. Summary metric cards: `Net Profit | ROI | Break-even Shows`
3. Editable cost table with live recalculation on any change

---

### 2.5 Label Executive View

This view shows a **portfolio-level financial summary** across all artists in the dataset who have tour revenue data. It is read-only — no interactive builder. The label executive comes here to see the big picture.

**Panel 1 — Portfolio Overview**

Metric cards across the top:
- Total projected gross (sum of all artist forward projections at default assumptions)
- Total net to artists (after venue splits)
- Portfolio avg ROI
- Number of artists by tier (Proven / Emerging / Experimental)

**Panel 2 — Artist Revenue Leaderboard**

Table of all artists with tour data, sorted by projected net tour profit descending:

| Artist | Tier | Projected Gross | Venue Take | Est. Costs | Net Profit | ROI | vs. Peer Avg |
|---|---|---|---|---|---|---|---|

Color-coded ROI column: green >50%, yellow 20–50%, red <20%.

**Panel 3 — Comp Analysis: Portfolio vs. Industry**

For each artist tier, show:
- This portfolio's avg gross per show vs. industry peer avg (from STG_TOUR_REVENUE across all artists)
- This portfolio's avg ticket price vs. peer avg
- Bar chart: portfolio artists vs. peer median, grouped by tier

**Panel 4 — Revenue Target Planning**

A single label-level revenue target input:
```python
label_target = st.number_input("Portfolio revenue target ($)", step=1_000_000)
```

Shows:
- Which artists are on track to hit their individual targets
- Total projected portfolio net vs. label target
- Gap and scenario analysis at portfolio level (same logic as Step 5b but aggregated)
- Which artists have the highest ROI and should be prioritized for investment

**Panel 5 — Risk & Opportunity Flags**

Two columns:
- 🔴 **At-risk artists**: declining listeners, low sellthrough projection, ROI <20%, or pricing below peer median by >20%
- 🟢 **High-opportunity artists**: rising fast, underpriced relative to peers, strong genre-market fit in untapped cities

---

## 3. Artist Career Arc (Artist Insights Tab)

Added as a new section below the existing per-artist event table in Tab 3, visible only when a specific artist is selected (not "All Artists").

### Panel 1 — Listener Growth Over Time
Line chart: x=date (from historical `STG_SPOTIFY_ARTISTS` accumulation), y=monthly listeners.
Annotate release dates from `STG_SPOTIFY_RELEASES` as vertical dashed lines labeled with release title.
Requires minimum 2 data points to render; shows "Accumulating data — check back after more pipeline runs" if only 1 snapshot exists.

### Panel 2 — Venue Size Progression
Step/bar chart: x=event date, y=venue capacity (from `STG_VENUE_CAPACITY` joined to `FACT_EVENTS`).
Shows trajectory from club → theater → amphitheater → arena over time.
Annotate % change in avg venue capacity year-over-year where data allows.

### Panel 3 — Revenue & Audience Efficiency
Built from `STG_TOUR_REVENUE` (multiple tours where available):
- **Listener-to-buyer ratio** per tour year: `tickets_sold / monthly_listeners_at_time`
- **Revenue per show** over time: `gross_revenue / shows`
- **Avg ticket price** trajectory

Displayed as a three-metric line chart with year on x-axis. Falls back gracefully if artist has only one tour entry.

### Panel 4 — Venue vs Venue / Tour vs Tour Comparison
Two `st.selectbox` widgets: "Compare [Tour/Venue A]" vs "[Tour/Venue B]"

Side-by-side metric cards showing:
- Gross revenue
- Tickets sold
- Avg ticket price
- Sellthrough rate (tickets_sold / venue_capacity, where capacity available)
- Revenue per show

Delta indicators show which performed better and by how much (e.g. "+$2.1M gross", "+15% avg ticket").

---

## 4. Data Flow Summary

```
GitHub Actions (daily)
  ├── scrape_spotify_releases.py → STG_SPOTIFY_RELEASES
  ├── extract_spotify.py (append mode) → STG_SPOTIFY_ARTISTS (historical)
  └── scrape_venue_capacity.py → STG_VENUE_CAPACITY

Streamlit Dashboard
  ├── Load all staging + mart tables
  ├── Compute artist tiers (Proven/Emerging/Experimental)
  ├── Compute growth rates from historical listener data
  ├── Compute pricing signals (existing)
  └── Render role-based views + career arc
```

---

## 5. Financial Model — Key Formulas Reference

```
Gross Revenue (per city)     = venue_capacity × sellthrough_rate × avg_ticket_price
Venue/Touring Co. Take       = gross_revenue × split_pct
Net to Artist (per city)     = gross_revenue − venue_take
Total Costs                  = Σ(cost_bucket_pct × gross_revenue) + flat_costs
Net Tour Profit              = Σ(net_to_artist) − total_costs
ROI                          = net_tour_profit / total_costs × 100
Break-even Shows             = total_fixed_costs / avg_net_per_show
Gap to Target                = revenue_target − net_tour_profit
Peer Benchmark Delta         = (artist_metric − peer_avg) / peer_avg × 100
Streaming Context Signal     = listener_30d_growth_rate (informs sellthrough tooltip only)
```

---

## 6. Files Changed

| File | Change |
|---|---|
| `streamlit_app.py` | Role selector + 4 role views + financial model + career arc |
| `src/scrape_spotify_releases.py` | New scraper |
| `src/scrape_venue_capacity.py` | New scraper |
| `src/extract_spotify.py` | Change MERGE to INSERT (append mode) |
| `.github/workflows/` | Add two new scrapers to daily pipeline |
| `dbt_project/models/staging/` | New staging models for releases + venue capacity |

---

## 7. What We Are Not Building

- Real-time ticket sales velocity (no API access to live TM sales data)
- Chartmetric integration (external paid tool, out of scope)
- Actual tour booking or calendar integration
- Label royalty accounting or recording advance modeling
- Tax or legal cost modeling
