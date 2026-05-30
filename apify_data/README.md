# apify_data — Nearby Places Scraper

Find the parking lots, bus stops (and whatever else you ask for) around a venue,
using the Apify **Google Maps Scraper** — then save the results and, optionally,
push them to Box.

This folder is **self-contained**: it takes an Apify input in, writes POI JSON
out. It has no dependency on the rest of the project and needs no `pip install`
(pure Python standard library).

Starting from an **address** instead of coordinates? POST it to the built-in HTTP
endpoint — it geocodes the address and fills `input.json` for you. See
*From an address (frontend → live endpoint)* below.

```
    input.json            scraper.py          <key>_scraped.json          Box
 (Apify input you   ──►   sends it to    ──►       saved locally    ──►  (optional
   edit by hand)          the Maps API              as JSON              HTTP upload)
```

---

## Quick start

1. **Edit `input.json`** — set the search terms and the location (full field
   guide below).
2. **Add your Apify token** to the repo-root `.env`:
   ```
   APIFY_TOKEN=apify_api_xxxxxxxxxxxx
   ```
3. **Run it:**
   ```bash
   python3 apify_data/scraper.py --live
   ```
   Results land in `apify_data/venue_scraped.json` (use `--key NAME` to change
   the filename).

> Drop `--live` to run against the bundled `demo_data.json` instead — handy for
> developing offline, no token needed.

---

## `input.json` — the one file you edit

`input.json` is the **official Apify Google Maps Scraper input**. The scraper
sends it to the Apify API exactly as written, so anything you can set in the
Apify console you can set here. A trimmed view of the fields you'll actually
touch:

```json
{
  "searchStringsArray": ["parking lot", "bus stop", "coffee", "restaurant"],
  "customGeolocation": {
    "type": "Point",
    "coordinates": ["-122.3390679", "47.6343777"],
    "radiusKm": 1
  },
  "maxCrawledPlacesPerSearch": 50,
  "language": "en"
}
```

| Field | What it controls |
|---|---|
| `searchStringsArray` | What to look for. **One Google Maps search runs per term** — add/remove terms to widen or narrow the net. |
| `customGeolocation` | The search **area** (a circle) — see the breakdown below. |
| `maxCrawledPlacesPerSearch` | Cap on places returned **per search term**. Higher = more complete but slower and costs more Apify compute. |
| `language` | Language for results, as an ISO code (`"en"`, `"zh"`, …). |
| *(all other keys)* | Optional Apify toggles — reviews, contacts, images, social profiles, leads, etc. Leave the defaults unless you need them. |

**`customGeolocation`** — the circle to search inside:

| Field | What it is |
|---|---|
| `type` | `"Point"` for a circular radius search. |
| `coordinates` | `[longitude, latitude]` — **longitude first** (the reverse of how Google Maps shows it). Strings or numbers both work. |
| `radiusKm` | Radius **in kilometres**. `1` = a 1 km radius (~1.24-mile diameter); `0.8` ≈ a 1-mile diameter. |

> Tip: grab a coordinate by right-clicking a spot in Google Maps — but remember
> to put **longitude before latitude** here.

---

## From an address (frontend → live endpoint)

Don't want to hand-edit coordinates? Run the small HTTP endpoint and POST it an
**address** — it geocodes the address, writes the coordinate into `input.json`
for you, and (optionally) runs the scrape. Geocoding is built in (`geocode.py`):
Google if `GOOGLE_MAPS_API_KEY` is set in `.env`, otherwise free OpenStreetMap
Nominatim — so this still has no dependency on the rest of the project.

```bash
# start the endpoint (separate from the main backend)
python3 apify_data/server.py            # listens on http://localhost:8500
```

The frontend then POSTs JSON to it:

```jsonc
POST http://localhost:8500/scrape
{
  "address": "1700 Westlake Ave N, Seattle, WA",   // required
  "radius_km": 1,                                    // optional
  "search_terms": ["parking lot", "bus stop"],       // optional
  "key": "venue_a",                                  // optional output name
  "run": true,                                       // optional: also scrape now
  "live": true,                                      // optional: live Apify vs mock
  "upload_box": false                                // optional: push to Box
}
```

The chain is: `address → geocode → input.json updated → (if run) scrape → save →
(if upload_box) Box`. With `"run": false` (the default) it **only** updates
`input.json`; you then scrape separately with `python3 apify_data/scraper.py --live`.

Just need geocoding on its own?

```bash
python3 apify_data/geocode.py "1700 Westlake Ave N, Seattle, WA"
```

---

## Running it

```bash
# run input.json, live
python3 apify_data/scraper.py --live
```

| Flag | What it does |
|---|---|
| *(none)* | Run `input.json`. Without `--live` you get the demo dataset. |
| `--live` | Hit the real Apify API. |
| `--upload-box` | Upload the saved file to Box after scraping. |
| `--key NAME` | Output filename → `NAME_scraped.json` (default `venue`). |
| `--lat --lon` | Override `customGeolocation`'s coordinate for a one-off run. |
| `--radius-km`, `--terms` | Override `radiusKm` / `searchStringsArray` just for this run. |
| `--input PATH` | Use a different input file. |
| `--token TOKEN` | Use a specific Apify token (implies `--live`). |

**If something goes wrong** (bad token, network hiccup), the scraper prints a
warning and falls back to the demo dataset rather than crashing — so a run always
produces a file.

---

## Sending results to Box

The flow is: **save locally first, then HTTP-POST the file to Box.** You don't
build anything on the Box side — Box already exposes an upload REST API; you just
need a token and a destination folder.

```bash
# scrape live, save locally, then upload to Box in one go
python3 apify_data/scraper.py --live --upload-box

# or upload a file you already have, on its own
python3 apify_data/box_uploader.py apify_data/venue_scraped.json
```

Set these in the repo-root `.env`:

```
BOX_DEVELOPER_TOKEN=...      # from the Box developer console — expires ~60 min
BOX_FOLDER_ID=               # destination folder id; empty = "0" (All Files root)
```

Re-uploading a file with the same name automatically creates a new **version** in
Box rather than failing.

> The developer token is the quickest option but expires after ~60 minutes —
> refresh it before a run. For something long-lived, switch to a Box CCG or JWT
> app (those need an enterprise/user id, not just these two values).

---

## Using it from Python

```python
from apify_data.scraper import load_input, run_scraper, save_results, scrape_nearby

# run the input.json input
places = run_scraper(load_input(), force_live=True)
save_results(places, "venue_a")        # → apify_data/venue_a_scraped.json

# or, from a bare coordinate (builds a minimal input for you)
places = scrape_nearby(47.6343777, -122.3390679, force_live=True)
```

---

## Environment (`.env`)

Credentials and the global mock switch live in the repo-root `.env` (gitignored).
`scraper.py` loads it automatically.

| Variable | Meaning |
|---|---|
| `APIFY_TOKEN` | Apify API token — required for live scraping. |
| `APIFY_ACTOR_ID` | Optional. Defaults to `nwua9Gu5YrADL7ZDj` (`compass/crawler-google-places`). |
| `USE_MOCK_DATA` | `"true"` (default) → demo fallback. This flag is **project-wide**; prefer `--live` to go live for just this module. |
| `BOX_DEVELOPER_TOKEN` | Box developer token — required for `--upload-box` (expires ~60 min). |
| `BOX_FOLDER_ID` | Box destination folder id (`0` = All Files root). |

`input.json` is the source of truth for the scrape input. The `DEFAULT_*`
constants in `scraper.py` are only a fallback for when `input.json` is missing.
