"""
Source 1: Ticketmaster Discovery API -> Snowflake RAW
Extracts music events from the Ticketmaster API and loads them into Snowflake.
Pulls both upcoming events and past 12 months of events with pagination.
"""

import os
import requests
import snowflake.connector
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

# ── Ticketmaster API ──────────────────────────────────────────────────────────

TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY")
BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


def fetch_events_page(params):
    """Fetch a single page of events from the API."""
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    events = data.get("_embedded", {}).get("events", [])
    page_info = data.get("page", {})
    return events, page_info


def fetch_all_events():
    """Fetch music events: broad search + targeted artist searches."""
    all_events = []
    now = datetime.now(timezone.utc)
    one_year_ago = now - timedelta(days=365)

    # ── Part 1: Broad music search with date ranges ──────────────────────────
    date_ranges = [
        (one_year_ago, one_year_ago + timedelta(days=90)),
        (one_year_ago + timedelta(days=90), one_year_ago + timedelta(days=180)),
        (one_year_ago + timedelta(days=180), one_year_ago + timedelta(days=270)),
        (one_year_ago + timedelta(days=270), now),
        (now, now + timedelta(days=180)),
    ]

    print("Fetching broad music events...")
    for start_dt, end_dt in date_ranges:
        start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        for page in range(5):
            params = {
                "apikey": TICKETMASTER_API_KEY,
                "classificationName": "Music",
                "size": 200,
                "page": page,
                "sort": "date,asc",
                "countryCode": "US",
                "startDateTime": start_str,
                "endDateTime": end_str,
            }
            try:
                events, page_info = fetch_events_page(params)
                if not events:
                    break
                all_events.extend(events)
                total_pages = page_info.get("totalPages", 0)
                print(f"  {start_dt.date()} to {end_dt.date()}, page {page + 1}/{total_pages}: {len(events)} events")
                if page + 1 >= total_pages:
                    break
            except Exception as e:
                print(f"  Error on page {page}: {e}")
                break

    # ── Part 2: Targeted search for high-profile artists ─────────────────────
    target_artists = [
        "Morgan Wallen", "Post Malone", "Zach Bryan", "Tyler Childers",
        "Drake", "Bad Bunny", "The Weeknd", "Billie Eilish", "Kendrick Lamar",
        "SZA", "Olivia Rodrigo", "Beyonce", "Taylor Swift", "Sabrina Carpenter",
        "Chappell Roan", "Luke Combs", "Chris Stapleton", "Hozier",
        "Dua Lipa", "Ed Sheeran", "Coldplay", "Bruno Mars", "Adele",
        "Travis Scott", "Lana Del Rey", "Doja Cat", "Tyler The Creator",
        "Imagine Dragons", "Green Day", "Linkin Park", "Metallica",
        "Foo Fighters", "Pearl Jam", "Dave Matthews Band", "Phish",
    ]

    print(f"\nFetching events for {len(target_artists)} target artists...")
    for artist in target_artists:
        for page in range(3):
            params = {
                "apikey": TICKETMASTER_API_KEY,
                "keyword": artist,
                "classificationName": "Music",
                "size": 200,
                "page": page,
                "countryCode": "US",
            }
            try:
                events, page_info = fetch_events_page(params)
                if not events:
                    break
                all_events.extend(events)
                total_pages = page_info.get("totalPages", 0)
                print(f"  {artist}: page {page + 1}/{total_pages}, {len(events)} events")
                if page + 1 >= total_pages:
                    break
            except Exception as e:
                print(f"  Error for {artist}: {e}")
                break

    # Deduplicate by event ID
    seen = set()
    unique_events = []
    for event in all_events:
        eid = event.get("id")
        if eid and eid not in seen:
            seen.add(eid)
            unique_events.append(event)

    print(f"\nFetched {len(unique_events)} unique events total")
    return unique_events


def parse_events(raw_events):
    """Flatten raw event JSON into rows for Snowflake."""
    rows = []
    for event in raw_events:
        venues = event.get("_embedded", {}).get("venues", [{}])
        venue = venues[0] if venues else {}

        attractions = event.get("_embedded", {}).get("attractions", [{}])
        artist = attractions[0] if attractions else {}

        price_ranges = event.get("priceRanges", [{}])
        price = price_ranges[0] if price_ranges else {}

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
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def setup_snowflake(conn):
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
    print("Starting Ticketmaster extraction (past 12 months + upcoming)...")
    raw_events = fetch_all_events()
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
