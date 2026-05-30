"""
Jingyi - Geospatial Analysis
Sends map/satellite images to a vision model and extracts structured site signals.
Pipeline: image_path -> GeoVisualSignals dict
"""

import os
import json
import base64
from pathlib import Path

USE_MOCK_DATA = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

VISION_PROMPT = """\
You are a site intelligence analyst helping evaluate event venues.

Analyze the provided map or satellite image as visual evidence only. Do not overclaim. \
Extract visible site signals relevant to a 100-person developer event.

Return strict JSON with these fields:

{
  "water_nearby": true | false | null,
  "green_space_level": "low" | "medium" | "high" | "unknown",
  "building_density": "low" | "medium" | "high" | "unknown",
  "road_access": "weak" | "moderate" | "strong" | "unknown",
  "visible_parking": "limited" | "moderate" | "strong" | "unknown",
  "land_use_context": "commercial_office" | "residential" | "industrial" | "mixed" | "unknown",
  "observations": ["Short evidence-based observation."],
  "risks": ["Short risk inferred from visible evidence."],
  "confidence": "low" | "medium" | "high"
}

Rules:
- Only mention things that are visible or reasonably inferable from the image.
- Do not claim exact traffic, crime, demographic, or foot traffic data.
- Do not call this NDVI or professional remote sensing.
- Use map/satellite visual signals as one evidence layer only.
- If uncertain, use "unknown" or set confidence to "low".
"""

# Mock response used when USE_MOCK_DATA=true or when the vision API is unavailable.
# Two variants so venue_a and venue_b feel different in demo mode.
_MOCK_SIGNALS_A = {
    "water_nearby": False,
    "green_space_level": "medium",
    "building_density": "high",
    "road_access": "strong",
    "visible_parking": "limited",
    "land_use_context": "commercial_office",
    "observations": [
        "Dense commercial district with multi-story office buildings.",
        "Multiple road intersections visible, suggesting strong street-level access.",
        "Limited surface parking in the immediate vicinity.",
        "Proximity to a waterway corridor visible to the west.",
    ],
    "risks": [
        "High building density may reduce drop-off and loading zone options.",
        "Street parking likely constrained during peak business hours.",
    ],
    "confidence": "medium",
}

_MOCK_SIGNALS_B = {
    "water_nearby": True,
    "green_space_level": "low",
    "building_density": "medium",
    "road_access": "moderate",
    "visible_parking": "moderate",
    "land_use_context": "mixed",
    "observations": [
        "Mixed-use neighborhood with lower building density than SLU.",
        "Surface parking lots visible nearby.",
        "Waterway visible within one block.",
        "Fewer road access points compared to downtown core.",
    ],
    "risks": [
        "Moderate road access may cause congestion during large arrivals.",
        "Mixed land use may reduce late-night transit frequency.",
    ],
    "confidence": "medium",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_site_image(image_path: str, venue_key: str = "") -> dict:
    """
    Analyzes a map or satellite image and returns structured visual site signals.

    Args:
        image_path: Path to a PNG or JPEG map/satellite image.
        venue_key:  Optional hint for mock data selection ('venue_a' or 'venue_b').

    Returns:
        Dict matching GeoVisualSignals schema.
    """
    if USE_MOCK_DATA or not Path(image_path).exists():
        return _mock_signals(venue_key)

    try:
        return _analyze_with_anthropic(image_path)
    except Exception as e:
        print(f"[vision_service] Vision analysis failed, using mock: {e}")
        return _mock_signals(venue_key)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _mock_signals(venue_key: str) -> dict:
    if "venue_b" in venue_key:
        return dict(_MOCK_SIGNALS_B)
    return dict(_MOCK_SIGNALS_A)


def _analyze_with_anthropic(image_path: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    image_bytes = Path(image_path).read_bytes()
    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
    # Detect actual format from magic bytes, not file extension
    # (Mapbox returns JPEG even when saved as .png)
    if image_bytes[:2] == b"\xff\xd8":
        media_type = "image/jpeg"
    else:
        media_type = "image/png"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": VISION_PROMPT},
                ],
            }
        ],
    )

    text = response.content[0].text
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])
