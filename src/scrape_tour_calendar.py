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
from cryptography.hazmat.primitives import serialization

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
        r"\*\*(?:\w+\s+)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
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
    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", "/Users/rachelmcdonald/rsa_key.p8")
    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    private_key_bytes = private_key.private_bytes(
        serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=private_key_bytes,
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
