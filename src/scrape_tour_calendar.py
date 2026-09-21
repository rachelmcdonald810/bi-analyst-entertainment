"""
Fetch upcoming tour dates from Ticketmaster Discovery API.
Loads into RAW_TOUR_CALENDAR (overwrites per artist on each run).
"""
import os
import requests
import snowflake.connector
from dotenv import load_dotenv
from datetime import datetime, timezone
from cryptography.hazmat.primitives import serialization

load_dotenv()

TM_API_KEY = os.getenv("TICKETMASTER_API_KEY")
TM_BASE_URL = "https://app.ticketmaster.com/discovery/v2/events.json"


def parse_tm_events(data: dict, artist_name: str) -> list[dict]:
    """
    Parse Ticketmaster Discovery API response into event dicts.

    Returns list of dicts with keys:
    artist_name, event_date, venue_name, city, state, ticket_url
    """
    events_raw = data.get("_embedded", {}).get("events", [])
    events = []
    for e in events_raw:
        event_date = e.get("dates", {}).get("start", {}).get("localDate")
        if not event_date:
            continue
        venues = e.get("_embedded", {}).get("venues", [])
        venue = venues[0] if venues else {}
        events.append({
            "artist_name": artist_name,
            "event_date": event_date,
            "venue_name": venue.get("name", ""),
            "city": venue.get("city", {}).get("name", ""),
            "state": venue.get("state", {}).get("stateCode", ""),
            "ticket_url": e.get("url", ""),
        })
    return events


def fetch_artist_events(artist_name: str) -> list[dict]:
    """Fetch upcoming events from Ticketmaster Discovery API."""
    try:
        r = requests.get(TM_BASE_URL, params={
            "apikey": TM_API_KEY,
            "keyword": artist_name,
            "classificationName": "music",
            "size": 50,
        })
        r.raise_for_status()
        return parse_tm_events(r.json(), artist_name)
    except Exception as e:
        print(f"  TM API error for {artist_name}: {e}")
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
    key_content = os.getenv("SNOWFLAKE_PRIVATE_KEY")
    if key_content:
        pem = key_content.encode()
    else:
        key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", "/Users/rachelmcdonald/rsa_key.p8")
        with open(key_path, "rb") as f:
            pem = f.read()
    private_key = serialization.load_pem_private_key(pem, password=None)
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
    print("Starting Ticketmaster tour calendar fetch...")
    conn = get_snowflake_connection()
    try:
        artist_names = get_artist_names(conn)
        print(f"Found {len(artist_names)} artists to fetch")

        all_rows = []
        loaded_at = datetime.now(timezone.utc).isoformat()

        for artist_name in artist_names:
            print(f"  Fetching {artist_name}...")
            events = fetch_artist_events(artist_name)
            for e in events:
                all_rows.append((
                    e["artist_name"],
                    e["event_date"],
                    e["venue_name"],
                    e["city"],
                    e["state"],
                    e["ticket_url"],
                    "ticketmaster",
                    loaded_at,
                ))
            print(f"    -> {len(events)} upcoming events found")

        load_calendar(conn, all_rows, artist_names)
        print("Ticketmaster tour calendar fetch complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
