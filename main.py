"""
SiteLens FastAPI application.
Skeleton created by Jingyi to unblock frontend integration.
Kone owns Apify/POI wiring (_mock_poi -> live apify_service + poi_aggregator).
Simin wired the real analysis pipeline: agent_service -> report_service -> box_service.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv(Path(__file__).parent / ".env")

import sys  # noqa: E402
sys.path.insert(0, str(Path(__file__).parent / "geo_service"))
sys.path.insert(0, str(Path(__file__).parent / "DataAnalysis"))
sys.path.insert(0, str(Path(__file__).parent / "apify_data"))

import json  # noqa: E402

from services.geo_pipeline import run_geo_pipeline  # noqa: E402
from agent_service import compare_venues  # noqa: E402
from report_service import build_packet_files, write_outputs_to_disk  # noqa: E402
from poi_aggregator import aggregate_pois  # noqa: E402
import box_service  # noqa: E402
from scraper import scrape_and_store  # noqa: E402

APIFY_DATA_DIR = Path(__file__).parent / "apify_data"

app = FastAPI(title="SiteLens API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "geo_service" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
BOX_OUTPUT_FOLDER_ID = os.getenv("BOX_FOLDER_ID")
BOX_CHECKLIST_FILE_ID = os.getenv("BOX_CHECKLIST_FILE_ID")


# ---------------------------------------------------------------------------
# Request model (matches what VenueForm.tsx sends)
# ---------------------------------------------------------------------------

class VenueInput(BaseModel):
    id: str = ""
    name: str = ""
    address: str


class AnalyzeVenuesRequest(BaseModel):
    event_name: str = ""
    use_case: str = ""
    venues: list[VenueInput]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze-venues")
def analyze_venues(req: AnalyzeVenuesRequest):
    # 1. Build per-venue evidence: Jingyi's geo signals + POI summary.
    venues = []
    for i, venue in enumerate(req.venues):
        venue_key = f"venue_{chr(ord('a') + i)}"  # venue_a, venue_b, ...
        geo = run_geo_pipeline(venue.address, venue_key)

        # Scrape nearby POI via Apify (skip if cached)
        cached = APIFY_DATA_DIR / f"{venue_key}_scraped.json"
        if cached.exists():
            print(f"[main] Using cached POI for {venue_key}")
        else:
            try:
                scrape_and_store(geo["lat"], geo["lon"], venue_key=venue_key)
            except Exception as e:
                print(f"[main] Apify scrape failed for {venue_key}: {e}")

        venues.append({
            "name": venue.name or geo["address"],
            "address": geo["address"],
            "visual_signals": geo["map_signals"],
            "poi_summary": _load_poi(venue_key),
            "_venue_key": venue_key,
            "_geo": geo,
        })

    # 2. Read the event checklist from Box (optional grounding input).
    checklist_text = _read_checklist()

    # 3. Decision agent. compare_venues always returns a valid dict
    #    (it falls back to a mock decision internally on any failure).
    venue_a = venues[0]
    venue_b = venues[1] if len(venues) > 1 else venues[0]
    decision = compare_venues(
        event_name=req.event_name,
        use_case=req.use_case,
        venue_a=venue_a,
        venue_b=venue_b,
        checklist_text=checklist_text,
    )

    # 4. Render the planning packet (markdown + csv).
    files = build_packet_files(req.event_name, req.use_case, decision, venues)

    # 5. Persist: local copy (always, = fallback) + Box upload (best-effort).
    folder_name = _folder_name(req.event_name)
    try:
        write_outputs_to_disk(req.event_name, req.use_case, decision, venues)
    except Exception as e:
        print(f"[main] local output write failed: {e}")
    box_outputs = _upload_to_box(folder_name, files)

    # 6. Assemble the response for the frontend.
    venue_results = []
    for i, vd in enumerate(venues):
        letter = chr(ord("a") + i)
        venue_results.append({
            "name": vd["name"],
            "address": vd["address"],
            "summary": decision.get(f"venue_{letter}_positioning") or _build_summary(vd["_geo"]),
            "overall_score": decision.get(f"venue_{letter}_overall_score"),
            "visual_signals": vd["visual_signals"],
            "poi_summary": vd["poi_summary"],
            "site_packet_markdown": files.get(f"{vd['_venue_key']}_site_packet.md", ""),
            "map_url": f"{BASE_URL}/static/demo/{vd['_venue_key']}_map.png",
            "satellite_url": f"{BASE_URL}/static/demo/{vd['_venue_key']}_satellite.png",
        })

    return {
        "overall_recommendation": decision.get("overall_recommendation", ""),
        "recommended_venue": decision.get("recommended_venue"),
        "recommended_venue_name": decision.get("recommended_venue_name"),
        "venues": venue_results,
        "tradeoff_matrix": decision.get("tradeoff_matrix", []),
        "key_risks": decision.get("key_risks", []),
        "organizer_actions": decision.get("organizer_actions", []),
        "attendee_logistics_email": decision.get("attendee_logistics_email", ""),
        "evidence_sources": decision.get("evidence_sources", []),
        "box_outputs": box_outputs,
    }


# ---------------------------------------------------------------------------
# Box helpers
# ---------------------------------------------------------------------------

def _read_checklist() -> str:
    """Download the event checklist from Box if configured; else empty."""
    if not (BOX_CHECKLIST_FILE_ID and os.getenv("BOX_DEVELOPER_TOKEN")):
        return ""
    try:
        path = box_service.download_box_file(
            BOX_CHECKLIST_FILE_ID,
            str(Path(__file__).parent / "outputs" / "_checklist.md"),
        )
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        print(f"[main] checklist read failed: {e}")
        return ""


def _upload_to_box(folder_name: str, files: dict) -> list:
    """Upload the packet to Box. Returns [] on failure (local files remain)."""
    if not (BOX_OUTPUT_FOLDER_ID and os.getenv("BOX_DEVELOPER_TOKEN")):
        return []
    try:
        result = box_service.upload_packet_to_box(
            BOX_OUTPUT_FOLDER_ID, folder_name, files
        )
        return result.get("box_outputs", [])
    except Exception as e:
        print(f"[main] Box upload failed (local outputs kept): {e}")
        return []


def _folder_name(event_name: str) -> str:
    from datetime import datetime
    import re
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (event_name or "").strip().lower())
    slug = slug.strip("-") or "venue-review"
    return f"{slug}_{datetime.now().strftime('%Y%m%d-%H%M%S')}"


# ---------------------------------------------------------------------------
# Helpers — real geo data
# ---------------------------------------------------------------------------

def _build_summary(geo: dict) -> str:
    sig = geo["map_signals"]
    parts = []
    if sig.get("water_nearby"):
        parts.append("waterfront access")
    density = sig.get("building_density", "unknown")
    if density != "unknown":
        parts.append(f"{density} building density")
    road = sig.get("road_access", "unknown")
    if road != "unknown":
        parts.append(f"{road} road access")
    parking = sig.get("visible_parking", "unknown")
    if parking not in ("unknown", "strong"):
        parts.append(f"{parking} parking")
    summary = f"{sig.get('land_use_context', 'mixed').replace('_', ' ').title()} area"
    if parts:
        summary += " — " + ", ".join(parts)
    obs = sig.get("observations", [])
    if obs:
        summary += ". " + obs[0]
    return summary


# ---------------------------------------------------------------------------
# Helper — mock POI (Kone will replace with live Apify + poi_aggregator)
# ---------------------------------------------------------------------------

def _load_poi(venue_key: str) -> dict:
    """
    Load Apify scrape and aggregate it via poi_aggregator.

    scrape_and_store() is called earlier in analyze_venues() and
    automatically produces per-venue files (venue_a_scraped.json, etc.).

    Tries, in order:
      1. apify_data/<venue_key>_scraped.json   (per-venue, created by scrape_and_store)
      2. apify_data/venue_scraped.json         (legacy single-venue fallback)
    Falls back to mock POI when neither exists.
    """
    candidates = [
        APIFY_DATA_DIR / f"{venue_key}_scraped.json",
        APIFY_DATA_DIR / "venue_scraped.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            places = raw if isinstance(raw, list) else (
                raw.get("places") or raw.get("results") or raw.get("data") or []
            )
            if places:
                return aggregate_pois(places)
        except Exception as e:
            print(f"[main] POI load failed for {path.name}, trying next: {e}")
    return _mock_poi(venue_key)


def _mock_poi(venue_key: str) -> dict:
    # Fallback when a venue has no cached Apify scrape yet.
    if venue_key == "venue_a":
        return {
            "category_counts": {"restaurant": 12, "coffee": 5, "parking": 3,
                                "hotel": 4, "bar": 6, "convenience": 2, "transit": 3},
            "top_places": [
                {"name": "Westlake Waterfront Grill", "category": "restaurant", "rating": 4.3, "review_count": 210, "address": "Seattle, WA"},
                {"name": "Lake Union Coffee", "category": "coffee", "rating": 4.5, "review_count": 88, "address": "Seattle, WA"},
                {"name": "Westlake Parking Garage", "category": "parking", "rating": 3.8, "review_count": 45, "address": "Seattle, WA"},
            ],
            "average_rating": 4.2,
        }
    return {
        "category_counts": {"restaurant": 18, "coffee": 8, "parking": 5,
                            "hotel": 6, "bar": 9, "convenience": 4, "transit": 5},
        "top_places": [
            {"name": "Capitol Hill Bistro", "category": "restaurant", "rating": 4.1, "review_count": 320, "address": "Seattle, WA"},
            {"name": "Eastlake Coffee Roasters", "category": "coffee", "rating": 4.6, "review_count": 145, "address": "Seattle, WA"},
            {"name": "South Lake Union Parking", "category": "parking", "rating": 3.5, "review_count": 60, "address": "Seattle, WA"},
        ],
        "average_rating": 4.3,
    }
