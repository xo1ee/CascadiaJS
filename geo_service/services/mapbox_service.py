"""
Jingyi - Map Data Retrieval
Handles geocoding and map/satellite image fetching.

Priority order:
  1. Mapbox Static Images API  (if MAPBOX_TOKEN is set)
  2. OpenStreetMap tile stitch (free, no token required)
  3. Solid-color placeholder   (last resort)

Pipeline: address -> (lat, lon) -> map/satellite PNGs
"""

import os
import json
import math
import struct
import zlib
import urllib.parse
from pathlib import Path

import httpx

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

_BASE = Path(__file__).parent.parent
DEMO_VENUES_PATH = _BASE / "data" / "demo_venues.json"
STATIC_DEMO_PATH = _BASE / "static" / "demo"

# OSM tile settings
_OSM_ZOOM = 15
_OSM_TILE_SIZE = 256          # pixels per tile
_OSM_GRID = 3                 # stitch an N×N grid of tiles → 768×768 image
_OSM_USER_AGENT = "SiteLens/1.0 (hackathon project)"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def geocode_address(address: str) -> tuple[float, float]:
    """
    Returns (lat, lon) for a venue address.
    Order: Mapbox → Nominatim (OSM, free) → demo_venues.json
    """
    if MAPBOX_TOKEN and not USE_MOCK_DATA:
        try:
            return _geocode_via_mapbox(address)
        except Exception as e:
            print(f"[mapbox_service] Mapbox geocoding failed: {e}")

    if not USE_MOCK_DATA:
        try:
            return _geocode_via_nominatim(address)
        except Exception as e:
            print(f"[mapbox_service] Nominatim geocoding failed: {e}")

    return _geocode_from_demo_data(address)


def get_map_snapshots(lat: float, lon: float, venue_key: str) -> dict:
    """
    Returns paths to map and satellite PNG images for a venue.
    Order: Mapbox → OSM tile stitch → solid-color placeholder

    Returns:
        {"map_path": str, "satellite_path": str}
    """
    map_path = STATIC_DEMO_PATH / f"{venue_key}_map.png"
    satellite_path = STATIC_DEMO_PATH / f"{venue_key}_satellite.png"

    if not USE_MOCK_DATA:
        if MAPBOX_TOKEN:
            try:
                _download_mapbox_image(lat, lon, "streets-v12", map_path)
                _download_mapbox_image(lat, lon, "satellite-streets-v12", satellite_path)
                return {"map_path": str(map_path), "satellite_path": str(satellite_path)}
            except Exception as e:
                print(f"[mapbox_service] Mapbox image failed: {e}")

        # OSM fallback — free, no token needed
        try:
            _download_osm_map(lat, lon, map_path)
            # OSM doesn't have free satellite; reuse the map tile for satellite slot
            _download_osm_map(lat, lon, satellite_path)
            return {"map_path": str(map_path), "satellite_path": str(satellite_path)}
        except Exception as e:
            print(f"[mapbox_service] OSM tile download failed: {e}")

    _ensure_placeholder_images(map_path, satellite_path)
    return {"map_path": str(map_path), "satellite_path": str(satellite_path)}


# ---------------------------------------------------------------------------
# Internal helpers — geocoding
# ---------------------------------------------------------------------------

def _geocode_via_mapbox(address: str) -> tuple[float, float]:
    encoded = urllib.parse.quote(address)
    url = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded}.json"
        f"?access_token={MAPBOX_TOKEN}&limit=1"
    )
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    coords = resp.json()["features"][0]["geometry"]["coordinates"]
    lon, lat = coords[0], coords[1]
    return lat, lon


def _geocode_via_nominatim(address: str) -> tuple[float, float]:
    """Free OSM-based geocoding — no token required."""
    url = "https://nominatim.openstreetmap.org/search"
    resp = httpx.get(
        url,
        params={"q": address, "format": "json", "limit": 1},
        headers={"User-Agent": _OSM_USER_AGENT},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"Nominatim returned no results for: {address}")
    return float(results[0]["lat"]), float(results[0]["lon"])


def _geocode_from_demo_data(address: str) -> tuple[float, float]:
    with open(DEMO_VENUES_PATH) as f:
        venues = json.load(f)

    address_lower = address.strip().lower()
    for venue in venues.values():
        if address_lower in venue["address"].lower() or venue["address"].lower() in address_lower:
            return venue["lat"], venue["lon"]

    first = next(iter(venues.values()))
    print(f"[mapbox_service] Address not found in demo data, using default: {first['name']}")
    return first["lat"], first["lon"]


# ---------------------------------------------------------------------------
# Internal helpers — map images
# ---------------------------------------------------------------------------

def _download_mapbox_image(
    lat: float,
    lon: float,
    style: str,
    output_path: Path,
    width: int = 800,
    height: int = 600,
    zoom: int = 15,
) -> None:
    url = (
        f"https://api.mapbox.com/styles/v1/mapbox/{style}/static"
        f"/pin-s+ff0000({lon},{lat})"
        f"/{lon},{lat},{zoom}/{width}x{height}"
        f"?access_token={MAPBOX_TOKEN}"
    )
    resp = httpx.get(url, timeout=20)
    resp.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(resp.content)


def _deg2tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon to OSM tile x/y at the given zoom level."""
    lat_r = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n)
    return x, y


def _download_osm_map(lat: float, lon: float, output_path: Path) -> None:
    """
    Downloads an _OSM_GRID × _OSM_GRID grid of OSM tiles centred on the
    venue and stitches them into a single PNG using only stdlib (no Pillow).
    """
    cx, cy = _deg2tile(lat, lon, _OSM_ZOOM)
    half = _OSM_GRID // 2
    tiles: list[list[bytes]] = []

    for row in range(_OSM_GRID):
        tile_row: list[bytes] = []
        for col in range(_OSM_GRID):
            tx, ty = cx - half + col, cy - half + row
            url = f"https://tile.openstreetmap.org/{_OSM_ZOOM}/{tx}/{ty}.png"
            resp = httpx.get(url, headers={"User-Agent": _OSM_USER_AGENT}, timeout=15)
            resp.raise_for_status()
            tile_row.append(resp.content)
        tiles.append(tile_row)

    _stitch_png_tiles(tiles, output_path)


def _stitch_png_tiles(tiles: list[list[bytes]], output_path: Path) -> None:
    """
    Stitches PNG tiles (all same size) into one PNG using only stdlib.
    Decodes each tile's IDAT stream, concatenates rows, re-encodes.
    """
    rows_count = len(tiles)
    cols_count = len(tiles[0])

    def read_png_chunks(data: bytes) -> dict:
        pos = 8  # skip signature
        chunks: dict[bytes, list[bytes]] = {}
        while pos < len(data):
            length = struct.unpack(">I", data[pos:pos+4])[0]
            ctype = data[pos+4:pos+8]
            cdata = data[pos+8:pos+8+length]
            chunks.setdefault(ctype, []).append(cdata)
            pos += 12 + length
        return chunks

    def png_dimensions(data: bytes) -> tuple[int, int]:
        w, h = struct.unpack(">II", data[8+8:8+8+8])
        return w, h

    # Determine tile dimensions from first tile
    first_tile = tiles[0][0]
    tile_w, tile_h = png_dimensions(first_tile)
    total_w = tile_w * cols_count
    total_h = tile_h * rows_count

    # Decompress each tile into raw scanlines
    all_rows: list[bytes] = []
    for tile_row in tiles:
        # Decompress each tile in this row
        tile_scanlines: list[list[bytes]] = []
        for tile_data in tile_row:
            chunks = read_png_chunks(tile_data)
            compressed = b"".join(chunks[b"IDAT"])
            raw = zlib.decompress(compressed)
            # Each scanline: 1 filter byte + tile_w * 3 RGB bytes
            stride = 1 + tile_w * 3
            scanlines = [raw[i * stride:(i + 1) * stride] for i in range(tile_h)]
            tile_scanlines.append(scanlines)
        # Merge scanlines across columns for each pixel row
        for y in range(tile_h):
            merged_row = b"\x00"  # filter byte = None
            for col_scanlines in tile_scanlines:
                merged_row += col_scanlines[y][1:]  # strip the filter byte from each tile
            all_rows.append(merged_row)

    def make_chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = make_chunk(b"IHDR", struct.pack(">IIBBBBB", total_w, total_h, 8, 2, 0, 0, 0))
    idat = make_chunk(b"IDAT", zlib.compress(b"".join(all_rows)))
    iend = make_chunk(b"IEND", b"")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(signature + ihdr + idat + iend)


def _ensure_placeholder_images(map_path: Path, satellite_path: Path) -> None:
    STATIC_DEMO_PATH.mkdir(parents=True, exist_ok=True)
    if not map_path.exists():
        _write_placeholder_png(map_path, color=(180, 200, 180))
    if not satellite_path.exists():
        _write_placeholder_png(satellite_path, color=(60, 80, 60))


def _write_placeholder_png(path: Path, color: tuple = (128, 128, 128), width: int = 256, height: int = 256) -> None:
    """Solid-color PNG — last resort only."""
    r, g, b = color

    def make_chunk(ctype: bytes, data: bytes) -> bytes:
        c = ctype + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = make_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    row = bytes([r, g, b] * width)
    raw = b"".join(b"\x00" + row for _ in range(height))
    idat = make_chunk(b"IDAT", zlib.compress(raw))
    iend = make_chunk(b"IEND", b"")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(signature + ihdr + idat + iend)
