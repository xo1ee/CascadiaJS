import type { AnalyzeVenuesResponse, VenueInput } from "./types";

const DEFAULT_API_BASE = "http://localhost:8000";

export function getApiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_BASE;
  return base.replace(/\/$/, "");
}

export type AnalyzeVenuesRequest = {
  event_name: string;
  use_case: string;
  venues: VenueInput[];
};

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function analyzeVenues(
  request: AnalyzeVenuesRequest,
): Promise<AnalyzeVenuesResponse> {
  const res = await fetch(`${getApiBase()}/api/analyze-venues`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.text();
      if (body) message = body;
    } catch {
      // keep default message
    }
    throw new ApiError(message, res.status);
  }

  return res.json() as Promise<AnalyzeVenuesResponse>;
}
