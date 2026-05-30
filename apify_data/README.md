# apify_data — Nearby Places Scraper

Find the parking lots, bus stops (and whatever else you ask for) around a venue,
using the Apify **Google Maps Scraper** — then save the results and, optionally,
push them to Box.

This folder is **self-contained**: it takes coordinates in, writes POI JSON out.
It has no dependency on the rest of the project and needs no `pip install` (pure
Python standard library).

```
   input.json            scraper.py            <key>_scraped.json          Box
  (you edit it)   ──►   Apify Google    ──►        saved locally    ──►  (optional
  venues+settings        Maps API                   as JSON              HTTP upload)
```

---

## Quick start

1. **Edit `input.json`** — set the venues and what to search for (full field
   guide below).
2. **Add your Apify token** to the repo-root `.env`:
   ```
   APIFY_TOKEN=apify_api_xxxxxxxxxxxx
   ```
3. **Run it:**
   ```bash
   python apify_data/scraper.py --live
   ```
   Each venue's results land in `apify_data/<key>_scraped.json`.

> Drop `--live` to run against the bundled `demo_data.json` instead — handy for
> developing offline, no token needed.

---

## `input.json` — the one file you edit

Everything about *what* gets scraped lives here, decoupled from the code:

```json
{
  "search_terms": ["parking lot", "bus stop"],
  "radius_km": 0.8,
  "max_per_search": 50,
  "language": "en",
  "upload_to_box": false,
  "venues": [
    { "key": "venue_a", "lat": 47.6340, "lon": -122.3401 }
  ]
}
```

| Field | Type | What it controls |
|---|---|---|
| `search_terms` | `string[]` | What to look for near each venue. One Google Maps search runs per term — add more (e.g. `"ev charging"`, `"hotel"`) to widen the net. |
| `radius_km` | `number` | Search radius **in kilometres** around each point. `0.8` ≈ a **1-mile diameter** (radius 0.5 mi). Bump it up to cover a wider area. |
| `max_per_search` | `number` | Cap on places returned **per search term**. Higher = more complete but slower and costs more Apify compute. `50` is a sensible default. |
| `language` | `string` | Language for Google Maps results, as an ISO code (`"en"`, `"zh"`, …). |
| `upload_to_box` | `boolean` | `true` → after saving locally, each file is HTTP-uploaded to Box. Same effect as passing `--upload-box`. |
| `venues` | `object[]` | The list of points to scrape — see below. Add as many as you like; each is scraped and saved separately. |

Each entry in **`venues`**:

| Field | What it is |
|---|---|
| `key` | Short id for this venue. The output is saved as `<key>_scraped.json`. |
| `lat` / `lon` | The coordinate to centre the search on. |

> The leading `_comment` key in `input.json` is just a note to yourself — the
> scraper ignores it.

---

## Running it

```bash
# scrape every venue in input.json, live
python apify_data/scraper.py --live
```

| Flag | What it does |
|---|---|
| *(none)* | Scrape every venue in `input.json`. |
| `--live` | Hit the real Apify API. Without it (and with `USE_MOCK_DATA=true`) you get the demo dataset. |
| `--upload-box` | Upload each saved file to Box (same as `upload_to_box: true`). |
| `--lat --lon --key` | One-off: scrape a single coordinate and ignore `input.json`'s venues. |
| `--input PATH` | Use a different input file. |
| `--radius-km`, `--terms` | Override `input.json` just for this run. |
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
python apify_data/scraper.py --live --upload-box

# or upload a file you already have, on its own
python apify_data/box_uploader.py apify_data/venue_a_scraped.json
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
from apify_data.scraper import scrape_and_store, scrape_nearby, load_input

# scrape one coordinate and write apify_data/venue_a_scraped.json
places, path = scrape_and_store(47.6340, -122.3401, venue_key="venue_a", force_live=True)

# just get the list back, no file
places = scrape_nearby(47.6340, -122.3401, force_live=True)

# read the settings from input.json yourself
cfg = load_input()   # {"search_terms": [...], "radius_km": ..., "venues": [...], ...}
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

The `DEFAULT_*` constants at the top of `scraper.py` are only fallbacks for when
`input.json` is missing or a key is absent — edit `input.json`, not the code.
