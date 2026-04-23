"""
Source 1: Ticketmaster Discovery API -> Snowflake RAW
Extracts music events from the Ticketmaster API and loads them into Snowflake.
"""

import os
import requests
import snowflake.connector
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# ── Ticketmaster API ──────────────────────────────────────────────────────────

TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


def fetch_events(keyword="music", size=200):
    """Fetch music events from Ticketmaster Discovery API."""
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "keyword": keyword,
        "classificationName": "Music",
        "size": min(size, 200),
        "sort": "date,asc",
        "countryCode": "US",
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()

    events = data.get("_embedded", {}).get("events", [])
    print(f"Fetched {len(events)} events from Ticketmaster")
    return events


def parse_events(raw_events):
    """Flatten raw event JSON into rows for Snowflake."""
    rows = []
    for event in raw_events:
        # Extract venue info
        venues = event.get("_embedded", {}).get("venues", [{}])
        venue = venues[0] if venues else {}

        # Extract artist/attraction info
        attractions = event.get("_embedded", {}).get("attractions", [{}])
        artist = attractions[0] if attractions else {}

        # Extract price range
        price_ranges = event.get("priceRanges", [{}])
        price = price_ranges[0] if price_ranges else {}

        # Extract date info
        dates = event.get("dates", {})
        start = dates.get("start", {})

        rows.append((
            event.get("id"),
            event.get("name"),
            event.get("url"),
            start.get("localDate"),
            start.get("localTime"),
            dates.get("status", {}).get("code"),
            artist.get("name"),
            artist.get("id"),
            venue.get("name"),
            venue.get("id"),
            venue.get("city", {}).get("name"),
            venue.get("state", {}).get("stateCode"),
            price.get("min"),
            price.get("max"),
            price.get("currency"),
            event.get("classifications", [{}])[0].get("genre", {}).get("name")
            if event.get("classifications") else None,
            datetime.now(timezone.utc).isoformat(),
        ))
    return rows


# ── Snowflake ─────────────────────────────────────────────────────────────────

def get_snowflake_connection():
    """Create a Snowflake connection using env vars."""
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def setup_snowflake(conn):
    """Create database, schema, and table if they don't exist."""
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS LIVE_MUSIC_DB")
    cur.execute("USE DATABASE LIVE_MUSIC_DB")
    cur.execute("CREATE SCHEMA IF NOT EXISTS RAW")
    cur.execute("USE SCHEMA RAW")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS RAW_TICKETMASTER_EVENTS (
            EVENT_ID            STRING,
            EVENT_NAME          STRING,
            EVENT_URL           STRING,
            EVENT_DATE          STRING,
            EVENT_TIME          STRING,
            SALE_STATUS         STRING,
            ARTIST_NAME         STRING,
            ARTIST_ID           STRING,
            VENUE_NAME          STRING,
            VENUE_ID            STRING,
            CITY                STRING,
            STATE               STRING,
            PRICE_MIN           FLOAT,
            PRICE_MAX           FLOAT,
            CURRENCY            STRING,
            GENRE               STRING,
            LOADED_AT           TIMESTAMP_TZ
        )
    """)
    cur.close()


def load_to_snowflake(conn, rows):
    """Insert parsed event rows into Snowflake."""
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO RAW_TICKETMASTER_EVENTS
            (EVENT_ID, EVENT_NAME, EVENT_URL, EVENT_DATE, EVENT_TIME,
             SALE_STATUS, ARTIST_NAME, ARTIST_ID, VENUE_NAME, VENUE_ID,
             CITY, STATE, PRICE_MIN, PRICE_MAX, CURRENCY, GENRE, LOADED_AT)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)
    conn.commit()
    cur.close()
    print(f"Loaded {len(rows)} rows into RAW_TICKETMASTER_EVENTS")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Starting Ticketmaster extraction...")
    raw_events = fetch_events()
    rows = parse_events(raw_events)

    conn = get_snowflake_connection()
    try:
        setup_snowflake(conn)
        load_to_snowflake(conn, rows)
        print("Ticketmaster extraction complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
