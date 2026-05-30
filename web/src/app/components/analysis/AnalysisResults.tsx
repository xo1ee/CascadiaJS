"use client";

import type {
  AnalyzeVenuesResponse,
  PoiSummary,
  TradeoffRow,
  VenueAnalysis,
  VisualSignals,
} from "@/lib/types";

const sectionClassName =
  "rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 sm:p-8";

const sectionTitleClassName =
  "mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400";

function venueLabel(index: number): string {
  return String.fromCharCode(65 + index);
}

function ratingBadgeClass(rating?: string): string {
  const base = "inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold";
  switch (rating) {
    case "Strong":
      return `${base} bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-200`;
    case "Medium":
      return `${base} bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-200`;
    case "Weak":
      return `${base} bg-red-100 text-red-800 dark:bg-red-950/60 dark:text-red-200`;
    default:
      return `${base} bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300`;
  }
}

function scoreCell(score?: number, rating?: string): string {
  if (score == null) return rating ?? "—";
  return rating ? `${score.toFixed(1)} (${rating})` : score.toFixed(1);
}

function edgeLabel(edge: string | undefined, venueNames: string[]): string {
  if (!edge || edge === "Tie") return "Even";
  const idx = edge === "A" ? 0 : edge === "B" ? 1 : -1;
  if (idx >= 0 && venueNames[idx]) return venueNames[idx];
  return edge;
}

function normalizePoiCounts(poi?: PoiSummary): Array<{ label: string; count: number }> {
  if (!poi) return [];
  const counts = poi.category_counts ?? {
    restaurant: poi.restaurants_count ?? 0,
    coffee: poi.coffee_count ?? 0,
    bar: poi.bars_count ?? 0,
    parking: poi.parking_count ?? 0,
    hotel: poi.hotels_count ?? 0,
  };
  return Object.entries(counts)
    .filter(([, count]) => count > 0)
    .map(([key, count]) => ({ label: key, count }));
}

function visualSignalTags(signals?: VisualSignals): string[] {
  if (!signals) return [];
  const tags: string[] = [];
  if (signals.water_nearby) tags.push("water nearby");
  if (signals.building_density) tags.push(`${signals.building_density} density`);
  if (signals.road_access) tags.push(`${signals.road_access} road access`);
  if (signals.visible_parking) tags.push(`${signals.visible_parking} parking`);
  if (signals.land_use_context) tags.push(signals.land_use_context.replace(/_/g, " "));
  if (signals.green_space_level) tags.push(`${signals.green_space_level} green space`);
  return tags;
}

function VenueAnalysisCard({
  analysis,
  index,
  isRecommended,
}: {
  analysis: VenueAnalysis;
  index: number;
  isRecommended: boolean;
}) {
  const poiCounts = normalizePoiCounts(analysis.poi_summary);
  const signals = visualSignalTags(analysis.visual_signals);

  return (
    <article
      className={`rounded-xl border p-5 ${
        isRecommended
          ? "border-emerald-200 bg-emerald-50/50 dark:border-emerald-900/50 dark:bg-emerald-950/20"
          : "border-zinc-100 bg-zinc-50/80 dark:border-zinc-800 dark:bg-zinc-950/50"
      }`}
    >
      <div className="mb-1 flex flex-wrap items-center gap-2">
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Venue {venueLabel(index)} · {analysis.name}
        </p>
        {isRecommended ? (
          <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
            Recommended
          </span>
        ) : null}
        {analysis.overall_score != null ? (
          <span className="ml-auto text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            {analysis.overall_score.toFixed(1)} / 5
          </span>
        ) : null}
      </div>
      <p className="mb-3 text-xs text-zinc-500 dark:text-zinc-400">{analysis.address}</p>

      {analysis.summary ? (
        <p className="mb-3 text-sm text-zinc-700 dark:text-zinc-300">{analysis.summary}</p>
      ) : null}

      <div className="grid grid-cols-2 gap-2">
        {analysis.map_url ? (
          <img
            src={analysis.map_url}
            alt={`Map for ${analysis.name}`}
            className="h-28 w-full rounded-lg border border-zinc-200 object-cover dark:border-zinc-700"
          />
        ) : null}
        {analysis.satellite_url ? (
          <img
            src={analysis.satellite_url}
            alt={`Satellite view for ${analysis.name}`}
            className="h-28 w-full rounded-lg border border-zinc-200 object-cover dark:border-zinc-700"
          />
        ) : null}
      </div>

      {poiCounts.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {poiCounts.map(({ label, count }) => (
            <span
              key={label}
              className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
            >
              <span className="font-semibold">{count}</span> {label}
            </span>
          ))}
          {analysis.poi_summary?.average_rating != null ? (
            <span className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
              ⭐ {analysis.poi_summary.average_rating.toFixed(1)} avg
            </span>
          ) : null}
        </div>
      ) : null}

      {signals.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {signals.map((tag) => (
            <span
              key={tag}
              className="rounded-md bg-indigo-50 px-2 py-0.5 text-[11px] text-indigo-800 dark:bg-indigo-950/50 dark:text-indigo-200"
            >
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      {analysis.poi_summary?.top_places && analysis.poi_summary.top_places.length > 0 ? (
        <div className="mt-4">
          <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Notable nearby
          </p>
          <ul className="space-y-1 text-xs text-zinc-600 dark:text-zinc-400">
            {analysis.poi_summary.top_places.slice(0, 3).map((place) => (
              <li key={`${place.name}-${place.category}`}>
                {place.name}
                {place.rating != null ? ` · ${place.rating}★` : ""}
                {place.category ? ` · ${place.category}` : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </article>
  );
}

function TradeoffMatrix({
  rows,
  venueNames,
  overallScores,
}: {
  rows: TradeoffRow[];
  venueNames: string[];
  overallScores: Array<number | undefined>;
}) {
  if (rows.length === 0) return null;

  const aName = venueNames[0] ?? "Venue A";
  const bName = venueNames[1] ?? "Venue B";
  const aOverall = overallScores[0];
  const bOverall = overallScores[1];

  return (
    <section className={sectionClassName}>
      <h2 className={sectionTitleClassName}>Trade-off Matrix</h2>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-zinc-200 dark:border-zinc-700">
              <th className="pb-2 pr-4 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                Criterion
              </th>
              <th className="pb-2 pr-4 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                {aName}
              </th>
              <th className="pb-2 pr-4 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                {bName}
              </th>
              <th className="pb-2 pr-4 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                Edge
              </th>
              <th className="pb-2 text-left text-[11px] font-semibold uppercase tracking-wide text-zinc-500">
                Evidence
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.criterion}
                className="border-b border-zinc-100 dark:border-zinc-800"
              >
                <td className="py-3 pr-4 font-medium text-zinc-900 dark:text-zinc-100">
                  {row.criterion}
                </td>
                <td className="py-3 pr-4">
                  <span className={ratingBadgeClass(row.venue_a_rating)}>
                    {scoreCell(row.venue_a_score, row.venue_a_rating)}
                  </span>
                </td>
                <td className="py-3 pr-4">
                  <span className={ratingBadgeClass(row.venue_b_rating)}>
                    {scoreCell(row.venue_b_score, row.venue_b_rating)}
                  </span>
                </td>
                <td className="py-3 pr-4 text-zinc-700 dark:text-zinc-300">
                  {edgeLabel(row.edge, venueNames)}
                </td>
                <td className="py-3 text-xs text-zinc-500 dark:text-zinc-400">
                  {row.evidence}
                </td>
              </tr>
            ))}
            {aOverall != null && bOverall != null ? (
              <tr className="bg-zinc-50/80 dark:bg-zinc-950/40">
                <td className="py-3 pr-4 font-semibold text-zinc-900 dark:text-zinc-100">
                  Overall (0–5)
                </td>
                <td className="py-3 pr-4 font-semibold">{aOverall.toFixed(1)}</td>
                <td className="py-3 pr-4 font-semibold">{bOverall.toFixed(1)}</td>
                <td className="py-3 pr-4 font-semibold">
                  {edgeLabel(
                    Math.abs(aOverall - bOverall) < 0.05
                      ? "Tie"
                      : aOverall > bOverall
                        ? "A"
                        : "B",
                    venueNames,
                  )}
                </td>
                <td className="py-3 text-xs text-zinc-500 dark:text-zinc-400">
                  Mean of the five criteria above.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function AnalysisResults({
  result,
  eventName,
}: {
  result: AnalyzeVenuesResponse;
  eventName: string;
}) {
  const venueNames = result.venues.map((v) => v.name);
  const recommendedIndex =
    result.recommended_venue === "B"
      ? 1
      : result.recommended_venue === "A"
        ? 0
        : -1;

  return (
    <div className="mt-8 space-y-6">

      <section className={sectionClassName}>
        <h2 className={sectionTitleClassName}>Venue Evidence</h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {result.venues.map((venue, index) => (
            <VenueAnalysisCard
              key={`${venue.name}-${venue.address}`}
              analysis={venue}
              index={index}
              isRecommended={index === recommendedIndex}
            />
          ))}
        </div>
      </section>

      <TradeoffMatrix
        rows={result.tradeoff_matrix}
        venueNames={venueNames}
        overallScores={result.venues.map((v) => v.overall_score)}
      />

      {result.key_risks && result.key_risks.length > 0 ? (
        <section className={sectionClassName}>
          <h2 className={sectionTitleClassName}>Key Risks &amp; Mitigations</h2>
          <div className="space-y-3">
            {result.key_risks.map((risk) => (
              <div
                key={`${risk.venue}-${risk.risk}`}
                className="rounded-r-lg border-l-[3px] border-amber-400 bg-amber-50/80 px-4 py-3 dark:border-amber-600 dark:bg-amber-950/30"
              >
                <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
                  Venue {risk.venue} — {risk.risk}
                </p>
                <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
                  Evidence: {risk.evidence}
                </p>
                <p className="mt-1 text-xs text-zinc-700 dark:text-zinc-300">
                  <span className="font-semibold text-emerald-700 dark:text-emerald-400">
                    Mitigation:
                  </span>{" "}
                  {risk.mitigation}
                </p>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {result.organizer_actions.length > 0 ? (
        <section className={sectionClassName}>
          <h2 className={sectionTitleClassName}>Organizer Action Checklist</h2>
          <ul className="space-y-2">
            {result.organizer_actions.map((action) => (
              <li
                key={action}
                className="flex gap-3 border-b border-zinc-100 py-2 text-sm text-zinc-800 last:border-0 dark:border-zinc-800 dark:text-zinc-200"
              >
                <span className="text-emerald-600 dark:text-emerald-400">☐</span>
                {action}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {result.attendee_logistics_email ? (
        <section className={sectionClassName}>
          <h2 className={sectionTitleClassName}>Attendee Logistics Email</h2>
          <div className="rounded-xl border border-dashed border-zinc-200 bg-zinc-50 px-4 py-4 dark:border-zinc-700 dark:bg-zinc-950/50">
            <p className="mb-2 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
              Subject: Getting to {eventName || "the event"}
            </p>
            <pre className="whitespace-pre-wrap font-sans text-sm text-zinc-700 dark:text-zinc-300">
              {result.attendee_logistics_email}
            </pre>
          </div>
        </section>
      ) : null}

      {result.box_outputs && result.box_outputs.length > 0 ? (
        <section className={sectionClassName}>
          <h2 className={sectionTitleClassName}>Saved to Box</h2>
          <ul className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {result.box_outputs.map((file) => (
              <li
                key={file.box_file_id}
                className="flex items-center gap-3 py-2.5 text-sm text-zinc-800 dark:text-zinc-200"
              >
                <span aria-hidden>📄</span>
                <span className="flex-1">{file.name}</span>
                {file.url ? (
                  <a
                    href={file.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium text-emerald-600 hover:text-emerald-500 dark:text-emerald-400"
                  >
                    Open in Box →
                  </a>
                ) : null}
              </li>
            ))}
          </ul>
          {result.evidence_sources && result.evidence_sources.length > 0 ? (
            <p className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
              Evidence sources: {result.evidence_sources.join(" · ")}
            </p>
          ) : null}
        </section>
      ) : result.evidence_sources && result.evidence_sources.length > 0 ? (
        <section className={sectionClassName}>
          <h2 className={sectionTitleClassName}>Evidence Sources</h2>
          <ul className="space-y-1 text-sm text-zinc-700 dark:text-zinc-300">
            {result.evidence_sources.map((source) => (
              <li key={source}>· {source}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
