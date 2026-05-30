"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import type { SearchBoxRetrieveResponse } from "@mapbox/search-js-core";
import { FormField, inputClassName, labelClassName } from "./FormField";
import { getMapboxToken } from "@/lib/mapbox";

const SearchBox = dynamic(
  () => import("@mapbox/search-js-react").then((mod) => mod.SearchBox),
  {
    ssr: false,
    loading: () => (
      <input
        disabled
        placeholder="Loading address search…"
        className={inputClassName}
      />
    ),
  },
);

const searchBoxTheme = {
  variables: {
    fontFamily: "inherit",
    borderRadius: "0.5rem",
    colorPrimary: "#059669",
    colorBackground: "#ffffff",
    colorText: "#18181b",
    border: "1px solid #e4e4e7",
    boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  },
  cssText: `
    .Input {
      width: 100%;
      padding: 0.625rem 0.875rem;
      font-size: 0.875rem;
      line-height: 1.25rem;
    }
    .Input:focus {
      border-color: #10b981;
      outline: none;
      box-shadow: 0 0 0 2px rgb(16 185 129 / 0.2);
    }
    .Results {
      border-radius: 0.5rem;
      margin-top: 0.25rem;
      font-size: 0.875rem;
    }
  `,
};

function formatRetrievedAddress(res: SearchBoxRetrieveResponse): string {
  const feature = res.features?.[0];
  if (!feature) return "";

  const { full_address, name, place_formatted } = feature.properties;
  return (
    full_address ??
    [name, place_formatted].filter(Boolean).join(", ") ??
    place_formatted ??
    name ??
    ""
  );
}

export function AddressSearchField({
  id,
  label,
  value,
  onChange,
  placeholder,
  hint,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  hint?: string;
}) {
  const accessToken = getMapboxToken();

  const searchOptions = useMemo(
    () => ({
      language: "en",
      country: "US",
      proximity: { lng: -122.3321, lat: 47.6062 },
      limit: 5,
    }),
    [],
  );

  if (!accessToken) {
    return (
      <FormField
        id={id}
        label={label}
        name={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        hint={
          hint ??
          "Add NEXT_PUBLIC_MAPBOX_TOKEN to web/.env.local for address autocomplete."
        }
      />
    );
  }

  return (
    <div>
      <label htmlFor={id} className={labelClassName}>
        {label}
      </label>
      <SearchBox
        accessToken={accessToken}
        value={value}
        placeholder={placeholder}
        theme={searchBoxTheme}
        options={searchOptions}
        onChange={onChange}
        onRetrieve={(res) => {
          const address = formatRetrievedAddress(res);
          if (address) onChange(address);
        }}
      />
      {hint ? (
        <p className="mt-1.5 text-xs text-zinc-500 dark:text-zinc-400">{hint}</p>
      ) : (
        <p className="mt-1.5 text-xs text-zinc-500 dark:text-zinc-400">
          Search by venue name or street address.
        </p>
      )}
    </div>
  );
}
