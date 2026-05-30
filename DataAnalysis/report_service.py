"""
Simin - Report generation layer.

Takes the Decision Agent output (agent_service.compare_venues) plus the
per-venue evidence and renders the human-readable deliverables that make up
the SiteLens planning packet:

    - venue_comparison_report.md   (main report)
    - venue_a_site_packet.md       (per-venue detail)
    - venue_b_site_packet.md
    - organizer_action_checklist.md
    - attendee_logistics_email.md
    - nearby_places_summary.csv    (POI evidence table)

Pure formatting — no LLM calls, no analysis. Templates follow design doc S21.

Input contract:
    decision: dict from agent_service.compare_venues()
    venues:   list of dicts, each:
                {
                  "name": str,
                  "address": str,
                  "visual_signals": GeoVisualSignals dict (Jingyi),
                  "poi_summary":    poi_aggregator.aggregate_pois output (Simin),
                }
"""

import os
import io
import csv
import re
from datetime import datetime
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Small formatting helpers
# ---------------------------------------------------------------------------

def _bullets(items: List[str], empty: str = "- None identified") -> str:
    items = [i for i in (items or []) if str(i).strip()]
    if not items:
        return empty
    return "\n".join(f"- {i}" for i in items)


def _venue_label(index: int) -> str:
    """0 -> 'A', 1 -> 'B', ..."""
    return chr(ord("A") + index)


def _venue_key(index: int) -> str:
    """0 -> 'venue_a', 1 -> 'venue_b', ..."""
    return f"venue_{chr(ord('a') + index)}"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", (text or "").strip().lower())
    return slug.strip("-") or "event"


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _score_cell(score: Any, rating: str) -> str:
    """Render one score cell as 'X.X (Rating)' on the shared 0-5 scale."""
    if score is None or score == "":
        return rating or "-"
    try:
        score = float(score)
    except (TypeError, ValueError):
        return rating or "-"
    return f"{score:.1f} ({rating})" if rating else f"{score:.1f}"


def _edge_label(edge: str, a_name: str, b_name: str) -> str:
    return {"A": a_name, "B": b_name}.get(edge, "Even")


def _render_tradeoff_table(decision: Dict[str, Any], venues: List[Dict]) -> str:
    a_name = venues[0]["name"] if len(venues) > 0 else "Venue A"
    b_name = venues[1]["name"] if len(venues) > 1 else "Venue B"

    # All scores are on a single 0-5 scale (5 = best; for Logistics Risk a
    # higher score means lower risk), so the table stays internally consistent.
    header = (
        f"| Criterion | {a_name} (0–5) | {b_name} (0–5) | Edge | Evidence |\n"
        f"|---|---|---|---|---|\n"
    )
    rows = []
    for row in decision.get("tradeoff_matrix", []):
        rows.append(
            f"| {row.get('criterion', '')} "
            f"| {_score_cell(row.get('venue_a_score'), row.get('venue_a_rating', ''))} "
            f"| {_score_cell(row.get('venue_b_score'), row.get('venue_b_rating', ''))} "
            f"| {_edge_label(row.get('edge', 'Tie'), a_name, b_name)} "
            f"| {row.get('evidence', '')} |"
        )
    if not rows:
        return header + "| _No comparison data available_ |  |  |  |  |"

    # Overall row = mean of the five criteria above, same 0-5 scale.
    a_overall = decision.get("venue_a_overall_score")
    b_overall = decision.get("venue_b_overall_score")
    overall_edge = "Tie"
    if a_overall is not None and b_overall is not None:
        overall_edge = "A" if a_overall > b_overall else "B" if b_overall > a_overall else "Tie"
    rows.append(
        f"| **Overall (0–5)** "
        f"| **{a_overall if a_overall is not None else '-'}** "
        f"| **{b_overall if b_overall is not None else '-'}** "
        f"| **{_edge_label(overall_edge, a_name, b_name)}** "
        f"| Mean of the five criteria above. |"
    )
    return header + "\n".join(rows)


def _render_key_risks(decision: Dict[str, Any]) -> str:
    risks = decision.get("key_risks", [])
    if not risks:
        return "_No key risks identified._"
    blocks = []
    for r in risks:
        blocks.append(
            f"- **Venue {r.get('venue', '?')} — {r.get('risk', '')}**\n"
            f"  - Evidence: {r.get('evidence', 'n/a')}\n"
            f"  - Mitigation: {r.get('mitigation', 'n/a')}"
        )
    return "\n".join(blocks)


def _render_poi_summary(poi: Dict[str, Any]) -> str:
    poi = poi or {}
    counts = poi.get("category_counts") or {
        "restaurant": poi.get("restaurants_count", 0),
        "coffee": poi.get("coffee_count", 0),
        "parking": poi.get("parking_count", 0),
        "hotel": poi.get("hotels_count", 0),
        "bar": poi.get("bars_count", 0),
        "convenience": poi.get("convenience_count", 0),
        "transit": poi.get("transit_count", 0),
    }
    count_line = ", ".join(f"{k}: {v}" for k, v in counts.items())

    avg = poi.get("average_rating")
    avg_line = f"\n\n**Average nearby rating:** {avg}" if avg else ""

    top = poi.get("top_places", [])[:5]
    if top:
        top_lines = "\n".join(
            f"- {p.get('name', 'Unknown')} "
            f"({p.get('category', 'place')}"
            + (f", {p.get('rating')}★" if p.get("rating") else "")
            + (f", {p.get('review_count')} reviews"
               if p.get("review_count") else "")
            + ")"
            for p in top
        )
    else:
        top_lines = "- No notable places available"

    return (
        f"**Nearby counts:** {count_line}{avg_line}\n\n"
        f"**Notable nearby places:**\n{top_lines}"
    )


# ---------------------------------------------------------------------------
# File generators (design doc S23)
# ---------------------------------------------------------------------------

def generate_comparison_report(
    event_name: str,
    use_case: str,
    decision: Dict[str, Any],
    venues: List[Dict[str, Any]],
) -> str:
    a_name = venues[0]["name"] if len(venues) > 0 else "Venue A"
    b_name = venues[1]["name"] if len(venues) > 1 else "Venue B"

    a_overall = decision.get("venue_a_overall_score")
    b_overall = decision.get("venue_b_overall_score")
    rec_name = decision.get("recommended_venue_name")
    scores_line = (
        f"**Overall scores (0–5):** {a_name} {a_overall if a_overall is not None else '-'} · "
        f"{b_name} {b_overall if b_overall is not None else '-'}"
        + (f" → **Recommended: {rec_name}**" if rec_name else "")
    )

    return f"""# SiteLens Venue Comparison Report

## Event
{event_name or "Unnamed event"}

## Use Case
{use_case or "Developer event venue evaluation"}

## Overall Recommendation
{decision.get("overall_recommendation", "_No recommendation generated._")}

{scores_line}

## Venue Positioning

### Venue A: {a_name}
{decision.get("venue_a_positioning", "_n/a_")}

### Venue B: {b_name}
{decision.get("venue_b_positioning", "_n/a_")}

## Trade-off Matrix

{_render_tradeoff_table(decision, venues)}

## Key Risks and Mitigations

{_render_key_risks(decision)}

## Organizer Action Items

{_bullets(decision.get("organizer_actions"), "- No actions generated")}

## Evidence Sources

{_bullets(decision.get("evidence_sources"), "- n/a")}
"""


def generate_site_packet(
    venue: Dict[str, Any],
    positioning: str = "",
    venue_risks: List[Dict[str, Any]] = None,
) -> str:
    sig = venue.get("visual_signals", {}) or {}
    venue_risks = venue_risks or []

    observations = _bullets(sig.get("observations"), "- No observations available")
    risk_lines = _bullets(sig.get("risks"), "- No risks identified")

    actions = [r.get("mitigation", "") for r in venue_risks]
    actions_block = _bullets(actions, "- See main comparison report")

    return f"""# Site Packet: {venue.get("name", "Venue")}

## Address
{venue.get("address", "Unknown")}

## Map / Satellite Observations
{observations}

## Nearby Place Summary
{_render_poi_summary(venue.get("poi_summary", {}))}

## Strengths
{positioning or "_See main comparison report._"}

## Risks
{risk_lines}

## Recommended Organizer Actions
{actions_block}
"""


def generate_action_checklist(decision: Dict[str, Any]) -> str:
    actions = decision.get("organizer_actions", [])
    if not actions:
        actions = ["No actions generated."]
    lines = "\n".join(f"- [ ] {a}" for a in actions)
    return f"""# Organizer Action Checklist

{lines}
"""


def generate_attendee_email(event_name: str, decision: Dict[str, Any]) -> str:
    email = decision.get("attendee_logistics_email", "_No email generated._")
    return f"""# Attendee Logistics Email

Subject: Getting to {event_name or "the event"}

{email}
"""


def generate_nearby_places_csv(venues: List[Dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Venue", "Name", "Category", "Rating", "Reviews", "Address"])
    for i, venue in enumerate(venues):
        label = venue.get("name") or f"Venue {_venue_label(i)}"
        for p in (venue.get("poi_summary", {}) or {}).get("top_places", []):
            writer.writerow([
                label,
                p.get("name", ""),
                p.get("category", ""),
                p.get("rating", ""),
                p.get("review_count", ""),
                p.get("address", ""),
            ])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def build_packet_files(
    event_name: str,
    use_case: str,
    decision: Dict[str, Any],
    venues: List[Dict[str, Any]],
) -> Dict[str, str]:
    """
    Render every packet file in-memory. Returns {filename: content}.
    box_service / write_outputs_to_disk consume this mapping.
    """
    files: Dict[str, str] = {
        "venue_comparison_report.md": generate_comparison_report(
            event_name, use_case, decision, venues
        ),
        "organizer_action_checklist.md": generate_action_checklist(decision),
        "attendee_logistics_email.md": generate_attendee_email(event_name, decision),
        "nearby_places_summary.csv": generate_nearby_places_csv(venues),
    }

    for i, venue in enumerate(venues):
        positioning = decision.get(f"{_venue_key(i)}_positioning", "")
        label = _venue_label(i)
        venue_risks = [
            r for r in decision.get("key_risks", [])
            if str(r.get("venue", "")).upper() in (label, "BOTH")
        ]
        files[f"{_venue_key(i)}_site_packet.md"] = generate_site_packet(
            venue, positioning, venue_risks
        )

    return files


def write_outputs_to_disk(
    event_name: str,
    use_case: str,
    decision: Dict[str, Any],
    venues: List[Dict[str, Any]],
    output_root: str = "outputs",
) -> List[str]:
    """
    Render the packet and write it to a unique local folder so repeated runs
    do not overwrite each other:  outputs/{event-slug}_{YYYYmmdd-HHMMSS}/

    Returns the list of written file paths.
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    folder_name = f"{_slugify(event_name)}_{timestamp}"
    folder = os.path.join(output_root, folder_name)
    os.makedirs(folder, exist_ok=True)

    files = build_packet_files(event_name, use_case, decision, venues)

    written = []
    for filename, content in files.items():
        path = os.path.join(folder, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# Standalone smoke test:  python DataAnalysis/report_service.py
# Uses agent_service's mock decision + sample venues to render real files.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from agent_service import compare_venues

    demo_venues = [
        {
            "name": "thinkspace Seattle",
            "address": "1700 Westlake Ave N #200, Seattle, WA 98109",
            "visual_signals": {
                "building_density": "high", "road_access": "strong",
                "visible_parking": "limited", "land_use_context": "commercial_office",
                "observations": ["Dense commercial district with office buildings."],
                "risks": ["Street parking likely constrained during business hours."],
                "confidence": "medium",
            },
            "poi_summary": {
                "category_counts": {"restaurant": 12, "coffee": 5, "parking": 3,
                                    "hotel": 4, "bar": 6, "convenience": 2, "transit": 3},
                "average_rating": 4.2,
                "top_places": [
                    {"name": "Westlake Grill", "category": "restaurant",
                     "rating": 4.3, "review_count": 210, "address": "Seattle, WA"},
                    {"name": "Lake Union Coffee", "category": "coffee",
                     "rating": 4.5, "review_count": 88, "address": "Seattle, WA"},
                ],
            },
        },
        {
            "name": "Capitol Hill Event Space",
            "address": "Capitol Hill, Seattle, WA",
            "visual_signals": {
                "water_nearby": True, "building_density": "medium",
                "road_access": "moderate", "visible_parking": "moderate",
                "land_use_context": "mixed",
                "observations": ["Mixed-use neighborhood with surface parking nearby."],
                "risks": ["Moderate road access may cause congestion during arrivals."],
                "confidence": "medium",
            },
            "poi_summary": {
                "category_counts": {"restaurant": 18, "coffee": 8, "parking": 5,
                                    "hotel": 6, "bar": 9, "convenience": 4, "transit": 5},
                "average_rating": 4.3,
                "top_places": [
                    {"name": "Capitol Hill Bistro", "category": "restaurant",
                     "rating": 4.1, "review_count": 320, "address": "Seattle, WA"},
                ],
            },
        },
    ]

    decision = compare_venues(
        event_name="Seattle AI Developer Meetup",
        use_case="100-person AI developer event",
        venue_a=demo_venues[0],
        venue_b=demo_venues[1],
        checklist_text="",
    )

    paths = write_outputs_to_disk(
        "Seattle AI Developer Meetup",
        "100-person AI developer event",
        decision,
        demo_venues,
    )
    print("Wrote packet files:")
    for p in paths:
        print(" ", p)
