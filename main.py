"""
SiteLens FastAPI application.
Skeleton created by Jingyi to unblock frontend integration.
Kone will own this file and replace mock sections with live Apify + Box data.
Simin will replace mock analysis sections with the real decision agent.
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

from services.geo_pipeline import run_geo_pipeline  # noqa: E402

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


# ---------------------------------------------------------------------------
# Request model (matches what VenueForm.tsx sends)
# ---------------------------------------------------------------------------

class VenueInput(BaseModel):
    id: str
    name: str
    address: str


class AnalyzeVenuesRequest(BaseModel):
    event_name: str = ""
    use_case: str = ""
    venues: list[VenueInput]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@app.post("/api/analyze-venues")
def analyze_venues(req: AnalyzeVenuesRequest):
    venue_results = []

    for i, venue in enumerate(req.venues):
        venue_key = f"venue_{chr(ord('a') + i)}"  # venue_a, venue_b, ...
        geo = run_geo_pipeline(venue.address, venue_key)

        venue_results.append({
            "name": venue.name or venue.address,
            "address": geo["address"],
            "summary": _build_summary(geo),
            "visual_signals": geo["map_signals"],
            "poi_summary": _mock_poi(venue_key),
            "site_packet_markdown": _build_site_packet(venue.name or venue.address, geo),
            "map_url": f"{BASE_URL}/static/demo/{venue_key}_map.png",
            "satellite_url": f"{BASE_URL}/static/demo/{venue_key}_satellite.png",
        })

    return {
        "overall_recommendation": _mock_recommendation(venue_results),
        "venues": venue_results,
        "tradeoff_matrix": _mock_tradeoff(venue_results),
        "key_risks": _mock_risks(venue_results),
        "organizer_actions": _mock_actions(),
        "attendee_logistics_email": _mock_email(req.event_name, req.venues),
        "evidence_sources": [
            "Map/satellite visual evidence (Mapbox + Claude vision)",
            "Nearby places data (Apify — mock)",
            "Box event checklist (mock)",
        ],
        "box_outputs": [],
    }


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


def _build_site_packet(name: str, geo: dict) -> str:
    sig = geo["map_signals"]
    obs = "\n".join(f"- {o}" for o in sig.get("observations", []))
    risks = "\n".join(f"- {r}" for r in sig.get("risks", []))
    return f"""## {name}

**Address:** {geo['address']}
**Coordinates:** {geo['lat']:.4f}, {geo['lon']:.4f}

### Map / Satellite Observations
{obs or '- No observations available'}

### Identified Risks
{risks or '- No risks identified'}

### Signal Summary
| Signal | Value |
|---|---|
| Water nearby | {geo['map_signals'].get('water_nearby')} |
| Green space | {geo['map_signals'].get('green_space_level')} |
| Building density | {geo['map_signals'].get('building_density')} |
| Road access | {geo['map_signals'].get('road_access')} |
| Visible parking | {geo['map_signals'].get('visible_parking')} |
| Land use | {geo['map_signals'].get('land_use_context')} |
| Confidence | {geo['map_signals'].get('confidence')} |
"""


# ---------------------------------------------------------------------------
# Helpers — mock (Kone / Simin will replace these)
# ---------------------------------------------------------------------------

def _mock_poi(venue_key: str) -> dict:
    # TODO (Kone): replace with live Apify data
    if venue_key == "venue_a":
        return {
            "category_counts": {"restaurant": 12, "coffee": 5, "parking": 3, "hotel": 4, "bar": 6},
            "top_places": [
                {"name": "Westlake Waterfront Grill", "category": "restaurant", "rating": 4.3, "review_count": 210},
                {"name": "Lake Union Coffee", "category": "coffee", "rating": 4.5, "review_count": 88},
                {"name": "Westlake Parking Garage", "category": "parking", "rating": 3.8, "review_count": 45},
            ],
            "average_rating": 4.2,
        }
    return {
        "category_counts": {"restaurant": 18, "coffee": 8, "parking": 5, "hotel": 6, "bar": 9},
        "top_places": [
            {"name": "Capitol Hill Bistro", "category": "restaurant", "rating": 4.1, "review_count": 320},
            {"name": "Eastlake Coffee Roasters", "category": "coffee", "rating": 4.6, "review_count": 145},
            {"name": "South Lake Union Parking", "category": "parking", "rating": 3.5, "review_count": 60},
        ],
        "average_rating": 4.3,
    }


def _mock_recommendation(venues: list) -> str:
    # TODO (Simin): replace with decision agent output
    if len(venues) < 2:
        return "Analysis complete. Review venue details below."
    a, b = venues[0]["name"], venues[1]["name"]
    return (
        f"{a} offers a distinctive waterfront setting well-suited for networking-heavy events. "
        f"{b} provides better access to restaurants and hotels, making it stronger for multi-day formats. "
        "Final choice depends on whether walkable amenities or venue character is prioritized."
    )


def _mock_tradeoff(venues: list) -> list:
    # TODO (Simin): replace with decision agent output
    a_sig = venues[0].get("visual_signals", {}) if venues else {}
    b_sig = venues[1].get("visual_signals", {}) if len(venues) > 1 else {}

    def rating(sig, key, good_values, bad_values):
        v = sig.get(key, "unknown")
        if v in good_values:
            return "Strong"
        if v in bad_values:
            return "Weak"
        return "Medium"

    rows = [
        {
            "criterion": "Accessibility",
            "venue_a_rating": rating(a_sig, "road_access", ["strong"], ["weak"]),
            "venue_b_rating": rating(b_sig, "road_access", ["strong"], ["weak"]),
            "evidence": "Based on road access signals from map imagery.",
        },
        {
            "criterion": "Parking",
            "venue_a_rating": rating(a_sig, "visible_parking", ["strong", "moderate"], ["limited"]),
            "venue_b_rating": rating(b_sig, "visible_parking", ["strong", "moderate"], ["limited"]),
            "evidence": "Based on visible parking signals from satellite imagery.",
        },
        {
            "criterion": "Nearby Amenities",
            "venue_a_rating": "Medium",
            "venue_b_rating": "Strong",
            "evidence": "Based on Apify nearby-place counts (mock).",
        },
        {
            "criterion": "Event Atmosphere",
            "venue_a_rating": "Strong" if a_sig.get("water_nearby") else "Medium",
            "venue_b_rating": "Strong" if b_sig.get("water_nearby") else "Medium",
            "evidence": "Based on land use context and visual character.",
        },
        {
            "criterion": "Logistics Risk",
            "venue_a_rating": rating(a_sig, "visible_parking", ["strong"], ["limited", "unknown"]),
            "venue_b_rating": rating(b_sig, "visible_parking", ["strong"], ["limited", "unknown"]),
            "evidence": "Parking and road access signals combined.",
        },
    ]
    return rows


def _mock_risks(venues: list) -> list:
    # TODO (Simin): replace with decision agent output
    risks = []
    for i, v in enumerate(venues):
        label = chr(ord("A") + i)
        for r in v.get("visual_signals", {}).get("risks", [])[:2]:
            risks.append({
                "venue": label,
                "risk": r,
                "evidence": "Identified from map/satellite visual signals.",
                "mitigation": "Confirm on-site and arrange alternatives in advance.",
            })
    return risks


def _mock_actions() -> list:
    # TODO (Simin): replace with decision agent output
    return [
        "Confirm parking capacity and reserve overflow options for both venues.",
        "Contact venues to verify A/V setup and capacity for 100 attendees.",
        "Identify rideshare drop-off zones and communicate to attendees.",
        "Book nearby restaurant blocks for post-event networking.",
        "Confirm accessibility compliance (elevator, ramp access).",
    ]


def _mock_email(event_name: str, venues: list) -> str:
    # TODO (Simin): replace with decision agent output
    name = event_name or "our upcoming developer event"
    addresses = " or ".join(v.address for v in venues)
    return f"""Hi everyone,

We're excited to share logistics details for {name}.

The event will be held at one of the following venues: {addresses}.
Final venue selection will be confirmed shortly.

**Getting there:**
- Rideshare (Uber/Lyft) is recommended — drop-off available at the main entrance.
- Limited street parking is available nearby. Please plan accordingly.
- Public transit options are within walking distance.

**Nearby amenities:**
- Several restaurants and coffee shops are within a 5-minute walk.
- Hotels are available nearby for out-of-town attendees.

We'll send a follow-up with the confirmed venue and a detailed map.

See you there!
"""
