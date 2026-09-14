# Data Pipeline Additions — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add five new data sources to the Live Music Analytics pipeline: Spotify release schedule, venue capacity, Bandsintown tour calendar, Spotify listener history (time series), and SeatGeek resale velocity — all feeding new Snowflake staging tables and dbt models.

**Architecture:** The existing raw tables (`RAW_SPOTIFY_ARTISTS`, `RAW_SEATGEEK_EVENTS`) already append on each pipeline run — the dbt models just deduplicate. New dbt models expose the full time series for growth rate and velocity calculations. Three new scrapers follow the exact same pattern as `src/extract_spotify_firecrawl.py`: Firecrawl or SeatGeek API → parse → INSERT into Snowflake raw table.

**Tech Stack:** Python 3.12, Firecrawl (firecrawl-py==4.23.0), SeatGeek API, Snowflake connector, dbt-snowflake, GitHub Actions, pytest

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `src/scrape_spotify_releases.py` | Create | Scrape latest release date/title from Spotify artist pages |
| `src/scrape_venue_capacity.py` | Create | Fetch venue capacity from SeatGeek API |
| `src/scrape_tour_calendar.py` | Create | Scrape announced tour dates from Bandsintown |
| `dbt_project/models/staging/stg_spotify_releases.sql` | Create | Stage release data, one row per artist |
| `dbt_project/models/staging/stg_spotify_artists_history.sql` | Create | Full time series of listener counts (no dedup) |
| `dbt_project/models/staging/stg_seatgeek_velocity.sql` | Create | Day-over-day listing_count and event_score changes |
| `dbt_project/models/staging/stg_venue_capacity.sql` | Create | Stage venue capacity with tier bucketing |
| `dbt_project/models/staging/stg_tour_calendar.sql` | Create | Stage announced tour dates |
| `dbt_project/models/staging/sources.yml` | Modify | Register 3 new raw tables |
| `dbt_project/models/staging/schema.yml` | Modify | Add descriptions + tests for 5 new models |
| `.github/workflows/scrape_spotify_releases.yml` | Create | Daily workflow for release scraper |
| `.github/workflows/scrape_venue_capacity.yml` | Create | Daily workflow for venue capacity scraper |
| `.github/workflows/scrape_tour_calendar.yml` | Create | Daily workflow for tour calendar scraper |
| `tests/test_parsers.py` | Create | Unit tests for all parsing functions |

---

### Task 1: Create Snowflake Raw Tables

These tables must exist before any scraper runs. Run these SQL statements in Snowflake (Snowsight worksheet) once manually to bootstrap.

**Files:**
- No file — run SQL directly in Snowsight

- [ ] **Step 1: Run DDL in Snowsight**

```sql
USE DATABASE LIVE_MUSIC_DB;
USE SCHEMA RAW;

CREATE TABLE IF NOT EXISTS RAW_SPOTIFY_RELEASES (
    ARTIST_NAME          VARCHAR,
    ARTIST_SPOTIFY_URL   VARCHAR,
    LATEST_RELEASE_TITLE VARCHAR,
    RELEASE_TYPE         VARCHAR,
    RELEASE_DATE         DATE,
    LOADED_AT            TIMESTAMP_TZ
);

CREATE TABLE IF NOT EXISTS RAW_VENUE_CAPACITY (
    VENUE_NAME   VARCHAR,
    CITY         VARCHAR,
    STATE        VARCHAR,
    CAPACITY     NUMBER,
    VENUE_TIER   VARCHAR,
    SG_VENUE_ID  VARCHAR,
    LOADED_AT    TIMESTAMP_TZ
);

CREATE TABLE IF NOT EXISTS RAW_TOUR_CALENDAR (
    ARTIST_NAME  VARCHAR,
    EVENT_DATE   DATE,
    VENUE_NAME   VARCHAR,
    CITY         VARCHAR,
    STATE        VARCHAR,
    TICKET_URL   VARCHAR,
    SOURCE       VARCHAR,
    LOADED_AT    TIMESTAMP_TZ
);
```

- [ ] **Step 2: Verify tables exist**

Run in Snowsight:
```sql
SHOW TABLES IN SCHEMA LIVE_MUSIC_DB.RAW;
```
Expected: `RAW_SPOTIFY_RELEASES`, `RAW_VENUE_CAPACITY`, `RAW_TOUR_CALENDAR` appear in results.

---

### Task 2: Unit Tests for Parsing Functions

Write tests first — they define the contract each parser must satisfy.

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_parsers.py`

- [ ] **Step 1: Create tests directory**

```bash
mkdir -p tests
touch tests/__init__.py
```

- [ ] **Step 2: Write failing tests**

Create `tests/test_parsers.py`:

```python
"""Unit tests for pipeline parsing functions."""
import pytest
from datetime import date


# ── Release parsing ───────────────────────────────────────────────────────────

def test_parse_release_date_album():
    from src.scrape_spotify_releases import parse_release
    markdown = """
## Discography
### Popular releases
**Short n' Sweet** · Album · 2024
**Emails I Can't Send** · Album · 2022
"""
    result = parse_release(markdown)
    assert result["title"] == "Short n' Sweet"
    assert result["release_type"] == "Album"
    assert result["release_year"] == "2024"


def test_parse_release_date_single():
    from src.scrape_spotify_releases import parse_release
    markdown = """
**Please Please Please** · Single · 2024
"""
    result = parse_release(markdown)
    assert result["title"] == "Please Please Please"
    assert result["release_type"] == "Single"


def test_parse_release_returns_none_on_empty():
    from src.scrape_spotify_releases import parse_release
    result = parse_release("")
    assert result is None


def test_parse_release_returns_none_on_no_match():
    from src.scrape_spotify_releases import parse_release
    result = parse_release("No release information found here.")
    assert result is None


# ── Venue capacity parsing ────────────────────────────────────────────────────

def test_venue_tier_arena():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(25000) == "arena"


def test_venue_tier_amphitheater():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(8000) == "amphitheater"


def test_venue_tier_theater():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(3000) == "theater"


def test_venue_tier_club():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(500) == "club"


def test_venue_tier_boundary_theater_low():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(1000) == "theater"


def test_venue_tier_boundary_amphitheater_low():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(5000) == "amphitheater"


# ── Tour calendar parsing ─────────────────────────────────────────────────────

def test_parse_bandsintown_events_basic():
    from src.scrape_tour_calendar import parse_events
    markdown = """
## Upcoming Events

**Sep 20, 2026** — Madison Square Garden, New York, NY [Get Tickets](https://bandsintown.com/t/123)
**Oct 5, 2026** — Crypto.com Arena, Los Angeles, CA [Get Tickets](https://bandsintown.com/t/456)
"""
    events = parse_events(markdown, "Test Artist")
    assert len(events) == 2
    assert events[0]["city"] == "New York"
    assert events[0]["state"] == "NY"
    assert events[0]["venue_name"] == "Madison Square Garden"


def test_parse_bandsintown_events_empty():
    from src.scrape_tour_calendar import parse_events
    events = parse_events("No upcoming events.", "Test Artist")
    assert events == []


def test_parse_bandsintown_events_returns_list():
    from src.scrape_tour_calendar import parse_events
    result = parse_events("", "Test Artist")
    assert isinstance(result, list)
```

- [ ] **Step 3: Run tests to verify they all fail**

```bash
cd ~/isba-4715/bi-analyst-entertainment && source venv/bin/activate && pip install pytest -q && pytest tests/test_parsers.py -v 2>&1 | head -40
```

Expected: All tests fail with `ModuleNotFoundError` — the source modules don't exist yet.

---

### Task 3: Create `src/scrape_spotify_releases.py`

**Files:**
- Create: `src/scrape_spotify_releases.py`

- [ ] **Step 1: Create the scraper**

```python
"""
Scrape latest release date and title from Spotify artist pages via Firecrawl.
Loads into RAW_SPOTIFY_RELEASES (one row per artist, overwrites previous).
"""
import os
import re
import snowflake.connector
from dotenv import load_dotenv
from firecrawl import V1FirecrawlApp as FirecrawlApp
from datetime import datetime, timezone

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)


def parse_release(markdown: str) -> dict | None:
    """
    Extract the latest release title, type, and year from Spotify page markdown.

    Spotify pages render releases as: **Title** · Album|Single|EP · YYYY
    Returns dict with keys: title, release_type, release_year
    Returns None if no match found.
    """
    if not markdown:
        return None
    pattern = r"\*\*([^*]+)\*\*\s*·\s*(Album|Single|EP|Compilation)\s*·\s*(\d{4})"
    match = re.search(pattern, markdown)
    if not match:
        return None
    return {
        "title": match.group(1).strip(),
        "release_type": match.group(2).strip(),
        "release_year": match.group(3).strip(),
    }


def scrape_artist_page(url: str) -> str | None:
    """Scrape a Spotify artist page and return the markdown content."""
    try:
        result = app.scrape_url(url, formats=["markdown"])
        return result.markdown if result else None
    except Exception as e:
        print(f"  Firecrawl error for {url}: {e}")
        return None


def get_artist_urls(conn) -> list[tuple[str, str]]:
    """Fetch artist names and Spotify URLs from Snowflake."""
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ARTIST_NAME, SPOTIFY_URL
        FROM RAW_SPOTIFY_ARTISTS
        WHERE SPOTIFY_URL IS NOT NULL
        ORDER BY ARTIST_NAME
    """)
    rows = cur.fetchall()
    cur.close()
    return [(row[0], row[1]) for row in rows]


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def load_releases(conn, rows: list[tuple]):
    """Delete existing records for these artists and insert fresh data."""
    if not rows:
        print("No release data to load.")
        return
    cur = conn.cursor()
    # Overwrite per artist: delete then insert
    artist_names = tuple(r[0] for r in rows)
    if len(artist_names) == 1:
        cur.execute("DELETE FROM RAW_SPOTIFY_RELEASES WHERE ARTIST_NAME = %s", (artist_names[0],))
    else:
        cur.execute(f"DELETE FROM RAW_SPOTIFY_RELEASES WHERE ARTIST_NAME IN {artist_names}")
    cur.executemany("""
        INSERT INTO RAW_SPOTIFY_RELEASES
            (ARTIST_NAME, ARTIST_SPOTIFY_URL, LATEST_RELEASE_TITLE,
             RELEASE_TYPE, RELEASE_DATE, LOADED_AT)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, rows)
    conn.commit()
    cur.close()
    print(f"Loaded {len(rows)} release records into RAW_SPOTIFY_RELEASES")


def main():
    print("Starting Spotify release scraping...")
    conn = get_snowflake_connection()
    try:
        artist_urls = get_artist_urls(conn)
        print(f"Found {len(artist_urls)} artists to scrape")

        rows = []
        loaded_at = datetime.now(timezone.utc).isoformat()

        for artist_name, spotify_url in artist_urls:
            print(f"  Scraping {artist_name}...")
            markdown = scrape_artist_page(spotify_url)
            release = parse_release(markdown or "")
            if release:
                # Use Jan 1 of the release year as the date (year is all Spotify exposes)
                release_date = f"{release['release_year']}-01-01"
                rows.append((
                    artist_name,
                    spotify_url,
                    release["title"],
                    release["release_type"],
                    release_date,
                    loaded_at,
                ))
                print(f"    → {release['title']} ({release['release_type']}, {release['release_year']})")
            else:
                print(f"    → No release found")

        load_releases(conn, rows)
        print("Spotify release scraping complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the parse_release tests**

```bash
cd ~/isba-4715/bi-analyst-entertainment && source venv/bin/activate && pytest tests/test_parsers.py::test_parse_release_date_album tests/test_parsers.py::test_parse_release_date_single tests/test_parsers.py::test_parse_release_returns_none_on_empty tests/test_parsers.py::test_parse_release_returns_none_on_no_match -v
```

Expected: All 4 pass.

- [ ] **Step 3: Commit**

```bash
cd ~/isba-4715/bi-analyst-entertainment && git add src/scrape_spotify_releases.py tests/ && git commit -m "feat: add Spotify release scraper and parser unit tests"
```

---

### Task 4: Create `src/scrape_venue_capacity.py`

Uses the SeatGeek API (already authenticated in the project) to fetch venue capacity — no Firecrawl needed.

**Files:**
- Create: `src/scrape_venue_capacity.py`

- [ ] **Step 1: Create the scraper**

```python
"""
Fetch venue capacity from SeatGeek API for venues in DIM_VENUES.
Loads into RAW_VENUE_CAPACITY (one row per venue, overwrites previous).
"""
import os
import requests
import snowflake.connector
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

SEATGEEK_CLIENT_ID = os.getenv("SEATGEEK_CLIENT_ID")
BASE_URL = "https://api.seatgeek.com/2"


def get_venue_tier(capacity: int) -> str:
    """
    Bucket a venue capacity into a tier label.
    club: <1000, theater: 1000-4999, amphitheater: 5000-19999, arena: 20000+
    """
    if capacity < 1000:
        return "club"
    elif capacity < 5000:
        return "theater"
    elif capacity < 20000:
        return "amphitheater"
    else:
        return "arena"


def fetch_venue_capacity(venue_name: str, city: str, state: str) -> dict | None:
    """Search SeatGeek for a venue and return its capacity data."""
    try:
        r = requests.get(f"{BASE_URL}/venues", params={
            "client_id": SEATGEEK_CLIENT_ID,
            "q": venue_name,
            "city": city,
            "per_page": 1,
        })
        r.raise_for_status()
        venues = r.json().get("venues", [])
        if not venues:
            return None
        v = venues[0]
        capacity = v.get("capacity")
        if not capacity or capacity == 0:
            return None
        return {
            "venue_name": venue_name,
            "city": city,
            "state": state,
            "capacity": capacity,
            "venue_tier": get_venue_tier(capacity),
            "sg_venue_id": str(v.get("id", "")),
        }
    except Exception as e:
        print(f"  Error fetching capacity for {venue_name}: {e}")
        return None


def get_venues(conn) -> list[tuple[str, str, str]]:
    """Fetch unique venues from DIM_VENUES."""
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT VENUE_NAME, CITY, STATE
        FROM RAW_MARTS.DIM_VENUES
        WHERE VENUE_NAME IS NOT NULL AND CITY IS NOT NULL
        ORDER BY VENUE_NAME
    """)
    rows = cur.fetchall()
    cur.close()
    return [(row[0], row[1], row[2]) for row in rows]


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def load_capacities(conn, rows: list[tuple]):
    if not rows:
        print("No venue capacity data to load.")
        return
    cur = conn.cursor()
    cur.execute("DELETE FROM RAW_VENUE_CAPACITY")
    cur.executemany("""
        INSERT INTO RAW_VENUE_CAPACITY
            (VENUE_NAME, CITY, STATE, CAPACITY, VENUE_TIER, SG_VENUE_ID, LOADED_AT)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, rows)
    conn.commit()
    cur.close()
    print(f"Loaded {len(rows)} venue capacity records")


def main():
    print("Starting venue capacity scraping...")
    conn = get_snowflake_connection()
    try:
        venues = get_venues(conn)
        print(f"Found {len(venues)} venues to look up")

        rows = []
        loaded_at = datetime.now(timezone.utc).isoformat()

        for venue_name, city, state in venues:
            print(f"  Looking up {venue_name} ({city}, {state})...")
            data = fetch_venue_capacity(venue_name, city, state)
            if data:
                rows.append((
                    data["venue_name"],
                    data["city"],
                    data["state"],
                    data["capacity"],
                    data["venue_tier"],
                    data["sg_venue_id"],
                    loaded_at,
                ))
                print(f"    → capacity={data['capacity']}, tier={data['venue_tier']}")
            else:
                print(f"    → not found on SeatGeek")

        load_capacities(conn, rows)
        print("Venue capacity scraping complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run venue tier tests**

```bash
cd ~/isba-4715/bi-analyst-entertainment && source venv/bin/activate && pytest tests/test_parsers.py::test_venue_tier_arena tests/test_parsers.py::test_venue_tier_amphitheater tests/test_parsers.py::test_venue_tier_theater tests/test_parsers.py::test_venue_tier_club tests/test_parsers.py::test_venue_tier_boundary_theater_low tests/test_parsers.py::test_venue_tier_boundary_amphitheater_low -v
```

Expected: All 6 pass.

- [ ] **Step 3: Commit**

```bash
cd ~/isba-4715/bi-analyst-entertainment && git add src/scrape_venue_capacity.py && git commit -m "feat: add venue capacity scraper using SeatGeek API"
```

---

### Task 5: Create `src/scrape_tour_calendar.py`

**Files:**
- Create: `src/scrape_tour_calendar.py`

- [ ] **Step 1: Create the scraper**

```python
"""
Scrape announced tour dates from Bandsintown artist pages via Firecrawl.
Loads into RAW_TOUR_CALENDAR (overwrites per artist on each run).
"""
import os
import re
import snowflake.connector
from dotenv import load_dotenv
from firecrawl import V1FirecrawlApp as FirecrawlApp
from datetime import datetime, timezone

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

# Bandsintown URL pattern: https://www.bandsintown.com/a/artist-name
BANDSINTOWN_BASE = "https://www.bandsintown.com/a"

# Month abbreviation → number
MONTH_MAP = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12",
}


def parse_events(markdown: str, artist_name: str) -> list[dict]:
    """
    Parse Bandsintown page markdown into a list of event dicts.

    Bandsintown renders events as:
    **Mon Month DD, YYYY** — Venue Name, City, ST [Get Tickets](url)

    Returns list of dicts with keys:
    artist_name, event_date, venue_name, city, state, ticket_url
    """
    if not markdown:
        return []

    # Pattern: Month DD, YYYY — Venue, City, ST
    pattern = (
        r"\*\*\w+\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"\s+(\d{1,2}),\s+(\d{4})\*\*"
        r"\s*[—-]\s*"
        r"([^,\n]+),\s*([^,\n]+),\s*([A-Z]{2})"
        r".*?\[Get Tickets\]\((https?://[^\)]+)\)"
    )

    events = []
    for match in re.finditer(pattern, markdown):
        month_abbr, day, year, venue, city, state, ticket_url = match.groups()
        month = MONTH_MAP.get(month_abbr, "01")
        day_padded = day.zfill(2)
        event_date = f"{year}-{month}-{day_padded}"
        events.append({
            "artist_name": artist_name,
            "event_date": event_date,
            "venue_name": venue.strip(),
            "city": city.strip(),
            "state": state.strip(),
            "ticket_url": ticket_url.strip(),
        })
    return events


def bandsintown_url(artist_name: str) -> str:
    """Build Bandsintown URL for an artist name."""
    slug = artist_name.lower().replace(" ", "-").replace("&", "and")
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    return f"{BANDSINTOWN_BASE}/{slug}"


def scrape_artist_events(artist_name: str) -> list[dict]:
    """Scrape Bandsintown for an artist's upcoming events."""
    url = bandsintown_url(artist_name)
    try:
        result = app.scrape_url(url, formats=["markdown"])
        markdown = result.markdown if result else ""
        return parse_events(markdown or "", artist_name)
    except Exception as e:
        print(f"  Firecrawl error for {artist_name}: {e}")
        return []


def get_artist_names(conn) -> list[str]:
    """Fetch artist names from Snowflake."""
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ARTIST_NAME
        FROM RAW_SPOTIFY_ARTISTS
        WHERE ARTIST_NAME IS NOT NULL
        ORDER BY ARTIST_NAME
    """)
    rows = cur.fetchall()
    cur.close()
    return [row[0] for row in rows]


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def load_calendar(conn, rows: list[tuple], artist_names: list[str]):
    """Delete existing records for these artists and insert fresh data."""
    if not rows:
        print("No tour calendar data to load.")
        return
    cur = conn.cursor()
    names_tuple = tuple(artist_names)
    if len(names_tuple) == 1:
        cur.execute("DELETE FROM RAW_TOUR_CALENDAR WHERE ARTIST_NAME = %s", (names_tuple[0],))
    else:
        cur.execute(f"DELETE FROM RAW_TOUR_CALENDAR WHERE ARTIST_NAME IN {names_tuple}")
    cur.executemany("""
        INSERT INTO RAW_TOUR_CALENDAR
            (ARTIST_NAME, EVENT_DATE, VENUE_NAME, CITY, STATE, TICKET_URL, SOURCE, LOADED_AT)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)
    conn.commit()
    cur.close()
    print(f"Loaded {len(rows)} tour calendar records")


def main():
    print("Starting Bandsintown tour calendar scraping...")
    conn = get_snowflake_connection()
    try:
        artist_names = get_artist_names(conn)
        print(f"Found {len(artist_names)} artists to scrape")

        all_rows = []
        loaded_at = datetime.now(timezone.utc).isoformat()

        for artist_name in artist_names:
            print(f"  Scraping {artist_name}...")
            events = scrape_artist_events(artist_name)
            for e in events:
                all_rows.append((
                    e["artist_name"],
                    e["event_date"],
                    e["venue_name"],
                    e["city"],
                    e["state"],
                    e["ticket_url"],
                    "bandsintown",
                    loaded_at,
                ))
            print(f"    → {len(events)} upcoming events found")

        load_calendar(conn, all_rows, artist_names)
        print("Bandsintown tour calendar scraping complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run tour calendar tests**

```bash
cd ~/isba-4715/bi-analyst-entertainment && source venv/bin/activate && pytest tests/test_parsers.py::test_parse_bandsintown_events_basic tests/test_parsers.py::test_parse_bandsintown_events_empty tests/test_parsers.py::test_parse_bandsintown_events_returns_list -v
```

Expected: All 3 pass.

- [ ] **Step 3: Run full test suite**

```bash
cd ~/isba-4715/bi-analyst-entertainment && source venv/bin/activate && pytest tests/test_parsers.py -v
```

Expected: All 13 tests pass.

- [ ] **Step 4: Commit**

```bash
cd ~/isba-4715/bi-analyst-entertainment && git add src/scrape_tour_calendar.py && git commit -m "feat: add Bandsintown tour calendar scraper"
```

---

### Task 6: Create dbt Staging Models

**Files:**
- Create: `dbt_project/models/staging/stg_spotify_releases.sql`
- Create: `dbt_project/models/staging/stg_spotify_artists_history.sql`
- Create: `dbt_project/models/staging/stg_seatgeek_velocity.sql`
- Create: `dbt_project/models/staging/stg_venue_capacity.sql`
- Create: `dbt_project/models/staging/stg_tour_calendar.sql`

- [ ] **Step 1: Create `stg_spotify_releases.sql`**

```sql
-- One row per artist: their latest known release.
-- Release date is approximated as Jan 1 of the release year
-- (Spotify pages expose year only, not exact date).
with source as (
    select *,
        row_number() over (partition by artist_name order by loaded_at desc) as _rn
    from {{ source('raw', 'raw_spotify_releases') }}
),

deduped as (
    select * from source where _rn = 1
)

select
    trim(initcap(artist_name))          as artist_name,
    trim(artist_spotify_url)            as artist_spotify_url,
    trim(latest_release_title)          as latest_release_title,
    trim(initcap(release_type))         as release_type,
    cast(release_date as date)          as release_date,
    datediff('day', release_date, current_date()) as days_since_release,
    case
        when datediff('day', release_date, current_date()) <= 90 then true
        else false
    end                                 as is_recent_release,
    cast(loaded_at as timestamp_tz)     as loaded_at
from deduped
where release_date is not null
```

- [ ] **Step 2: Create `stg_spotify_artists_history.sql`**

```sql
-- Full time series of Spotify listener counts — one row per artist per day.
-- Used for listener growth rate calculations and Career Arc charts.
-- Unlike stg_spotify_artists, this model does NOT deduplicate.
select
    trim(initcap(artist_name))          as artist_name,
    cast(monthly_listeners as integer)  as monthly_listeners,
    cast(loaded_at as timestamp_tz)     as loaded_at,
    cast(loaded_at as date)             as snapshot_date
from {{ source('raw', 'raw_spotify_artists') }}
where monthly_listeners is not null
  and artist_name is not null
```

- [ ] **Step 3: Create `stg_seatgeek_velocity.sql`**

```sql
-- Day-over-day changes in SeatGeek listing_count and event_score per event.
-- listing_velocity > 0 = demand building (more listings appearing).
-- score_velocity > 0 = event gaining traction on SeatGeek.
-- price_gap_ratio = resale avg / TM avg ticket (computed in dashboard, not here).
with snapshots as (
    select
        cast(event_id as varchar)           as event_id,
        trim(initcap(performer_name))       as performer_name,
        cast(listing_count as integer)      as listing_count,
        cast(event_score as float)          as event_score,
        cast(average_price as float)        as average_price,
        cast(loaded_at as timestamp_tz)     as loaded_at,
        cast(loaded_at as date)             as snapshot_date
    from {{ source('raw', 'raw_seatgeek_events') }}
    where event_id is not null
),

with_velocity as (
    select
        *,
        listing_count - lag(listing_count) over (
            partition by event_id order by loaded_at
        ) as listing_velocity,
        event_score - lag(event_score) over (
            partition by event_id order by loaded_at
        ) as score_velocity
    from snapshots
)

select * from with_velocity
```

- [ ] **Step 4: Create `stg_venue_capacity.sql`**

```sql
-- One row per venue with capacity and tier bucketing.
with source as (
    select *,
        row_number() over (
            partition by venue_name, city, state order by loaded_at desc
        ) as _rn
    from {{ source('raw', 'raw_venue_capacity') }}
),

deduped as (
    select * from source where _rn = 1
)

select
    trim(initcap(venue_name))           as venue_name,
    trim(initcap(city))                 as city,
    trim(upper(state))                  as state,
    cast(capacity as integer)           as capacity,
    trim(lower(venue_tier))             as venue_tier,
    trim(sg_venue_id)                   as sg_venue_id,
    cast(loaded_at as timestamp_tz)     as loaded_at
from deduped
where capacity is not null and capacity > 0
```

- [ ] **Step 5: Create `stg_tour_calendar.sql`**

```sql
-- Announced tour dates from Bandsintown.
-- Labeled as proxy data — does not include unannounced/private bookings.
with source as (
    select *
    from {{ source('raw', 'raw_tour_calendar') }}
    where artist_name is not null
      and event_date is not null
)

select
    trim(initcap(artist_name))          as artist_name,
    cast(event_date as date)            as event_date,
    trim(initcap(venue_name))           as venue_name,
    trim(initcap(city))                 as city,
    trim(upper(state))                  as state,
    trim(ticket_url)                    as ticket_url,
    trim(lower(source))                 as source,
    cast(loaded_at as timestamp_tz)     as loaded_at
from source
where event_date >= current_date()  -- only future events
```

- [ ] **Step 6: Commit**

```bash
cd ~/isba-4715/bi-analyst-entertainment && git add dbt_project/models/staging/stg_spotify_releases.sql dbt_project/models/staging/stg_spotify_artists_history.sql dbt_project/models/staging/stg_seatgeek_velocity.sql dbt_project/models/staging/stg_venue_capacity.sql dbt_project/models/staging/stg_tour_calendar.sql && git commit -m "feat: add 5 new dbt staging models for releases, history, velocity, capacity, calendar"
```

---

### Task 7: Update `sources.yml` and `schema.yml`

**Files:**
- Modify: `dbt_project/models/staging/sources.yml`
- Modify: `dbt_project/models/staging/schema.yml`

- [ ] **Step 1: Add new raw tables to `sources.yml`**

Replace the entire file:

```yaml
version: 2

sources:
  - name: raw
    database: LIVE_MUSIC_DB
    schema: RAW
    tables:
      - name: raw_ticketmaster_events
        description: Raw event data from Ticketmaster Discovery API
      - name: raw_spotify_artists
        description: Raw artist data scraped from Spotify via Firecrawl (appended daily — full history)
      - name: raw_seatgeek_performers
        description: Raw performer popularity data from SeatGeek API
      - name: raw_seatgeek_events
        description: Raw event data from SeatGeek API (appended daily — full history for velocity)
      - name: raw_tour_revenue
        description: Verified tour revenue data from Pollstar, Billboard, Touring Data
      - name: raw_spotify_releases
        description: Latest release title/type/year scraped from Spotify artist pages via Firecrawl
      - name: raw_venue_capacity
        description: Venue capacity data fetched from SeatGeek API
      - name: raw_tour_calendar
        description: Announced tour dates scraped from Bandsintown via Firecrawl (proxy — excludes private bookings)
```

- [ ] **Step 2: Add new models to `schema.yml`**

Append to the existing `schema.yml` (after the last existing model entry):

```yaml
  - name: stg_spotify_releases
    description: Latest release per artist scraped from Spotify. Release date is Jan 1 of release year (Spotify exposes year only).
    columns:
      - name: artist_name
        description: Artist name
        tests:
          - not_null
      - name: latest_release_title
        description: Title of most recent release
        tests:
          - not_null
      - name: release_type
        description: Album, Single, or EP
      - name: is_recent_release
        description: True if release_date is within last 90 days

  - name: stg_spotify_artists_history
    description: Full time series of Spotify monthly listener counts. One row per artist per pipeline run. Used for growth rate and career arc charts.
    columns:
      - name: artist_name
        description: Artist name
        tests:
          - not_null
      - name: monthly_listeners
        description: Monthly listener count at snapshot time
        tests:
          - not_null
      - name: snapshot_date
        description: Date of the pipeline run that produced this row

  - name: stg_seatgeek_velocity
    description: Day-over-day changes in SeatGeek listing_count and event_score. listing_velocity > 0 = demand building. Proxy for primary ticket sales velocity pending Ticketmaster partner API access.
    columns:
      - name: event_id
        description: SeatGeek event identifier
        tests:
          - not_null
      - name: listing_velocity
        description: Change in listing_count since previous snapshot. NULL for first snapshot.
      - name: score_velocity
        description: Change in event_score since previous snapshot. NULL for first snapshot.

  - name: stg_venue_capacity
    description: Venue capacity and tier from SeatGeek API. club <1000, theater 1000-4999, amphitheater 5000-19999, arena 20000+.
    columns:
      - name: venue_name
        description: Venue name
        tests:
          - not_null
      - name: capacity
        description: Maximum venue capacity
        tests:
          - not_null
      - name: venue_tier
        description: club, theater, amphitheater, or arena
        tests:
          - not_null
          - accepted_values:
              values: ['club', 'theater', 'amphitheater', 'arena']

  - name: stg_tour_calendar
    description: Announced upcoming tour dates from Bandsintown. Proxy only — excludes unannounced and private bookings.
    columns:
      - name: artist_name
        description: Artist name
        tests:
          - not_null
      - name: event_date
        description: Date of announced show
        tests:
          - not_null
      - name: city
        description: City of the show
      - name: state
        description: State abbreviation
```

- [ ] **Step 3: Commit**

```bash
cd ~/isba-4715/bi-analyst-entertainment && git add dbt_project/models/staging/sources.yml dbt_project/models/staging/schema.yml && git commit -m "feat: register new raw tables in sources.yml and add schema tests for new models"
```

---

### Task 8: Create GitHub Actions Workflows

**Files:**
- Create: `.github/workflows/scrape_spotify_releases.yml`
- Create: `.github/workflows/scrape_venue_capacity.yml`
- Create: `.github/workflows/scrape_tour_calendar.yml`

- [ ] **Step 1: Create `scrape_spotify_releases.yml`**

```yaml
name: Daily Spotify Release Scraping

on:
  schedule:
    - cron: "0 9 * * *"
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Run Spotify release scraper
        env:
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
          SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
          SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PASSWORD }}
          SNOWFLAKE_WAREHOUSE: ${{ secrets.SNOWFLAKE_WAREHOUSE }}
          SNOWFLAKE_DATABASE: ${{ secrets.SNOWFLAKE_DATABASE }}
          SNOWFLAKE_SCHEMA: ${{ secrets.SNOWFLAKE_SCHEMA }}
        run: python src/scrape_spotify_releases.py
```

- [ ] **Step 2: Create `scrape_venue_capacity.yml`**

```yaml
name: Weekly Venue Capacity Scraping

on:
  schedule:
    - cron: "0 10 * * 0"
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Run venue capacity scraper
        env:
          SEATGEEK_CLIENT_ID: ${{ secrets.SEATGEEK_CLIENT_ID }}
          SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
          SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PASSWORD }}
          SNOWFLAKE_WAREHOUSE: ${{ secrets.SNOWFLAKE_WAREHOUSE }}
          SNOWFLAKE_DATABASE: ${{ secrets.SNOWFLAKE_DATABASE }}
          SNOWFLAKE_SCHEMA: ${{ secrets.SNOWFLAKE_SCHEMA }}
        run: python src/scrape_venue_capacity.py
```

- [ ] **Step 3: Create `scrape_tour_calendar.yml`**

```yaml
name: Daily Tour Calendar Scraping

on:
  schedule:
    - cron: "0 11 * * *"
  workflow_dispatch:

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: pip install -r requirements-dev.txt

      - name: Run tour calendar scraper
        env:
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
          SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
          SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PASSWORD }}
          SNOWFLAKE_WAREHOUSE: ${{ secrets.SNOWFLAKE_WAREHOUSE }}
          SNOWFLAKE_DATABASE: ${{ secrets.SNOWFLAKE_DATABASE }}
          SNOWFLAKE_SCHEMA: ${{ secrets.SNOWFLAKE_SCHEMA }}
        run: python src/scrape_tour_calendar.py
```

- [ ] **Step 4: Commit**

```bash
cd ~/isba-4715/bi-analyst-entertainment && git add .github/workflows/scrape_spotify_releases.yml .github/workflows/scrape_venue_capacity.yml .github/workflows/scrape_tour_calendar.yml && git commit -m "feat: add GitHub Actions workflows for 3 new scrapers"
```

---

### Task 9: Smoke Test All Three Scrapers Locally

Run each scraper against real Snowflake to confirm end-to-end connectivity and basic output before relying on GitHub Actions.

**Prerequisites:** `.env` file must have `FIRECRAWL_API_KEY`, `SEATGEEK_CLIENT_ID`, and all `SNOWFLAKE_*` vars set.

- [ ] **Step 1: Test release scraper (2 artists only)**

Temporarily edit `scrape_spotify_releases.py` — change `get_artist_urls` call to limit to 2 rows for smoke test:

```python
# In main(), replace:
artist_urls = get_artist_urls(conn)
# With:
artist_urls = get_artist_urls(conn)[:2]
```

Run:
```bash
cd ~/isba-4715/bi-analyst-entertainment && source venv/bin/activate && python src/scrape_spotify_releases.py
```

Expected output contains lines like:
```
Found N artists to scrape
  Scraping Zach Bryan...
    → Something in the Orange (Album, 2022)
Loaded 2 release records into RAW_SPOTIFY_RELEASES
```

Verify in Snowsight:
```sql
SELECT * FROM LIVE_MUSIC_DB.RAW.RAW_SPOTIFY_RELEASES LIMIT 5;
```

- [ ] **Step 2: Revert the 2-artist limit**

Remove the `[:2]` slice. Restore original `artist_urls = get_artist_urls(conn)`.

- [ ] **Step 3: Test venue capacity scraper (5 venues only)**

Temporarily edit `scrape_venue_capacity.py` — limit to 5 venues:

```python
# In main(), replace:
venues = get_venues(conn)
# With:
venues = get_venues(conn)[:5]
```

Run:
```bash
python src/scrape_venue_capacity.py
```

Expected: 1–5 rows loaded into `RAW_VENUE_CAPACITY`. Revert the `[:5]` slice.

- [ ] **Step 4: Test tour calendar scraper (2 artists only)**

Temporarily edit `scrape_tour_calendar.py`:

```python
# In main(), replace:
artist_names = get_artist_names(conn)
# With:
artist_names = get_artist_names(conn)[:2]
```

Run:
```bash
python src/scrape_tour_calendar.py
```

Expected: 0–N rows loaded into `RAW_TOUR_CALENDAR`. Revert the `[:2]` slice.

- [ ] **Step 5: Final commit**

```bash
cd ~/isba-4715/bi-analyst-entertainment && git add -A && git commit -m "feat: complete data pipeline additions — scrapers, dbt models, workflows" && git push
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|---|---|
| Release schedule scraper (Firecrawl) | Task 3 |
| `STG_SPOTIFY_RELEASES` table + dbt model | Tasks 1, 6 |
| Historical listener accumulation (append mode) | Already works — raw table appends. Task 6 adds `stg_spotify_artists_history` to expose it |
| Growth rate computation | `stg_spotify_artists_history` provides the time series; growth rate computed in dashboard (Plan B) |
| Artist tier classification | Computed in dashboard (Plan B) — uses data from this plan |
| Resale demand velocity via SeatGeek append | Task 6 `stg_seatgeek_velocity` — raw table already appends |
| `STG_TOUR_CALENDAR` + scraper | Tasks 1, 5, 8 |
| `STG_VENUE_CAPACITY` + scraper | Tasks 1, 4, 7, 8 |
| GitHub Actions for new scrapers | Task 8 |
| Data source transparency | Implemented in dbt model descriptions + dashboard labels (Plan B) |
| Future TM partner API column | Reserved in dashboard (Plan B) |
