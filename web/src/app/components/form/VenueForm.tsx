"use client";

import { useState } from "react";
import { analyzeVenues, ApiError } from "@/lib/api";
import type { AnalyzeVenuesResponse, VenueAnalysis, VenueInput } from "@/lib/types";

// user input data
type Venue = VenueInput;
// form placeholders
const VENUE_PLACEHOLDERS: Pick<Venue, "name" | "address">[] = [
  {
    name: "thinkspace Seattle",
    address: "1700 Westlake Ave N #200, Seattle, WA 98109",
  },
  {
    name: "Impact Hub Seattle",
    address: "220 2nd Ave S, Seattle, WA 98104",
  },
];

// default compares 2 venues (user can add more)
const DEFAULT_VENUES: Venue[] = [
  { id: "venue-1", name: "", address: "" },
  { id: "venue-2", name: "", address: "" },
];

const inputClassName =
  "w-full rounded-lg border border-zinc-200 bg-white px-3.5 py-2.5 text-sm text-zinc-900 shadow-sm outline-none transition placeholder:text-zinc-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:focus:border-emerald-400 dark:focus:ring-emerald-400/20";

const labelClassName =
  "mb-1.5 block text-sm font-medium text-zinc-700 dark:text-zinc-300";

const venueCardClassName =
  "space-y-5 rounded-xl border border-zinc-100 bg-zinc-50/80 p-5 dark:border-zinc-800 dark:bg-zinc-950/50";

function Field({
  id,
  label,
  name,
  value,
  onChange,
  placeholder,
  hint,
}: {
  id: string;
  label: string;
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder: string;
  hint?: string;
}) {
  return (
    <div>
      <label htmlFor={id} className={labelClassName}>
        {label}
      </label>
      <input
        type="text"
        id={id}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={inputClassName}
      />
      {hint ? (
        <p className="mt-1.5 text-xs text-zinc-500 dark:text-zinc-400">{hint}</p>
      ) : null}
    </div>
  );
}

function VenueInputCard({
  venue,
  index,
  onUpdate,
  onRemove,
  canRemove,
}: {
  venue: Venue;
  index: number;
  onUpdate: (id: string, field: keyof Pick<Venue, "name" | "address">, value: string) => void;
  onRemove: (id: string) => void;
  canRemove: boolean;
}) {
  const placeholders = VENUE_PLACEHOLDERS[index] ?? {
    name: "Venue name",
    address: "Street address, city, state, zip",
  };

  return (
    <div className={venueCardClassName}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Venue {index + 1}
        </p>
        {canRemove ? (
          <button
            type="button"
            onClick={() => onRemove(venue.id)}
            className="text-xs font-medium text-zinc-500 transition hover:text-red-600 dark:text-zinc-400 dark:hover:text-red-400"
          >
            Remove
          </button>
        ) : null}
      </div>
      <Field
        id={`${venue.id}-name`}
        label="Name"
        name="name"
        value={venue.name}
        onChange={(e) => onUpdate(venue.id, "name", e.target.value)}
        placeholder={placeholders.name}
      />
      <Field
        id={`${venue.id}-address`}
        label="Address"
        name="address"
        value={venue.address}
        onChange={(e) => onUpdate(venue.id, "address", e.target.value)}
        placeholder={placeholders.address}
      />
    </div>
  );
}

// ===========================================================================
// Dark results dashboard (matches slides/assets/results_page.png)
// ===========================================================================

function Stars({ score = 0 }: { score?: number }) {
  const full = Math.max(0, Math.min(5, Math.round(score)));
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="text-sm leading-none tracking-tight">
        <span className="text-amber-300">{"★".repeat(full)}</span>
        <span className="text-slate-600">{"★".repeat(5 - full)}</span>
      </span>
      <span className="text-[11px] tabular-nums text-slate-400">{score.toFixed(1)}</span>
    </span>
  );
}

// Score bands on the shared 0–5 scale (matches the per-criterion stars and
// the backend's _rating_from_score: Strong ≥ 4.0, Medium ≥ 2.75, else Weak).
function scoreColor(score = 0): string {
  if (score >= 4.0) return "text-emerald-300";
  if (score >= 2.75) return "text-amber-300";
  return "text-rose-300";
}

const CRITERIA_ORDER = [
  "Accessibility",
  "Nearby Amenities",
  "Event Atmosphere",
  "Logistics Risk",
  "Attendee Communication Needs",
];

function VenueScoreCard({
  label,
  venue,
  matrix,
  which,
  recommended,
}: {
  label: string;
  venue?: VenueAnalysis;
  matrix: AnalyzeVenuesResponse["tradeoff_matrix"];
  which: "a" | "b";
  recommended: boolean;
}) {
  const counts = venue?.poi_summary?.category_counts;
  return (
    <div
      className={`rounded-xl border bg-[#0f1626] p-5 ${
        recommended ? "border-cyan-400/50 shadow-[0_0_24px_-8px_rgba(34,211,238,0.4)]" : "border-cyan-500/15"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-cyan-400/80">
            {label}
            {recommended ? <span className="ml-2 text-amber-300">★ recommended</span> : null}
          </p>
          <p className="mt-1 text-lg font-semibold text-slate-100">
            {venue?.name ?? label}
          </p>
          {venue?.address ? (
            <p className="text-xs text-slate-500">{venue.address}</p>
          ) : null}
        </div>
        <div className="text-right">
          <p className={`text-3xl font-bold tabular-nums ${scoreColor(venue?.overall_score)}`}>
            {typeof venue?.overall_score === "number" ? venue.overall_score.toFixed(1) : "—"}
          </p>
          <p className="text-[10px] uppercase tracking-wider text-slate-500">/ 5</p>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {CRITERIA_ORDER.map((crit) => {
          const row = matrix.find((r) => r.criterion === crit);
          const score = which === "a" ? row?.venue_a_score : row?.venue_b_score;
          return (
            <div key={crit} className="flex items-center justify-between gap-2">
              <span className="text-xs text-slate-400">{crit}</span>
              <Stars score={score ?? 0} />
            </div>
          );
        })}
      </div>

      {counts ? (
        <div className="mt-4 flex flex-wrap gap-1.5 border-t border-white/5 pt-3">
          {Object.entries(counts)
            .filter(([, v]) => v > 0)
            .map(([k, v]) => (
              <span
                key={k}
                className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 text-[11px] text-slate-300"
              >
                <b className="text-slate-100">{v}</b> {k}
              </span>
            ))}
        </div>
      ) : null}
    </div>
  );
}

function ResultsDashboard({
  result,
  onReset,
}: {
  result: AnalyzeVenuesResponse;
  onReset: () => void;
}) {
  const venues = result.venues ?? [];
  const aName = venues[0]?.name ?? "Venue A";
  const bName = venues[1]?.name ?? "Venue B";
  const recIndex = result.recommended_venue === "B" ? 1 : 0;
  const recName = result.recommended_venue_name ?? venues[recIndex]?.name ?? "—";
  const recScore = venues[recIndex]?.overall_score;

  const sectionLabel =
    "mb-3 text-[11px] font-semibold uppercase tracking-wider text-cyan-400/80";
  const card = "rounded-xl border border-cyan-500/15 bg-[#0f1626] p-5";

  const edgeLabel = (edge?: string) =>
    edge === "A" ? aName : edge === "B" ? bName : "Even";

  return (
    <div className="min-h-full bg-[#0a0e1a] px-4 py-8 text-slate-200 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        {/* Top bar */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-baseline gap-2">
            <span className="text-sm font-semibold tracking-wide text-cyan-300">SiteLens</span>
            <span className="text-xs text-slate-500">/ Venue Analysis Results</span>
          </div>
          <button
            type="button"
            onClick={onReset}
            className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-slate-300 transition hover:border-cyan-400/40 hover:text-cyan-300"
          >
            ← New comparison
          </button>
        </div>

        {/* Recommended banner */}
        <div className="mb-5 flex items-center justify-between gap-4 rounded-xl border border-cyan-400/30 bg-gradient-to-r from-[#0e1b2e] to-[#0f1626] p-5">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-cyan-400/80">
              🏆 Recommended Venue
            </p>
            <p className="mt-1 text-2xl font-bold text-slate-50">{recName}</p>
            <p className="mt-1 max-w-2xl text-sm text-slate-400">
              {result.overall_recommendation}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <p className={`text-4xl font-bold tabular-nums ${scoreColor(recScore)}`}>
              {typeof recScore === "number" ? recScore.toFixed(1) : "—"}
            </p>
            <p className="text-[10px] uppercase tracking-wider text-slate-500">Overall / 5</p>
          </div>
        </div>

        {/* Venue score cards */}
        <div className="mb-5 grid gap-4 sm:grid-cols-2">
          <VenueScoreCard
            label="Venue A"
            venue={venues[0]}
            matrix={result.tradeoff_matrix}
            which="a"
            recommended={recIndex === 0}
          />
          <VenueScoreCard
            label="Venue B"
            venue={venues[1]}
            matrix={result.tradeoff_matrix}
            which="b"
            recommended={recIndex === 1}
          />
        </div>

        <div className="grid gap-5 lg:grid-cols-3">
          {/* Trade-off table (spans 2 cols) */}
          <div className={`${card} lg:col-span-2`}>
            <h3 className={sectionLabel}>Trade-off Match</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] uppercase text-slate-500">
                    <th className="py-2 pr-3">Criterion</th>
                    <th className="px-2 py-2">{aName}</th>
                    <th className="px-2 py-2">{bName}</th>
                    <th className="py-2 pl-2">Edge</th>
                  </tr>
                </thead>
                <tbody>
                  {result.tradeoff_matrix?.map((row, i) => (
                    <tr key={i} className="border-t border-white/5 align-top">
                      <td className="py-2.5 pr-3 font-medium text-slate-200">{row.criterion}</td>
                      <td className="px-2 py-2.5">
                        <Stars score={row.venue_a_score ?? 0} />
                      </td>
                      <td className="px-2 py-2.5">
                        <Stars score={row.venue_b_score ?? 0} />
                      </td>
                      <td className="py-2.5 pl-2">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                            row.edge === "Tie"
                              ? "bg-slate-700/50 text-slate-300"
                              : "bg-cyan-500/15 text-cyan-300"
                          }`}
                        >
                          {edgeLabel(row.edge)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {result.key_risks?.length ? (
              <div className="mt-5 border-t border-white/5 pt-4">
                <h3 className={sectionLabel}>Key Risks &amp; Mitigations</h3>
                <ul className="space-y-2.5">
                  {result.key_risks.map((r, i) => (
                    <li key={i} className="rounded-lg border-l-2 border-amber-400/60 bg-amber-400/5 px-3 py-2">
                      <p className="text-sm font-medium text-slate-200">
                        Venue {r.venue} — {r.risk}
                      </p>
                      {r.mitigation ? (
                        <p className="mt-0.5 text-xs text-slate-400">
                          <span className="font-semibold text-cyan-300">Mitigation:</span> {r.mitigation}
                        </p>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>

          {/* Right column: organizer actions + email */}
          <div className="space-y-5">
            {result.organizer_actions?.length ? (
              <div className={card}>
                <h3 className={sectionLabel}>Organizer Actions</h3>
                <ul className="space-y-2">
                  {result.organizer_actions.map((a, i) => (
                    <li key={i} className="flex gap-2 text-sm text-slate-300">
                      <span className="text-cyan-400">☐</span>
                      <span>{a}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {result.attendee_logistics_email ? (
              <div className={card}>
                <h3 className={sectionLabel}>Attendee Logistics Preview</h3>
                <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg border border-white/5 bg-black/20 p-3 font-sans text-xs text-slate-300">
                  {result.attendee_logistics_email}
                </pre>
              </div>
            ) : null}
          </div>
        </div>

        {/* Box outputs */}
        {result.box_outputs?.length ? (
          <div className={`${card} mt-5`}>
            <h3 className={sectionLabel}>Saved to Box</h3>
            <div className="flex flex-wrap gap-2">
              {result.box_outputs.map((o, i) => (
                <a
                  key={i}
                  href={o.url || "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300 transition hover:border-cyan-400/40 hover:text-cyan-300"
                >
                  📄 {o.name}
                </a>
              ))}
            </div>
            {result.evidence_sources?.length ? (
              <p className="mt-3 text-[11px] text-slate-500">
                Evidence: {result.evidence_sources.join(" · ")}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function VenueForm() {
  const [eventName, setEventName] = useState("");
  const [useCase, setUseCase] = useState("");
  const [venues, setVenues] = useState<Venue[]>(DEFAULT_VENUES);
  const [comparisonResult, setComparisonResult] =
    useState<AnalyzeVenuesResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const useScrollLayout = venues.length > 2;
  const allVenuesHaveAddress = venues.every((v) => v.address.trim().length > 0);
  const updateVenue = (
    id: string,
    field: keyof Pick<Venue, "name" | "address">,
    value: string,
  ) => {
    setVenues((prev) =>
      prev.map((venue) => (venue.id === id ? { ...venue, [field]: value } : venue)),
    );
  };

  const addVenue = () => {
    setComparisonResult(null);
    setVenues((prev) => [
      ...prev,
      { id: crypto.randomUUID(), name: "", address: "" },
    ]);
  };

  const removeVenue = (id: string) => {
    setComparisonResult(null);
    setVenues((prev) => prev.filter((venue) => venue.id !== id));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!allVenuesHaveAddress) {
      setError("Enter an address for each venue before generating.");
      return;
    }

    setIsLoading(true);
    setError(null);
    setComparisonResult(null);

    try {
      const result = await analyzeVenues({
        event_name: eventName,
        use_case: useCase,
        venues,
      });
      setComparisonResult(result);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Something went wrong. Is the backend running on port 8000?";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // After a successful comparison, show the dark results dashboard.
  if (comparisonResult && !isLoading) {
    return (
      <ResultsDashboard
        result={comparisonResult}
        onReset={() => setComparisonResult(null)}
      />
    );
  }

  return (
    <div className="min-h-full bg-zinc-50 px-4 py-10 dark:bg-zinc-950 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <header className="mb-8 text-center sm:text-left">
          <p className="mb-2 text-sm font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
            SiteLens
          </p>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Compare event venues
          </h1>
          <p className="mt-2 max-w-xl text-base text-zinc-600 dark:text-zinc-400">
            Turn any event venue into an evidence-backed planning packet using
            map signals, nearby places, and your Box checklist.
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
        >
          <section className="border-b border-zinc-100 px-6 py-6 dark:border-zinc-800 sm:px-8">
            <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Event context
            </h2>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field
                id="event-name"
                label="Event name"
                name="eventName"
                value={eventName}
                onChange={(e) => setEventName(e.target.value)}
                placeholder="Seattle AI Developer Meetup"
              />
              <Field
                id="use-case"
                label="Use case"
                name="useCase"
                value={useCase}
                onChange={(e) => setUseCase(e.target.value)}
                placeholder="100-person AI developer event"
              />
            </div>
          </section>

          <section className="border-b border-zinc-100 px-6 py-6 dark:border-zinc-800 sm:px-8">
            <div className="mb-4 flex items-center justify-between gap-4">
              <h2 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
                Venue candidates
              </h2>
              <button
                type="button"
                onClick={addVenue}
                className="text-xs font-semibold text-emerald-600 transition hover:text-emerald-500 dark:text-emerald-400 dark:hover:text-emerald-300"
              >
                + Add venue
              </button>
            </div>

            {useScrollLayout ? (
              <div className="max-h-[480px] space-y-4 overflow-y-auto pr-1">
                {venues.map((venue, index) => (
                  <VenueInputCard
                    key={venue.id}
                    venue={venue}
                    index={index}
                    onUpdate={updateVenue}
                    onRemove={removeVenue}
                    canRemove={venues.length > 2}
                  />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                {venues.map((venue, index) => (
                  <VenueInputCard
                    key={venue.id}
                    venue={venue}
                    index={index}
                    onUpdate={updateVenue}
                    onRemove={removeVenue}
                    canRemove={false}
                  />
                ))}
              </div>
            )}
          </section>

          <div className="px-6 py-6 sm:px-8">
            {error ? (
              <p
                role="alert"
                className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200"
              >
                {error}
              </p>
            ) : null}

            {isLoading ? (
              <p className="mb-4 text-sm text-zinc-500 dark:text-zinc-400">
                Analyzing venues — geocoding maps, scoring evidence, building your packet…
              </p>
            ) : null}

            <button
              type="submit"
              disabled={isLoading || !allVenuesHaveAddress}
              className="w-full rounded-lg bg-emerald-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 dark:focus:ring-offset-zinc-900 sm:w-auto sm:min-w-[220px]"
            >
              {isLoading ? "Generating…" : "Generate Venue Packet"}
            </button>
            {!allVenuesHaveAddress && !isLoading ? (
              <p className="mt-2 text-xs text-zinc-500 dark:text-zinc-400">
                Fill in every venue address to enable generation.
              </p>
            ) : null}
          </div>
        </form>
      </div>
    </div>
  );
}
