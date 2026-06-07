"""
Apify Google Maps Scraper — fetch & store.

Self-contained module. It sends the input in apify_data/input.json to the Apify
"Google Maps Scraper" actor (compass/crawler-google-places), gets back nearby
places — parking lots, bus stops, ... — and stores them as JSON in this folder.
No dependency on the rest of the project; pure Python standard library.

Input — apify_data/input.json is the **official Apify actor input**, sent to the
API as-is. Edit that file to change the search terms, the location
(`customGeolocation`), radius, language, and any other actor option. This code
does not hardcode the input; it just loads and forwards it.

Config — read from the repo-root .env automatically (or the real environment):
    APIFY_TOKEN      Apify API token — required for a live scrape.
    APIFY_ACTOR_ID   Optional; defaults to compass/crawler-google-places.
    USE_MOCK_DATA    "true" (default) → reuse demo_data.json so the module keeps
                     working offline / without a token. Project-wide flag; use
                     --live / force_live to go live for just this module.

Usage as a CLI:
    # use input.json (mock by default → demo_data.json)
    python apify_data/scraper.py
    # live (real Apify), just this module
    python apify_data/scraper.py --live
    # live + save locally + HTTP-upload the saved file to Box
    python apify_data/scraper.py --live --upload-box
    # override the location in input.json for a one-off run
    python apify_data/scraper.py --lat 47.6343777 --lon -122.3390679 --live

Usage as a library:
    from apify_data.scraper import load_input, run_scraper, save_results
    places = run_scraper(load_input(), force_live=True)
    save_results(places, "venue_a")
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
DEMO_DATA_PATH = DATA_DIR / "demo_data.json"
INPUT_PATH = DATA_DIR / "input.json"


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

# Fallback input — used only if input.json is missing. The real, hand-editable
# input lives in input.json (official Apify format).
DEFAULT_SEARCH_TERMS = ["parking lot", "bus stop", "coffee", "bars", "restaurant", "hotel", "grocery"]
DEFAULT_RADIUS_KM = 1
DEFAULT_MAX_PER_SEARCH = 50
DEFAULT_LANGUAGE = "en"

_APIFY_SYNC_URL = (
    f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/run-sync-get-dataset-items"
)


# --- Public API -------------------------------------------------------------

def load_input(path: Path | str = INPUT_PATH) -> dict:
    """Load the Apify actor input (official format) from input.json.

    Returns the dict exactly as stored — it is forwarded to the Apify API as-is.
    If the file is missing, returns a minimal fallback built from DEFAULT_*.
    """
    path = Path(path)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return _default_input()


def update_input(
    lat: float,
    lon: float,
    *,
    radius_km: float | None = None,
    search_terms: list[str] | None = None,
    path: Path | str = INPUT_PATH,
) -> dict:
    """Write a location into input.json and return the updated input.

    This is how a frontend's address (once geocoded to lat/lon) gets persisted:
    load the current input.json, set the coordinate — and optionally the radius
    and search terms — then save it back. The scraper reads input.json as usual.
    """
    path = Path(path)
    cfg = load_input(path)
    _apply_overrides(cfg, lat=lat, lon=lon, radius_km=radius_km, terms=search_terms)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return cfg


def run_scraper(apify_input: dict, *, token: str | None = None, force_live: bool = False) -> list[dict]:
    """Send ``apify_input`` (an official Apify input dict) to the actor and
    return the scraped places.

    Calls the Apify Google Maps Scraper when a token is available, otherwise
    falls back to the bundled demo dataset so this module keeps working offline.
    Live mode is used when a token is present AND either ``USE_MOCK_DATA`` is
    false (the project-wide flag) or ``force_live`` is set.
    """
    api_token = token or APIFY_TOKEN
    if api_token and (force_live or not USE_MOCK_DATA):
        try:
            return _fetch_via_apify(apify_input, api_token)
        except Exception as e:  # network / API / parse errors → degrade to demo
            print(f"[scraper] Apify request failed, using demo data: {e}")
    return _load_demo_data()


def scrape_nearby(
    lat: float,
    lon: float,
    *,
    search_terms: list[str] | None = None,
    radius_km: float = DEFAULT_RADIUS_KM,
    max_per_search: int = DEFAULT_MAX_PER_SEARCH,
    language: str = DEFAULT_LANGUAGE,
    token: str | None = None,
    force_live: bool = False,
) -> list[dict]:
    """Convenience wrapper: build a minimal official input from a single
    coordinate and run it. (For full control, edit input.json + run_scraper.)
    """
    apify_input = {
        "searchStringsArray": search_terms or DEFAULT_SEARCH_TERMS,
        "customGeolocation": {
            "type": "Point",
            "coordinates": [lon, lat],  # GeoJSON order: [lng, lat]
            "radiusKm": radius_km,
        },
        "maxCrawledPlacesPerSearch": max_per_search,
        "language": language,
    }
    return run_scraper(apify_input, token=token, force_live=force_live)


def scrape_and_store(lat: float, lon: float, venue_key: str = "venue", **kwargs) -> tuple[list[dict], Path]:
    """Coordinate convenience: scrape near (lat, lon) and save the results."""
    places = scrape_nearby(lat, lon, **kwargs)
    return places, save_results(places, venue_key)


def save_results(places: list[dict], key: str = "venue") -> Path:
    """Write ``places`` to ``apify_data/<key>_scraped.json``."""
    output_path = DATA_DIR / f"{key}_scraped.json"
    with open(output_path, "w") as f:
        json.dump(places, f, indent=2, ensure_ascii=False)
    return output_path


# --- Internal helpers -------------------------------------------------------

def _fetch_via_apify(apify_input: dict, token: str) -> list[dict]:
    """POST the input to the actor's run-sync endpoint and return the items.

    ``run-sync-get-dataset-items`` blocks until the run finishes and returns the
    scraped places directly — no run-status polling needed.
    """
    url = f"{_APIFY_SYNC_URL}?{urllib.parse.urlencode({'token': token})}"
    body = json.dumps(apify_input).encode("utf-8")
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


def _default_input() -> dict:
    return {
        "searchStringsArray": DEFAULT_SEARCH_TERMS,
        "customGeolocation": {
            "type": "Point",
            "coordinates": [-122.3401, 47.6340],
            "radiusKm": DEFAULT_RADIUS_KM,
        },
        "maxCrawledPlacesPerSearch": DEFAULT_MAX_PER_SEARCH,
        "language": DEFAULT_LANGUAGE,
    }


def _apply_overrides(apify_input: dict, *, lat=None, lon=None, radius_km=None, terms=None) -> dict:
    """Apply optional CLI overrides onto the loaded input, in place."""
    if lat is not None and lon is not None:
        geo = apify_input.setdefault("customGeolocation", {"type": "Point"})
        geo["type"] = "Point"
        geo["coordinates"] = [lon, lat]  # [lng, lat]
    if radius_km is not None:
        apify_input.setdefault("customGeolocation", {"type": "Point"})["radiusKm"] = radius_km
    if terms:
        apify_input["searchStringsArray"] = terms
    return apify_input


# --- CLI --------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run the Apify Google Maps Scraper from input.json and store the results."
    )
    p.add_argument("--input", default=str(INPUT_PATH), help="path to the input JSON (official Apify input)")
    p.add_argument("--key", default="venue", help="output filename → <key>_scraped.json")
    p.add_argument("--lat", type=float, default=None, help="override the latitude in customGeolocation")
    p.add_argument("--lon", type=float, default=None, help="override the longitude in customGeolocation")
    p.add_argument("--radius-km", type=float, default=None, help="override customGeolocation.radiusKm")
    p.add_argument("--terms", nargs="+", default=None, help="override searchStringsArray")
    p.add_argument("--token", default=None, help="Apify token (overrides APIFY_TOKEN)")
    p.add_argument("--live", action="store_true",
                   help="force a live Apify call without flipping USE_MOCK_DATA")
    p.add_argument("--upload-box", action="store_true",
                   help="after saving locally, HTTP-upload the JSON file to Box")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    apify_input = load_input(args.input)
    _apply_overrides(
        apify_input, lat=args.lat, lon=args.lon, radius_km=args.radius_km, terms=args.terms
    )

    # An explicitly-passed --token implies you want a live call.
    force_live = args.live or args.token is not None
    places = run_scraper(apify_input, token=args.token, force_live=force_live)
    path = save_results(places, args.key)

    went_live = bool(args.token or APIFY_TOKEN) and (force_live or not USE_MOCK_DATA)
    source = "Apify (live)" if went_live else "demo data (mock)"
    print(f"Stored {len(places)} places from {source} → {path}")

    # Final flow: data is saved locally above, then HTTP-POSTed to Box.
    if args.upload_box:
        from box_uploader import upload_file
        file_id = upload_file(path)
        print(f"Uploaded to Box → file id {file_id}")
