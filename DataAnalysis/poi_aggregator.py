import json
from typing import Any, Dict, List, Optional


CATEGORY_MAP = {
    "restaurant": ["restaurant", "food", "dining", "meal_takeaway", "meal_delivery"],
    "coffee": ["coffee", "cafe", "coffee shop", "bakery"],
    "parking": ["parking", "parking lot", "parking garage"],
    "hotel": ["hotel", "lodging", "motel"],
    "bar": ["bar", "pub", "night club", "brewery"],
    "convenience": ["convenience store", "supermarket", "grocery store", "grocery"],
    "transit": [
        "bus stop", "bus station", "subway station", "metro station",
        "train station", "light rail", "transit station", "transit stop",
        "tram stop", "public transit"
    ],
}


def get_first(place: Dict[str, Any], keys: List[str], default=None):
    for key in keys:
        if key in place and place[key] not in [None, ""]:
            return place[key]
    return default


def normalize_category(place: Dict[str, Any]) -> str:
    raw_values = []

    for key in ["category", "categoryName", "type", "placeType"]:
        value = place.get(key)
        if isinstance(value, str):
            raw_values.append(value.lower())

    # Some APIs return categories/types as a list
    for key in ["categories", "types"]:
        value = place.get(key)
        if isinstance(value, list):
            raw_values.extend([str(v).lower() for v in value])

    raw_text = " ".join(raw_values)

    for normalized, keywords in CATEGORY_MAP.items():
        for keyword in keywords:
            if keyword in raw_text:
                return normalized

    return "other"


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int:
    try:
        if value is None or value == "":
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def aggregate_pois(raw_places: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Any]:
    counts = {
        "restaurants_count": 0,
        "coffee_count": 0,
        "parking_count": 0,
        "hotels_count": 0,
        "bars_count": 0,
        "convenience_count": 0,
        "transit_count": 0
    }

    # Nested dict matching the frontend contract (PoiSummary.category_counts
    # in web/src/lib/types.ts). Keys mirror normalize_category() output.
    category_counts = {
        "restaurant": 0,
        "coffee": 0,
        "parking": 0,
        "hotel": 0,
        "bar": 0,
        "convenience": 0,
        "transit": 0,
    }

    normalized_places = []
    ratings = []

    for place in raw_places:
        category = normalize_category(place)

        if category in category_counts:
            category_counts[category] += 1

        if category == "restaurant":
            counts["restaurants_count"] += 1
        elif category == "coffee":
            counts["coffee_count"] += 1
        elif category == "parking":
            counts["parking_count"] += 1
        elif category == "hotel":
            counts["hotels_count"] += 1
        elif category == "bar":
            counts["bars_count"] += 1
        elif category == "convenience":
            counts["convenience_count"] += 1
        elif category == "transit":
            counts["transit_count"] += 1

        rating = safe_float(get_first(place, ["rating", "totalScore", "stars", "score"]))
        review_count = safe_int(get_first(place, ["review_count", "reviewsCount", "reviews", "userRatingsTotal"]))

        if rating is not None:
            ratings.append(rating)

        normalized_places.append({
            "name": get_first(place, ["name", "title"], "Unknown place"),
            "category": category,
            "rating": rating,
            "review_count": review_count,
            "address": get_first(place, ["address", "formattedAddress", "vicinity"], ""),
            "distance_meters": safe_float(get_first(place, ["distance_meters", "distanceMeters", "distance"]))
        })

    # Sort by review_count first, then rating
    top_places = sorted(
        normalized_places,
        key=lambda x: (x["review_count"], x["rating"] or 0),
        reverse=True
    )[:top_n]

    average_rating = round(sum(ratings) / len(ratings), 2) if ratings else None

    return {
        **counts,
        "category_counts": category_counts,
        "average_rating": average_rating,
        "total_places": len(raw_places),
        "top_places": top_places
    }


def aggregate_from_file(input_path: str, output_path: str) -> Dict[str, Any]:
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Some Apify outputs may wrap places inside a key
    if isinstance(raw_data, dict):
        raw_places = (
                raw_data.get("places")
                or raw_data.get("results")
                or raw_data.get("data")
                or []
        )
    else:
        raw_places = raw_data

    result = aggregate_pois(raw_places)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result
