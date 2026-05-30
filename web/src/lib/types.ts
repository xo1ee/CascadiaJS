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
  /** Overall 0-5 score = mean of the per-criterion scores (null if no matrix) */
  overall_score?: number | null;
  visual_signals?: VisualSignals;
  poi_summary?: PoiSummary;
  site_packet_markdown?: string;
  map_url?: string;
  satellite_url?: string;
};

export type TradeoffRow = {
  criterion: string;
  /** 0-5 per-criterion scores */
  venue_a_score?: number;
  venue_b_score?: number;
  /** Derived rating bands (Strong | Medium | Weak) */
  venue_a_rating?: string;
  venue_b_rating?: string;
  /** Which venue wins this criterion: "A" | "B" | "Tie" */
  edge?: string;
  /** Used when comparing N venues */
  venue_ratings?: string[];
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
  /** "A" | "B" — which venue is recommended */
  recommended_venue?: string;
  recommended_venue_name?: string;
  venues: VenueAnalysis[];
  tradeoff_matrix: TradeoffRow[];
  key_risks?: KeyRisk[];
  organizer_actions: string[];
  attendee_logistics_email: string;
  box_outputs?: BoxOutput[];
  evidence_sources?: string[];
};
