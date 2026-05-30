"""
Simin - Decision Agent (AI analysis layer).

Consumes the structured evidence produced upstream:
    - Jingyi's geo visual_signals  (geo_evidence_schema.GeoVisualSignals)
    - Simin's poi_summary          (poi_aggregator.aggregate_pois output)
    - Box event checklist text

and runs a single grounded LLM call to compare two venues for a developer
event. Returns the structured decision JSON consumed by report_service.py
and main.py.

Pipeline:
    {event_name, use_case, venue_a, venue_b, checklist}
        -> compare_venues()
        -> decision JSON (see SCHEMA below)
"""

import os
import json
from typing import Any, Dict

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

# Model is configurable so the team can swap it from one place.
# Defaults to the same Claude model Jingyi's vision_service uses, which is
# already proven to work with the team's ANTHROPIC_API_KEY.
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-5-20250929")

# The five fixed evaluation dimensions (design doc Section 11 Planner Agent).
EVALUATION_CRITERIA = [
    "Accessibility",
    "Nearby Amenities",
    "Event Atmosphere",
    "Logistics Risk",
    "Attendee Communication Needs",
]

# ---------------------------------------------------------------------------
# Decision Agent prompt (design doc Section 20). Rules + output schema live
# here — this is the "fixed" half of the prompt; venue evidence is injected
# at runtime in compare_venues().
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are SiteLens, an AI site intelligence agent for DevRel and event teams.

Your task is to compare two candidate venues for a developer event using only
the evidence provided to you.

Evidence you will receive:
1. Event name and use case.
2. The event venue checklist (the team's internal planning standard, from Box).
3. Venue A and Venue B visual signals from map/satellite evidence.
4. Venue A and Venue B nearby-place (POI) summaries from Apify.

Evaluate both venues across these five criteria:
- Accessibility
- Nearby Amenities
- Event Atmosphere
- Logistics Risk
- Attendee Communication Needs

Rules:
- Ground every claim in the evidence provided. Do not invent numbers, places,
  ratings, traffic, crime, demographics, or foot-traffic data.
- Do not call this professional remote sensing or NDVI. Treat map/satellite as
  one visual evidence layer only.
- When a signal is "unknown" or confidence is low, say so explicitly rather
  than guessing.
- Do not simply say one venue is good and the other is bad. Explain what each
  venue is better for and the trade-offs.
- Produce concrete, actionable organizer actions and a ready-to-send attendee
  logistics email grounded in the evidence.

Return STRICT JSON only (no markdown, no commentary) with exactly this schema:

{
  "overall_recommendation": "Short recommendation with nuance.",
  "venue_a_positioning": "What Venue A is best for.",
  "venue_b_positioning": "What Venue B is best for.",
  "tradeoff_matrix": [
    {
      "criterion": "Accessibility",
      "venue_a_rating": "Strong | Medium | Weak",
      "venue_b_rating": "Strong | Medium | Weak",
      "evidence": "Evidence-based explanation referencing the provided signals."
    }
  ],
  "key_risks": [
    {
      "venue": "A | B | Both",
      "risk": "Short risk.",
      "evidence": "Why this risk was identified from the evidence.",
      "mitigation": "Concrete action to reduce the risk."
    }
  ],
  "organizer_actions": [
    "Concrete action item."
  ],
  "attendee_logistics_email": "A ready-to-send attendee logistics email as plain text.",
  "evidence_sources": [
    "Box event checklist",
    "Apify nearby places",
    "Map/satellite visual evidence"
  ]
}

The tradeoff_matrix MUST contain exactly one row per evaluation criterion,
in this order: Accessibility, Nearby Amenities, Event Atmosphere,
Logistics Risk, Attendee Communication Needs.
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compare_venues(
    event_name: str,
    use_case: str,
    venue_a: Dict[str, Any],
    venue_b: Dict[str, Any],
    checklist_text: str = "",
) -> Dict[str, Any]:
    """
    Compare two venues and return the structured decision JSON.

    Args:
        event_name:     Event name, e.g. "Seattle AI Developer Meetup".
        use_case:       Free-text use case, e.g. "100-person AI developer event".
        venue_a:        Dict with keys:
                            "name"            -> str
                            "address"         -> str
                            "visual_signals"  -> Jingyi's GeoVisualSignals dict
                            "poi_summary"     -> poi_aggregator.aggregate_pois output
        venue_b:        Same shape as venue_a.
        checklist_text: Event venue checklist text read from Box (optional).

    Returns:
        Decision dict matching the schema documented in SYSTEM_PROMPT.
    """
    if USE_MOCK_DATA or not os.getenv("ANTHROPIC_API_KEY"):
        return _mock_decision(venue_a, venue_b)

    try:
        return _decide_with_anthropic(
            event_name, use_case, venue_a, venue_b, checklist_text
        )
    except Exception as e:
        print(f"[agent_service] Decision agent failed, using mock: {e}")
        return _mock_decision(venue_a, venue_b)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_user_content(
    event_name: str,
    use_case: str,
    venue_a: Dict[str, Any],
    venue_b: Dict[str, Any],
    checklist_text: str,
) -> str:
    """Inject the runtime evidence into the user message."""

    def venue_block(label: str, venue: Dict[str, Any]) -> str:
        return (
            f"== Venue {label}: {venue.get('name', 'Unknown')} ==\n"
            f"Address: {venue.get('address', 'Unknown')}\n"
            f"Map/satellite visual signals (JSON):\n"
            f"{json.dumps(venue.get('visual_signals', {}), ensure_ascii=False, indent=2)}\n"
            f"Nearby places POI summary (JSON):\n"
            f"{json.dumps(venue.get('poi_summary', {}), ensure_ascii=False, indent=2)}\n"
        )

    checklist = checklist_text.strip() or "(No checklist provided — use the five default criteria.)"

    return (
        f"Event: {event_name or 'Unnamed event'}\n"
        f"Use case: {use_case or 'developer event venue evaluation'}\n\n"
        f"== Box Event Venue Checklist ==\n{checklist}\n\n"
        f"{venue_block('A', venue_a)}\n"
        f"{venue_block('B', venue_b)}"
    )


def _decide_with_anthropic(
    event_name: str,
    use_case: str,
    venue_a: Dict[str, Any],
    venue_b: Dict[str, Any],
    checklist_text: str,
) -> Dict[str, Any]:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_content = _build_user_content(
        event_name, use_case, venue_a, venue_b, checklist_text
    )

    response = client.messages.create(
        model=LLM_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    text = response.content[0].text
    # Extract the JSON object even if the model wraps it in prose/fences.
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


# ---------------------------------------------------------------------------
# Mock fallback — keeps the demo alive if the LLM is unavailable.
# Lightly grounded in the actual signals so it still feels real.
# ---------------------------------------------------------------------------

def _mock_decision(venue_a: Dict[str, Any], venue_b: Dict[str, Any]) -> Dict[str, Any]:
    a_name = venue_a.get("name", "Venue A")
    b_name = venue_b.get("name", "Venue B")
    a_sig = venue_a.get("visual_signals", {})
    b_sig = venue_b.get("visual_signals", {})
    a_poi = venue_a.get("poi_summary", {})
    b_poi = venue_b.get("poi_summary", {})

    def amenities_rating(poi: Dict[str, Any]) -> str:
        total = (poi.get("restaurants_count", 0) + poi.get("coffee_count", 0)
                 + poi.get("bars_count", 0))
        return "Strong" if total >= 15 else "Medium" if total >= 6 else "Weak"

    def access_rating(sig: Dict[str, Any]) -> str:
        road = sig.get("road_access", "unknown")
        return {"strong": "Strong", "moderate": "Medium", "weak": "Weak"}.get(road, "Medium")

    matrix = [
        {
            "criterion": "Accessibility",
            "venue_a_rating": access_rating(a_sig),
            "venue_b_rating": access_rating(b_sig),
            "evidence": "Based on road access signals from map imagery.",
        },
        {
            "criterion": "Nearby Amenities",
            "venue_a_rating": amenities_rating(a_poi),
            "venue_b_rating": amenities_rating(b_poi),
            "evidence": "Based on nearby restaurant, coffee, and bar counts from POI data.",
        },
        {
            "criterion": "Event Atmosphere",
            "venue_a_rating": "Strong" if a_sig.get("water_nearby") else "Medium",
            "venue_b_rating": "Strong" if b_sig.get("water_nearby") else "Medium",
            "evidence": "Based on land use context and visible surroundings.",
        },
        {
            "criterion": "Logistics Risk",
            "venue_a_rating": "Weak" if a_sig.get("visible_parking") == "limited" else "Medium",
            "venue_b_rating": "Weak" if b_sig.get("visible_parking") == "limited" else "Medium",
            "evidence": "Based on visible parking constraints and road access.",
        },
        {
            "criterion": "Attendee Communication Needs",
            "venue_a_rating": "Medium",
            "venue_b_rating": "Medium",
            "evidence": "Both venues need clear arrival, parking, and transit guidance.",
        },
    ]

    risks = []
    for label, sig in (("A", a_sig), ("B", b_sig)):
        for r in sig.get("risks", [])[:2]:
            risks.append({
                "venue": label,
                "risk": r,
                "evidence": "Identified from map/satellite visual signals.",
                "mitigation": "Confirm on-site and arrange alternatives in advance.",
            })

    return {
        "overall_recommendation": (
            f"{a_name} suits a professional, weekday developer event with strong road "
            f"access, while {b_name} leans social with more walkable amenities. Choose "
            f"based on whether venue character or nearby food/after-party options matter more."
        ),
        "venue_a_positioning": f"{a_name} is best for a focused, professional event with easy arrival.",
        "venue_b_positioning": f"{b_name} is best for a social event with strong nearby amenities.",
        "tradeoff_matrix": matrix,
        "key_risks": risks or [{
            "venue": "Both",
            "risk": "Parking and arrival logistics unconfirmed.",
            "evidence": "Visual parking signals were limited or unknown.",
            "mitigation": "Recommend rideshare and confirm parking with each venue.",
        }],
        "organizer_actions": [
            "Confirm parking capacity and reserve overflow options for the chosen venue.",
            "Verify A/V setup and capacity for the expected headcount.",
            "Identify rideshare drop-off zones and share them with attendees.",
            "Book a nearby restaurant or bar block for post-event networking.",
        ],
        "attendee_logistics_email": (
            "Subject: Getting to the event\n\n"
            "Hi everyone,\n\n"
            "Here are the logistics for the event. Rideshare is recommended as parking "
            "may be limited; drop-off is available at the main entrance. Several "
            "restaurants and coffee shops are within a short walk. We'll follow up with "
            "the confirmed venue and a detailed map.\n\nSee you there!"
        ),
        "evidence_sources": [
            "Box event checklist",
            "Apify nearby places",
            "Map/satellite visual evidence",
        ],
    }


# ---------------------------------------------------------------------------
# Standalone smoke test:  python DataAnalysis/agent_service.py
# Runs against mock inputs so Simin can iterate without the full pipeline.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_a = {
        "name": "thinkspace Seattle",
        "address": "1700 Westlake Ave N #200, Seattle, WA 98109",
        "visual_signals": {
            "water_nearby": False, "green_space_level": "medium",
            "building_density": "high", "road_access": "strong",
            "visible_parking": "limited", "land_use_context": "commercial_office",
            "observations": ["Dense commercial district with office buildings."],
            "risks": ["Street parking likely constrained during business hours."],
            "confidence": "medium",
        },
        "poi_summary": {
            "restaurants_count": 12, "coffee_count": 5, "parking_count": 3,
            "hotels_count": 4, "bars_count": 6, "average_rating": 4.2,
        },
    }
    demo_b = {
        "name": "Demo Venue B",
        "address": "Capitol Hill, Seattle, WA",
        "visual_signals": {
            "water_nearby": True, "green_space_level": "low",
            "building_density": "medium", "road_access": "moderate",
            "visible_parking": "moderate", "land_use_context": "mixed",
            "observations": ["Mixed-use neighborhood with surface parking nearby."],
            "risks": ["Moderate road access may cause congestion during arrivals."],
            "confidence": "medium",
        },
        "poi_summary": {
            "restaurants_count": 18, "coffee_count": 8, "parking_count": 5,
            "hotels_count": 6, "bars_count": 9, "average_rating": 4.3,
        },
    }

    result = compare_venues(
        event_name="Seattle AI Developer Meetup",
        use_case="100-person AI developer event",
        venue_a=demo_a,
        venue_b=demo_b,
        checklist_text="",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
