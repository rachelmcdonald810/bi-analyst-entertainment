"""
Fetch venue capacity from SeatGeek API for venues in DIM_VENUES.
Loads into RAW_VENUE_CAPACITY (one row per venue, overwrites previous).
"""
import os
import requests
import snowflake.connector
from dotenv import load_dotenv
from datetime import datetime, timezone
from cryptography.hazmat.primitives import serialization

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
