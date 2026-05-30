"""
Apify Google Maps Scraper — fetch & store.

Self-contained module. Given a venue's coordinates (lat, lon), it queries the
Apify "Google Maps Scraper" actor (compass/crawler-google-places) for nearby
points of interest — parking lots, bus stops, ... — within a radius, and stores
the raw results as JSON in this folder. It has no dependency on any other part
of the project; the caller passes the coordinates in.

Stored JSON matches demo_data_from_scraper.json. Each item:
    {"address", "location": {"lat", "lng"}, "categoryName", "categories": [...]}
Live runs additionally include richer fields such as "title", "totalScore" and
"reviewsCount".

Config — read from the repo-root .env automatically (or the real environment):
    APIFY_TOKEN      Apify API token — required for a live scrape.
    APIFY_ACTOR_ID   Optional; defaults to compass/crawler-google-places.
    USE_MOCK_DATA    "true" (default) → reuse demo_data_from_scraper.json so the
                     pipeline keeps working offline / without a token. This flag
                     is project-wide; use --live / force_live to go live for just
                     this module without flipping it.

Usage as a library:
    from apify_data.scraper import scrape_and_store
    places, path = scrape_and_store(47.6340, -122.3401, venue_key="venue_a")

Usage as a CLI:
    # mock (default): reuse the demo dataset
    python apify_data/scraper.py --lat 47.6340 --lon -122.3401 --key venue_a
    # live: token from .env/env, just this module
    python apify_data/scraper.py --lat 47.6340 --lon -122.3401 --key venue_a --live
"""

from __future__ import annotations

import os
import json
import argparse
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# --- Config -----------------------------------------------------------------

DATA_DIR = Path(__file__).parent
DEMO_DATA_PATH = DATA_DIR / "demo_data_from_scraper.json"


def _load_env_file(path: Path) -> None:
    """Best-effort .env loader (stdlib only) so standalone CLI runs pick up
    APIFY_TOKEN / USE_MOCK_DATA from the repo-root .env without needing
    python-dotenv. Real environment variables always win — we only fill keys
    that aren't already set.
    """
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


# Load the repo-root .env (one level up from apify_data/) before reading config.
_load_env_file(DATA_DIR.parent / ".env")

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
# compass/crawler-google-places — the standard "Google Maps Scraper".
APIFY_ACTOR_ID = os.getenv("APIFY_ACTOR_ID") or "nwua9Gu5YrADL7ZDj"
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# What to look for around each venue. Extend to add more categories.
DEFAULT_SEARCH_TERMS = ["parking lot", "bus stop"]
# "diameter 1 mile" → radius 0.5 mile ≈ 0.8 km.
DEFAULT_RADIUS_KM = 0.8
DEFAULT_MAX_PER_SEARCH = 50

_APIFY_SYNC_URL = (
    f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/run-sync-get-dataset-items"
)


# --- Public API -------------------------------------------------------------

def scrape_nearby(
    lat: float,
    lon: float,
    *,
    search_terms: list[str] | None = None,
    radius_km: float = DEFAULT_RADIUS_KM,
    max_per_search: int = DEFAULT_MAX_PER_SEARCH,
    token: str | None = None,
    force_live: bool = False,
) -> list[dict]:
    """Return places within ``radius_km`` of ``(lat, lon)``.

    Calls the Apify Google Maps Scraper when a token is available, otherwise
    falls back to the bundled demo dataset so this module keeps working
    offline. Live mode is used when a token is present AND either
    ``USE_MOCK_DATA`` is false (the project-wide flag) or ``force_live`` is set
    (lets you test just this module without flipping the shared flag).
    """
    terms = search_terms or DEFAULT_SEARCH_TERMS
    api_token = token or APIFY_TOKEN

    if api_token and (force_live or not USE_MOCK_DATA):
        try:
            return _fetch_via_apify(lat, lon, terms, radius_km, max_per_search, api_token)
        except Exception as e:  # network / API / parse errors → degrade to demo
            print(f"[scraper] Apify request failed, using demo data: {e}")

    return _load_demo_data()


def scrape_and_store(
    lat: float,
    lon: float,
    venue_key: str = "venue",
    **kwargs,
) -> tuple[list[dict], Path]:
    """Scrape nearby places and persist them to ``<venue_key>_scraped.json``.

    Returns ``(places, output_path)``.
    """
    places = scrape_nearby(lat, lon, **kwargs)
    output_path = save_results(places, venue_key)
    return places, output_path


def save_results(places: list[dict], venue_key: str = "venue") -> Path:
    """Write ``places`` to ``apify_data/<venue_key>_scraped.json``."""
    output_path = DATA_DIR / f"{venue_key}_scraped.json"
    with open(output_path, "w") as f:
        json.dump(places, f, indent=2, ensure_ascii=False)
    return output_path


# --- Internal helpers -------------------------------------------------------

def _fetch_via_apify(
    lat: float,
    lon: float,
    search_terms: list[str],
    radius_km: float,
    max_per_search: int,
    token: str,
) -> list[dict]:
    """Run the actor synchronously and return the scraped dataset items.

    ``run-sync-get-dataset-items`` blocks until the run finishes and returns the
    places directly — no run-status polling needed.
    """
    payload = {
        "searchStringsArray": search_terms,
        "customGeolocation": {
            "type": "Point",
            # GeoJSON order is [lng, lat] — reversed from Google Maps display.
            "coordinates": [lon, lat],
            "radiusKm": radius_km,
        },
        "maxCrawledPlacesPerSearch": max_per_search,
        "language": "en",
    }
    url = f"{_APIFY_SYNC_URL}?{urllib.parse.urlencode({'token': token})}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:  # scraping can take minutes
        return json.load(resp)


def _load_demo_data() -> list[dict]:
    with open(DEMO_DATA_PATH) as f:
        return json.load(f)


# --- CLI --------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Fetch & store nearby places via the Apify Google Maps Scraper."
    )
    p.add_argument("--lat", type=float, required=True, help="venue latitude")
    p.add_argument("--lon", type=float, required=True, help="venue longitude")
    p.add_argument("--key", default="venue", help="venue key → output filename")
    p.add_argument("--radius-km", type=float, default=DEFAULT_RADIUS_KM)
    p.add_argument("--terms", nargs="+", default=DEFAULT_SEARCH_TERMS,
                   help="search terms, e.g. --terms 'parking lot' 'bus stop'")
    p.add_argument("--token", default=None, help="Apify token (overrides APIFY_TOKEN)")
    p.add_argument("--live", action="store_true",
                   help="force a live Apify call without flipping USE_MOCK_DATA")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    # An explicitly-passed --token implies you want a live call.
    force_live = args.live or args.token is not None
    places, path = scrape_and_store(
        args.lat,
        args.lon,
        args.key,
        search_terms=args.terms,
        radius_km=args.radius_km,
        token=args.token,
        force_live=force_live,
    )
    went_live = bool(args.token or APIFY_TOKEN) and (force_live or not USE_MOCK_DATA)
    source = "Apify (live)" if went_live else "demo data (mock)"
    print(f"Stored {len(places)} places from {source} → {path}")
