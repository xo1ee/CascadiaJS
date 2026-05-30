/** User-entered venue — id, name, address only */
export type VenueInput = {
  id: string;
  name: string;
  address: string;
};

export type VisualSignals = {
  water_nearby?: boolean | null;
  green_space_level?: string;
  building_density?: string;
  road_access?: string;
  visible_parking?: string;
  land_use_context?: string;
  observations?: string[];
  risks?: string[];
  confidence?: string;
};

export type PoiSummary = {
  category_counts?: Record<string, number>;
  /** Legacy flat counts from older POI payloads */
  restaurants_count?: number;
  coffee_count?: number;
  parking_count?: number;
  hotels_count?: number;
  bars_count?: number;
  top_places?: Array<{
    name: string;
    category: string;
    rating?: number;
    review_count?: number;
    address?: string;
  }>;
  average_rating?: number;
};

/** AI-generated evidence and summary for one venue */
export type VenueAnalysis = {
  name: string;
  address: string;
  summary?: string;
  overall_score?: number;
  visual_signals?: VisualSignals;
  poi_summary?: PoiSummary;
  site_packet_markdown?: string;
  map_url?: string;
  satellite_url?: string;
};

export type TradeoffRow = {
  criterion: string;
  venue_a_score?: number;
  venue_b_score?: number;
  venue_a_rating?: string;
  venue_b_rating?: string;
  /** Used when comparing N venues */
  venue_ratings?: string[];
  edge?: string;
  evidence: string;
};

export type KeyRisk = {
  venue: string;
  risk: string;
  evidence: string;
  mitigation: string;
};

export type BoxOutput = {
  name: string;
  box_file_id: string;
  url?: string;
};

/** Full response from POST /api/analyze-venues */
export type AnalyzeVenuesResponse = {
  overall_recommendation: string;
  recommended_venue?: "A" | "B" | null;
  recommended_venue_name?: string | null;
  venues: VenueAnalysis[];
  tradeoff_matrix: TradeoffRow[];
  key_risks?: KeyRisk[];
  organizer_actions: string[];
  attendee_logistics_email: string;
  box_outputs?: BoxOutput[];
  evidence_sources?: string[];
};
