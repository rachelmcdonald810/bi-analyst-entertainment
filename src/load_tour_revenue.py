"""
Load verified tour revenue data into Snowflake.
Sources: Pollstar, Billboard Boxscore, Touring Data.
"""

import os
import snowflake.connector
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

# Verified tour revenue data from industry sources
TOUR_DATA = [
    # (artist, tour_name, gross_revenue, tickets_sold, avg_ticket_price, shows, year, source)
    ("Taylor Swift", "Eras Tour", 2200000000, 10060000, 219, 149, "2023-2024", "Pollstar"),
    ("Morgan Wallen", "One Night At A Time Tour", 260400000, 3100000, 212, 87, "2023-2024", "Billboard Boxscore"),
    ("Post Malone", "F-1 Trillion Tour", 63000000, 470000, 134, 25, "2024", "Billboard Boxscore"),
    ("Metallica", "M72 World Tour", 517500000, 4230000, 120, 70, "2023-2025", "Pollstar"),
    ("Bruno Mars", "Park MGM Residency", 197200000, 574000, 344, 110, "2022-2026", "Billboard Boxscore"),
    ("Ed Sheeran", "Mathematics Tour", 875700000, 8800000, 100, 188, "2022-2025", "Billboard Boxscore"),
    ("Olivia Rodrigo", "GUTS World Tour", 209100000, 1600000, 131, 101, "2024", "Billboard Boxscore"),
    ("Beyonce", "Renaissance World Tour", 579800000, 2800000, 207, 56, "2023", "Pollstar"),
    ("Dave Matthews Band", "Summer Tour 2023", 52000000, 1000000, 52, 45, "2023", "Pollstar"),
    ("Zach Bryan", "Quittin Time Tour", 379200000, 1920000, 198, 81, "2024", "Touring Data"),
    ("Foo Fighters", "Everything Or Nothing At All Tour", 103500000, 862523, 120, 31, "2024", "Pollstar"),
    ("Chris Stapleton", "All-American Road Show", 224300000, 2000000, 112, 333, "2017-2023", "Billboard"),
    ("Doja Cat", "The Scarlet Tour", 67200000, 383017, 175, 31, "2023-2024", "Billboard Boxscore"),
    ("Luke Combs", "Growin Up And Gettin Old Tour", 164900000, 1238820, 133, 25, "2024", "Touring Data"),
    ("Billie Eilish", "Hit Me Hard And Soft Tour", 190000000, 1200000, 152, 70, "2024-2025", "Pollstar"),
    ("Kendrick Lamar", "The Big Steppers Tour", 110900000, 929000, 119, 73, "2022-2023", "Touring Data"),
    ("Drake", "Its All A Blur Tour", 320500000, 1300000, 247, 80, "2023-2024", "Billboard Boxscore"),
    ("Bad Bunny", "Most Wanted Tour", 210900000, 753287, 280, 49, "2024", "Pollstar"),
    ("SZA", "SOS Tour", 95500000, 674000, 142, 50, "2023", "Billboard Boxscore"),
    ("Sabrina Carpenter", "Short N Sweet Tour", 126600000, 974467, 130, 72, "2024-2025", "Touring Data"),
]


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


def main():
    print("Loading tour revenue reference data...")
    conn = get_snowflake_connection()
    cur = conn.cursor()

    cur.execute("CREATE DATABASE IF NOT EXISTS LIVE_MUSIC_DB")
    cur.execute("USE DATABASE LIVE_MUSIC_DB")
    cur.execute("CREATE SCHEMA IF NOT EXISTS RAW")
    cur.execute("USE SCHEMA RAW")

    cur.execute("""
        CREATE OR REPLACE TABLE RAW_TOUR_REVENUE (
            ARTIST_NAME         STRING,
            TOUR_NAME           STRING,
            GROSS_REVENUE       NUMBER,
            TICKETS_SOLD        NUMBER,
            AVG_TICKET_PRICE    NUMBER,
            SHOWS               NUMBER,
            TOUR_YEAR           STRING,
            SOURCE              STRING,
            LOADED_AT           TIMESTAMP_TZ
        )
    """)

    now = datetime.now(timezone.utc).isoformat()
    rows = [(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], now) for r in TOUR_DATA]

    cur.executemany("""
        INSERT INTO RAW_TOUR_REVENUE
            (ARTIST_NAME, TOUR_NAME, GROSS_REVENUE, TICKETS_SOLD,
             AVG_TICKET_PRICE, SHOWS, TOUR_YEAR, SOURCE, LOADED_AT)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)
    conn.commit()
    cur.close()
    conn.close()
    print(f"Loaded {len(rows)} tour revenue records.")


if __name__ == "__main__":
    main()
