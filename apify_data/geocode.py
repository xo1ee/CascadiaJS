"""
Address → (lat, lon). Self-contained, no dependency on the rest of the project.

Uses Google Geocoding if a key is set (GOOGLE_MAPS_API_KEY / GOOGLE_API_KEY),
otherwise the free OpenStreetMap Nominatim service (no key required). Standard
library only.

CLI:
    python apify_data/geocode.py "1700 Westlake Ave N, Seattle, WA"
"""

from __future__ import annotations

import os
import json
import urllib.parse
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent


def _load_env(path: Path) -> None:
    """Tiny stdlib .env loader (so a Google key in .env is picked up)."""
    if not path.exists():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env(_REPO_ROOT / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_API_KEY")
_USER_AGENT = "SiteLens-apify/1.0 (geocoder)"


def geocode(address: str) -> tuple[float, float]:
    """Return ``(lat, lon)`` for ``address``.

    Google Geocoding when a key is configured, otherwise free Nominatim.
    Raises if the address cannot be resolved.
    """
    address = address.strip()
    if not address:
        raise ValueError("empty address")

    if GOOGLE_API_KEY:
        try:
            return _geocode_google(address)
        except Exception as e:
            print(f"[geocode] Google failed ({e}); falling back to Nominatim")

    return _geocode_nominatim(address)


def _geocode_google(address: str) -> tuple[float, float]:
    url = "https://maps.googleapis.com/maps/api/geocode/json?" + urllib.parse.urlencode(
        {"address": address, "key": GOOGLE_API_KEY}
    )
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.load(r)
    if data.get("status") != "OK" or not data.get("results"):
        raise RuntimeError(f"Google geocoding status={data.get('status')}")
    loc = data["results"][0]["geometry"]["location"]
    return float(loc["lat"]), float(loc["lng"])


def _geocode_nominatim(address: str) -> tuple[float, float]:
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
        {"q": address, "format": "json", "limit": 1}
    )
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:
        results = json.load(r)
    if not results:
        raise RuntimeError(f"no geocoding result for: {address}")
    return float(results[0]["lat"]), float(results[0]["lon"])


if __name__ == "__main__":
    import sys

    addr = " ".join(sys.argv[1:]) or "Space Needle, Seattle, WA"
    lat, lon = geocode(addr)
    print(f"{addr}\n  -> lat={lat}, lon={lon}   (coordinates for input.json: [{lon}, {lat}])")
