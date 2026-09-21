"""Unit tests for pipeline parsing functions."""
import pytest


# ── Release parsing ───────────────────────────────────────────────────────────

def test_parse_release_date_album():
    from src.scrape_spotify_releases import parse_release
    markdown = """
[Short n' Sweet](https://open.spotify.com/album/abc)

2024 • Album

[Emails I Can't Send](https://open.spotify.com/album/def)

2022 • Album
"""
    result = parse_release(markdown)
    assert result["title"] == "Short n' Sweet"
    assert result["release_type"] == "Album"
    assert result["release_year"] == "2024"


def test_parse_release_date_single():
    from src.scrape_spotify_releases import parse_release
    markdown = """
[Please Please Please](https://open.spotify.com/album/xyz)

2024 • Single
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

def test_parse_tm_events_basic():
    from src.scrape_tour_calendar import parse_tm_events
    data = {
        "_embedded": {
            "events": [
                {
                    "name": "Zach Bryan - With Heaven On Tour",
                    "dates": {"start": {"localDate": "2026-10-03"}},
                    "_embedded": {
                        "venues": [{
                            "name": "Gillette Stadium",
                            "city": {"name": "Foxborough"},
                            "state": {"stateCode": "MA"},
                        }]
                    },
                    "url": "https://www.ticketmaster.com/event/abc",
                },
                {
                    "name": "Zach Bryan - With Heaven On Tour",
                    "dates": {"start": {"localDate": "2026-10-10"}},
                    "_embedded": {
                        "venues": [{
                            "name": "Jordan Hare Stadium",
                            "city": {"name": "Auburn"},
                            "state": {"stateCode": "AL"},
                        }]
                    },
                    "url": "https://www.ticketmaster.com/event/def",
                },
            ]
        }
    }
    events = parse_tm_events(data, "Zach Bryan")
    assert len(events) == 2
    assert events[0]["city"] == "Foxborough"
    assert events[0]["state"] == "MA"
    assert events[0]["venue_name"] == "Gillette Stadium"


def test_parse_tm_events_empty():
    from src.scrape_tour_calendar import parse_tm_events
    events = parse_tm_events({}, "Test Artist")
    assert events == []


def test_parse_tm_events_returns_list():
    from src.scrape_tour_calendar import parse_tm_events
    result = parse_tm_events({}, "Test Artist")
    assert isinstance(result, list)
