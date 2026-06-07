"use client";

import { useState } from "react";
import { AnalysisResults } from "@/app/components/analysis/AnalysisResults";
import { AddressSearchField } from "./AddressSearchField";
import { analyzeVenues, ApiError } from "@/lib/api";
import type { AnalyzeVenuesResponse, VenueInput } from "@/lib/types";

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
  { id: "venue-1", name: "thinkspace Seattle", address: "1700 Westlake Ave N #200, Seattle, WA 98109" },
  { id: "venue-2", name: "Impact Hub Seattle", address: "220 2nd Ave S, Seattle, WA 98104" },
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
      <AddressSearchField
        id={`${venue.id}-address`}
        label="Address"
        value={venue.address}
        onChange={(address) => onUpdate(venue.id, "address", address)}
        placeholder={placeholders.address}
      />
    </div>
  );
}

export default function VenueForm() {
  const [eventName, setEventName] = useState("CascadiaJS 2026");
  const [useCase, setUseCase] = useState("100-person AI developer event");
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
  return (
    <div className="min-h-full bg-zinc-50 px-4 py-10 dark:bg-zinc-950 sm:px-6 lg:px-8">
      <div
        className={`mx-auto ${comparisonResult ? "max-w-5xl" : "max-w-3xl"}`}
      >
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

          <section className="px-6 py-6 sm:px-8">
            <h2 className="mb-4 text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              AI Comparison
            </h2>

            {error ? (
              <p
                role="alert"
                className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200"
              >
                {error}
              </p>
            ) : isLoading ? (
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Analyzing venues — geocoding maps, scraping nearby places, and
                running the decision agent…
              </p>
            ) : comparisonResult ? (
              <p className="text-sm text-zinc-600 dark:text-zinc-400">
                Analysis complete. Scroll down for the full planning packet.
              </p>
            ) : (
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                Submit the form to generate an evidence-backed venue comparison.
              </p>
            )}
          </section>

          <div className="border-t border-zinc-100 bg-zinc-50/50 px-6 py-5 dark:border-zinc-800 dark:bg-zinc-950/30 sm:px-8">
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

        {comparisonResult ? (
          <AnalysisResults result={comparisonResult} eventName={eventName} />
        ) : null}
      </div>
    </div>
  );
}
