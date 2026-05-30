"""
Shared schema for Jingyi's geo evidence output.
Simin's analysis module consumes this as input.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel


class GeoVisualSignals(BaseModel):
    water_nearby: Optional[bool] = None
    green_space_level: Literal["low", "medium", "high", "unknown"] = "unknown"
    building_density: Literal["low", "medium", "high", "unknown"] = "unknown"
    road_access: Literal["weak", "moderate", "strong", "unknown"] = "unknown"
    visible_parking: Literal["limited", "moderate", "strong", "unknown"] = "unknown"
    land_use_context: Literal[
        "commercial_office", "residential", "industrial", "mixed", "unknown"
    ] = "unknown"
    observations: List[str] = []
    risks: List[str] = []
    confidence: Literal["low", "medium", "high"] = "low"


class GeoEvidence(BaseModel):
    """
    Structured geo evidence for one venue.
    Produced by Jingyi's pipeline; consumed by Simin's agent_service.
    """
    address: str
    lat: float
    lon: float
    map_path: str
    satellite_path: str
    map_signals: GeoVisualSignals
    satellite_signals: GeoVisualSignals


def build_geo_evidence(
    address: str,
    lat: float,
    lon: float,
    snapshots: dict,
    map_signals: dict,
    satellite_signals: dict,
) -> dict:
    """
    Combines geocoding output, map snapshots, and visual signals into a
    single GeoEvidence dict for Simin's analysis module.
    """
    return GeoEvidence(
        address=address,
        lat=lat,
        lon=lon,
        map_path=snapshots["map_path"],
        satellite_path=snapshots["satellite_path"],
        map_signals=GeoVisualSignals(**map_signals),
        satellite_signals=GeoVisualSignals(**satellite_signals),
    ).model_dump()
