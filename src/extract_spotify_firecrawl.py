"""
Source 2: Spotify artist pages via Firecrawl -> Snowflake RAW
Scrapes Spotify artist pages using the Firecrawl API and loads artist
popularity and metadata into Snowflake.
"""

import os
import json
import re
import snowflake.connector
from dotenv import load_dotenv
from firecrawl import V1FirecrawlApp as FirecrawlApp
from datetime import datetime, timezone

load_dotenv()

# ── Firecrawl Setup ───────────────────────────────────────────────────────────

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

# Top artists to scrape — chosen for live touring relevance
ARTIST_URLS = [
    ("Taylor Swift", "https://open.spotify.com/artist/06HL4z0CvFAxyc27GXpf02"),
    ("Morgan Wallen", "https://open.spotify.com/artist/4oUHIQIBe0LHzYfvXNW4QM"),
    ("Drake", "https://open.spotify.com/artist/3TVXtAsR1Inumwj472S9r4"),
    ("Bad Bunny", "https://open.spotify.com/artist/4q3ewBCX7sLwd24euuV69X"),
    ("The Weeknd", "https://open.spotify.com/artist/1Xyo4u8uXC1ZmMpatF05PJ"),
    ("Billie Eilish", "https://open.spotify.com/artist/6qqNVTkY8uBg9cP3Jd7DAH"),
    ("Kendrick Lamar", "https://open.spotify.com/artist/2YZyLoL8N0Wb9xBt1NhZWg"),
    ("SZA", "https://open.spotify.com/artist/7tYKF4w9nC0nq9CsPZTHyP"),
    ("Olivia Rodrigo", "https://open.spotify.com/artist/1McMsnEElThX1knmY4oliG"),
    ("Zach Bryan", "https://open.spotify.com/artist/40ZNYROS4zLfyyBSs2PGe2"),
    ("Beyonce", "https://open.spotify.com/artist/6vWDO969PvNqNYHIOW5v0m"),
    ("Post Malone", "https://open.spotify.com/artist/246dkjvS1zLTtiykXe5h60"),
    ("Sabrina Carpenter", "https://open.spotify.com/artist/74KM79TiuVKeVCqs8QtB0B"),
    ("Chappell Roan", "https://open.spotify.com/artist/7GlBOeep6PqTfFi59PTUUN"),
    ("Tyler Childers", "https://open.spotify.com/artist/5K8mNMsW3wUZxJwCnuqqde"),
]


def scrape_artist(artist_name, url):
    """Scrape a Spotify artist page using Firecrawl."""
    print(f"Scraping {artist_name}...")
    try:
        result = app.scrape_url(url, formats=["markdown"])
        return result
    except Exception as e:
        print(f"  Error scraping {artist_name}: {e}")
        return None


def parse_monthly_listeners(markdown_text):
    """Extract monthly listener count from scraped markdown."""
    if not markdown_text:
        return None
    match = re.search(r"([\d,]+)\s*monthly\s*listeners", markdown_text, re.IGNORECASE)
    if match:
        return int(match.group(1).replace(",", ""))
    return None


def parse_scraped_data(artist_name, url, result):
    """Parse Firecrawl result into a row for Snowflake."""
    if not result:
        return None

    markdown = result.markdown or ""
    metadata = result.metadata if result.metadata else {}
    if not isinstance(metadata, dict):
        metadata = metadata.model_dump() if hasattr(metadata, "model_dump") else {}

    monthly_listeners = parse_monthly_listeners(markdown)

    # Extract artist description/bio from the page title or metadata
    page_title = result.title or metadata.get("title", "")
    page_description = metadata.get("description", "")

    return (
        url.split("/")[-1],  # Spotify artist ID from URL
        artist_name,
        url,
        monthly_listeners,
        page_title,
        page_description,
        markdown[:5000] if markdown else None,  # Store first 5000 chars of raw markdown
        json.dumps(metadata) if metadata else None,
        datetime.now(timezone.utc).isoformat(),
    )


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
        CREATE TABLE IF NOT EXISTS RAW_SPOTIFY_ARTISTS (
            ARTIST_ID           STRING,
            ARTIST_NAME         STRING,
            SPOTIFY_URL         STRING,
            MONTHLY_LISTENERS   NUMBER,
            PAGE_TITLE          STRING,
            PAGE_DESCRIPTION    STRING,
            RAW_MARKDOWN        STRING,
            RAW_METADATA        STRING,
            LOADED_AT           TIMESTAMP_TZ
        )
    """)
    cur.close()


def load_to_snowflake(conn, rows):
    """Insert parsed artist rows into Snowflake."""
    cur = conn.cursor()
    cur.executemany("""
        INSERT INTO RAW_SPOTIFY_ARTISTS
            (ARTIST_ID, ARTIST_NAME, SPOTIFY_URL, MONTHLY_LISTENERS,
             PAGE_TITLE, PAGE_DESCRIPTION, RAW_MARKDOWN, RAW_METADATA, LOADED_AT)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)
    conn.commit()
    cur.close()
    print(f"Loaded {len(rows)} rows into RAW_SPOTIFY_ARTISTS")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Starting Spotify artist scraping via Firecrawl...")
    rows = []

    for artist_name, url in ARTIST_URLS:
        result = scrape_artist(artist_name, url)
        row = parse_scraped_data(artist_name, url, result)
        if row:
            rows.append(row)

    if not rows:
        print("No data scraped. Check your Firecrawl API key and network connection.")
        return

    print(f"\nParsed {len(rows)} artists. Loading to Snowflake...")
    conn = get_snowflake_connection()
    try:
        setup_snowflake(conn)
        load_to_snowflake(conn, rows)
        print("Spotify Firecrawl extraction complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
