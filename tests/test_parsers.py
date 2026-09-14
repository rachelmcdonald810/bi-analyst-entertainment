"""Unit tests for pipeline parsing functions."""
import pytest
from datetime import date


# ── Release parsing ───────────────────────────────────────────────────────────

def test_parse_release_date_album():
    from src.scrape_spotify_releases import parse_release
    markdown = """
## Discography
### Popular releases
**Short n' Sweet** · Album · 2024
**Emails I Can't Send** · Album · 2022
"""
    result = parse_release(markdown)
    assert result["title"] == "Short n' Sweet"
    assert result["release_type"] == "Album"
    assert result["release_year"] == "2024"


def test_parse_release_date_single():
    from src.scrape_spotify_releases import parse_release
    markdown = """
**Please Please Please** · Single · 2024
"""
    result = parse_release(markdown)
    assert result["title"] == "Please Please Please"
    assert result["release_type"] == "Single"


def test_parse_release_returns_none_on_empty():
    from src.scrape_spotify_releases import parse_release
    result = parse_release("")
    assert result is None


def test_parse_release_returns_none_on_no_match():
    from src.scrape_spotify_releases import parse_release
    result = parse_release("No release information found here.")
    assert result is None


# ── Venue capacity parsing ────────────────────────────────────────────────────

def test_venue_tier_arena():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(25000) == "arena"


def test_venue_tier_amphitheater():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(8000) == "amphitheater"


def test_venue_tier_theater():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(3000) == "theater"


def test_venue_tier_club():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(500) == "club"


def test_venue_tier_boundary_theater_low():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(1000) == "theater"


def test_venue_tier_boundary_amphitheater_low():
    from src.scrape_venue_capacity import get_venue_tier
    assert get_venue_tier(5000) == "amphitheater"


# ── Tour calendar parsing ─────────────────────────────────────────────────────

def test_parse_bandsintown_events_basic():
    from src.scrape_tour_calendar import parse_events
    markdown = """
## Upcoming Events

**Sep 20, 2026** — Madison Square Garden, New York, NY [Get Tickets](https://bandsintown.com/t/123)
**Oct 5, 2026** — Crypto.com Arena, Los Angeles, CA [Get Tickets](https://bandsintown.com/t/456)
"""
    events = parse_events(markdown, "Test Artist")
    assert len(events) == 2
    assert events[0]["city"] == "New York"
    assert events[0]["state"] == "NY"
    assert events[0]["venue_name"] == "Madison Square Garden"


def test_parse_bandsintown_events_empty():
    from src.scrape_tour_calendar import parse_events
    events = parse_events("No upcoming events.", "Test Artist")
    assert events == []


def test_parse_bandsintown_events_returns_list():
    from src.scrape_tour_calendar import parse_events
    result = parse_events("", "Test Artist")
    assert isinstance(result, list)
