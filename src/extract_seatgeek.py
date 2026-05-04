"""
Source 3: SeatGeek API -> Snowflake RAW
Extracts performer popularity data and event listings from SeatGeek
to complement Ticketmaster (events) and Spotify (streaming) data.
Provides a third demand signal: SeatGeek popularity score.
"""

import os
import requests
import snowflake.connector
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

SEATGEEK_CLIENT_ID = os.getenv("SEATGEEK_CLIENT_ID")
BASE_URL = "https://api.seatgeek.com/2"


def fetch_performers(artist_names):
    """Fetch performer data from SeatGeek for a list of artist names."""
    performers = []
    for name in artist_names:
        try:
            r = requests.get(f"{BASE_URL}/performers", params={
                "client_id": SEATGEEK_CLIENT_ID,
                "q": name,
                "per_page": 1,
            })
            r.raise_for_status()
            data = r.json()
            results = data.get("performers", [])
            if results:
                perf = results[0]
                performers.append(perf)
                print(f"  {perf['name']}: score={perf.get('score')}, popularity={perf.get('popularity')}, events={perf.get('num_upcoming_events')}")
            else:
                print(f"  {name}: not found on SeatGeek")
        except Exception as e:
            print(f"  {name}: error - {e}")
    return performers


def fetch_events_for_performers(performer_ids):
    """Fetch events with pricing for given performer IDs."""
    all_events = []
    for pid in performer_ids:
        try:
            r = requests.get(f"{BASE_URL}/events", params={
                "client_id": SEATGEEK_CLIENT_ID,
                "performers.id": pid,
                "per_page": 100,
            })
            r.raise_for_status()
            events = r.json().get("events", [])
            all_events.extend(events)
        except Exception as e:
            print(f"  Error fetching events for performer {pid}: {e}")
    return all_events


def parse_performers(performers):
    """Parse performer data into rows for Snowflake."""
    rows = []
    for p in performers:
        genres = ", ".join(g.get("name", "") for g in p.get("genres", []))
        rows.append((
            str(p.get("id")),
            p.get("name"),
            p.get("short_name"),
            p.get("url"),
            p.get("score"),
            p.get("popularity"),
            p.get("num_upcoming_events"),
            genres or None,
            p.get("type"),
            datetime.now(timezone.utc).isoformat(),
        ))
    return rows


def parse_events(events):
    """Parse event data into rows for Snowflake."""
    rows = []
    seen = set()
    for e in events:
        eid = str(e.get("id"))
        if eid in seen:
            continue
        seen.add(eid)

        venue = e.get("venue", {})
        stats = e.get("stats", {})
        performers = e.get("performers", [])
        primary = next((p for p in performers if p.get("primary")), performers[0] if performers else {})

        rows.append((
            eid,
            e.get("title"),
            e.get("url"),
            e.get("datetime_local", "")[:10] or None,  # date portion
            e.get("datetime_local", "")[11:] or None,   # time portion
            e.get("type"),
            primary.get("name"),
            str(primary.get("id", "")),
            venue.get("name"),
            str(venue.get("id", "")),
            venue.get("city"),
            venue.get("state"),
            stats.get("lowest_price"),
            stats.get("average_price"),
            stats.get("highest_price"),
            stats.get("listing_count"),
            e.get("popularity"),
            e.get("score"),
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
        CREATE TABLE IF NOT EXISTS RAW_SEATGEEK_PERFORMERS (
            PERFORMER_ID        STRING,
            PERFORMER_NAME      STRING,
            SHORT_NAME          STRING,
            SEATGEEK_URL        STRING,
            SG_SCORE            FLOAT,
            SG_POPULARITY       FLOAT,
            UPCOMING_EVENTS     NUMBER,
            GENRES              STRING,
            PERFORMER_TYPE      STRING,
            LOADED_AT           TIMESTAMP_TZ
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS RAW_SEATGEEK_EVENTS (
            EVENT_ID            STRING,
            EVENT_TITLE         STRING,
            EVENT_URL           STRING,
            EVENT_DATE          STRING,
            EVENT_TIME          STRING,
            EVENT_TYPE          STRING,
            PERFORMER_NAME      STRING,
            PERFORMER_ID        STRING,
            VENUE_NAME          STRING,
            VENUE_ID            STRING,
            CITY                STRING,
            STATE               STRING,
            LOWEST_PRICE        FLOAT,
            AVERAGE_PRICE       FLOAT,
            HIGHEST_PRICE       FLOAT,
            LISTING_COUNT       NUMBER,
            EVENT_POPULARITY    FLOAT,
            EVENT_SCORE         FLOAT,
            LOADED_AT           TIMESTAMP_TZ
        )
    """)
    cur.close()


def load_performers(conn, rows):
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO RAW_SEATGEEK_PERFORMERS
            (PERFORMER_ID, PERFORMER_NAME, SHORT_NAME, SEATGEEK_URL,
             SG_SCORE, SG_POPULARITY, UPCOMING_EVENTS, GENRES,
             PERFORMER_TYPE, LOADED_AT)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)
    conn.commit()
    cur.close()
    print(f"Loaded {len(rows)} performers into RAW_SEATGEEK_PERFORMERS")


def load_events(conn, rows):
    if not rows:
        print("No SeatGeek events to load.")
        return
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO RAW_SEATGEEK_EVENTS
            (EVENT_ID, EVENT_TITLE, EVENT_URL, EVENT_DATE, EVENT_TIME,
             EVENT_TYPE, PERFORMER_NAME, PERFORMER_ID, VENUE_NAME, VENUE_ID,
             CITY, STATE, LOWEST_PRICE, AVERAGE_PRICE, HIGHEST_PRICE,
             LISTING_COUNT, EVENT_POPULARITY, EVENT_SCORE, LOADED_AT)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)
    conn.commit()
    cur.close()
    print(f"Loaded {len(rows)} events into RAW_SEATGEEK_EVENTS")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Starting SeatGeek extraction...")

    # Artists to look up — combine Spotify list + top Ticketmaster artists
    target_artists = [
        "Taylor Swift", "Morgan Wallen", "Drake", "Bad Bunny", "The Weeknd",
        "Billie Eilish", "Kendrick Lamar", "SZA", "Olivia Rodrigo", "Zach Bryan",
        "Beyonce", "Post Malone", "Sabrina Carpenter", "Chappell Roan",
        "Tyler Childers", "Metallica", "Dave Matthews Band", "Chris Stapleton",
        "Bruno Mars", "Phish", "Doja Cat", "Ed Sheeran", "Foo Fighters",
        "Luke Combs", "Riley Green", "Luke Bryan", "Green Day", "Linkin Park",
        "Pearl Jam", "Coldplay", "Adele", "Travis Scott", "Lana Del Rey",
        "Imagine Dragons", "Hozier", "Dua Lipa",
    ]

    print(f"\nFetching performer data for {len(target_artists)} artists...")
    performers = fetch_performers(target_artists)
    performer_rows = parse_performers(performers)

    print(f"\nFetching events for {len(performers)} performers...")
    performer_ids = [p.get("id") for p in performers]
    events = fetch_events_for_performers(performer_ids)
    event_rows = parse_events(events)

    print(f"\nLoading to Snowflake...")
    conn = get_snowflake_connection()
    try:
        setup_snowflake(conn)
        load_performers(conn, performer_rows)
        load_events(conn, event_rows)
        print("SeatGeek extraction complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
