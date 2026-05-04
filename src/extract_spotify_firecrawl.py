"""
Source 2: Spotify artist pages via Firecrawl -> Snowflake RAW
Scrapes Spotify artist pages using the Firecrawl API and loads artist
popularity and metadata into Snowflake.

Dynamically discovers top artists from Ticketmaster data in Snowflake,
plus a curated list of high-profile touring artists.
"""

import os
import json
import re
import requests
import snowflake.connector
from dotenv import load_dotenv
from firecrawl import V1FirecrawlApp as FirecrawlApp
from datetime import datetime, timezone

load_dotenv()

# ── Firecrawl Setup ───────────────────────────────────────────────────────────

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

# Curated list of high-profile touring artists (guaranteed Spotify presence)
CURATED_ARTISTS = [
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
    # Artists with high event counts in Ticketmaster data
    ("Metallica", "https://open.spotify.com/artist/2ye2Wgw4gimLv2eAKyk1NB"),
    ("Dave Matthews Band", "https://open.spotify.com/artist/2TI7qyDE0QfyOlnbtfDo7L"),
    ("Chris Stapleton", "https://open.spotify.com/artist/4YLtL2PYDjzMIJSAiEHNKi"),
    ("Bruno Mars", "https://open.spotify.com/artist/0du5cEVh5yTK9QJze8zA0C"),
    ("Phish", "https://open.spotify.com/artist/4YPqbAiLCBM9cEsBMgMFya"),
    ("Doja Cat", "https://open.spotify.com/artist/5cj0lLjcoR7YOSnhnX0Po5"),
    ("Ed Sheeran", "https://open.spotify.com/artist/6eUKZXaKkcviH0Ku9w2n3V"),
    ("Foo Fighters", "https://open.spotify.com/artist/7jy3rLJdDQY21OgRLCZ9sD"),
    ("Luke Combs", "https://open.spotify.com/artist/718COspgdWOnwOFpJHRZHS"),
    ("Riley Green", "https://open.spotify.com/artist/1nBAxEKiJKb8Hu5MfBLjSH"),
    ("Luke Bryan", "https://open.spotify.com/artist/0BvkDsjIUla7X0k6CSWh1I"),
    ("Soulja Boy", "https://open.spotify.com/artist/7c4V3MRqsFKCmNqFHXVByj"),
    ("Boys Like Girls", "https://open.spotify.com/artist/68aMD6TLRYlRbi0HgkSUoX"),
    ("Sepultura", "https://open.spotify.com/artist/09kPFq6SHHPvaQnCjSCKtH"),
    ("Danny Brown", "https://open.spotify.com/artist/2fGfRomjBWPMV0lMeDp4mV"),
]

# Spotify Search API (public, no auth needed)
SPOTIFY_SEARCH_URL = "https://open.spotify.com/search"


def get_top_ticketmaster_artists(conn, limit=50):
    """Get the most frequent artists from Ticketmaster events in Snowflake."""
    cur = conn.cursor()
    cur.execute(f"""
        SELECT ARTIST_NAME, COUNT(*) as event_count
        FROM RAW_TICKETMASTER_EVENTS
        WHERE ARTIST_NAME IS NOT NULL
          AND ARTIST_NAME != ''
        GROUP BY ARTIST_NAME
        ORDER BY event_count DESC
        LIMIT {limit}
    """)
    artists = [(row[0], row[1]) for row in cur.fetchall()]
    cur.close()
    print(f"Found {len(artists)} unique artists in Ticketmaster data")
    return artists


def search_spotify_artist(artist_name):
    """Search for an artist's Spotify URL using Spotify's public web search."""
    # Use a simple approach: construct the likely Spotify search URL
    # and use Firecrawl to find the artist page
    try:
        search_url = f"https://open.spotify.com/search/{requests.utils.quote(artist_name)}"
        result = app.scrape_url(search_url, formats=["markdown"])
        if result and result.markdown:
            # Look for artist profile links in the scraped content
            match = re.search(r"https://open\.spotify\.com/artist/([a-zA-Z0-9]+)", result.markdown)
            if match:
                return f"https://open.spotify.com/artist/{match.group(1)}"
    except Exception as e:
        print(f"  Could not search Spotify for {artist_name}: {e}")
    return None


def scrape_artist(artist_name, url):
    """Scrape a Spotify artist page using Firecrawl."""
    print(f"  Scraping {artist_name}...")
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

    page_title = result.title or metadata.get("title", "")
    page_description = metadata.get("description", "")

    return (
        url.split("/")[-1],
        artist_name,
        url,
        monthly_listeners,
        page_title,
        page_description,
        markdown[:5000] if markdown else None,
        json.dumps(metadata) if metadata else None,
        datetime.now(timezone.utc).isoformat(),
    )


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

    conn = get_snowflake_connection()
    try:
        setup_snowflake(conn)

        # Build artist URL list: curated + top Ticketmaster artists
        artist_urls = dict(CURATED_ARTISTS)  # name -> url
        curated_names = {name.lower() for name, _ in CURATED_ARTISTS}

        # Get top artists from Ticketmaster data
        tm_artists = get_top_ticketmaster_artists(conn, limit=50)

        # For TM artists not in curated list, try to find their Spotify URL
        print(f"\nSearching Spotify for top Ticketmaster artists...")
        for artist_name, event_count in tm_artists:
            if artist_name.lower() not in curated_names and artist_name not in artist_urls:
                url = search_spotify_artist(artist_name)
                if url:
                    artist_urls[artist_name] = url
                    print(f"    Found: {artist_name} ({event_count} events)")

        print(f"\nTotal artists to scrape: {len(artist_urls)}")

        # Scrape all artists
        rows = []
        for artist_name, url in artist_urls.items():
            result = scrape_artist(artist_name, url)
            row = parse_scraped_data(artist_name, url, result)
            if row:
                rows.append(row)

        if not rows:
            print("No data scraped.")
            return

        print(f"\nParsed {len(rows)} artists. Loading to Snowflake...")
        load_to_snowflake(conn, rows)
        print("Spotify Firecrawl extraction complete.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
