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
