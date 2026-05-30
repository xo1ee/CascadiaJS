"""
Jingyi - Top-level geo pipeline orchestrator.
Kone's main.py and Simin's agent_service call run_geo_pipeline().

Full flow:
    address
    -> geocode_address()       -> (lat, lon)
    -> get_map_snapshots()     -> {map_path, satellite_path}
    -> analyze_site_image() x2 -> map_signals, satellite_signals
    -> build_geo_evidence()    -> GeoEvidence dict
"""

from services.mapbox_service import geocode_address, get_map_snapshots
from services.vision_service import analyze_site_image
from geo_evidence_schema import build_geo_evidence


def run_geo_pipeline(address: str, venue_key: str) -> dict:
    """
    Runs the full geo evidence pipeline for one venue.

    Args:
        address:    Human-readable venue address string.
        venue_key:  Short identifier, e.g. 'venue_a' or 'venue_b'.
                    Used for image filenames and mock data selection.

    Returns:
        GeoEvidence dict (see geo_evidence_schema.py).
        Ready to be passed into Simin's agent_service.compare_venues().
    """
    lat, lon = geocode_address(address)
    snapshots = get_map_snapshots(lat, lon, venue_key)
    map_signals = analyze_site_image(snapshots["map_path"], venue_key)
    satellite_signals = analyze_site_image(snapshots["satellite_path"], venue_key)
    return build_geo_evidence(address, lat, lon, snapshots, map_signals, satellite_signals)
