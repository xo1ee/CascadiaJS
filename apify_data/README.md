# apify_data — Google Maps Scraper step

Kone's part of SiteLens. Given a venue's coordinates, call the Apify **Google
Maps Scraper** and store nearby points of interest — parking lots, bus stops, …
— within a ~1-mile-diameter radius. Self-contained: it just takes coordinates in
and writes POI JSON out.

## Files
- `scraper.py` — fetch + store. Standard library only, no `pip install` needed.
- `demo_data_from_scraper.json` — sample scraper output; used as the offline fallback.
- `<venue_key>_scraped.json` — generated output, one file per venue. Safe to delete.

## Setup (one-time)
Credentials live in the repo-root `.env` (already created, gitignored).
Paste your two values on these lines:

```
APIFY_TOKEN=apify_api_xxxxxxxxxxxx
APIFY_ACTOR_ID=            # leave empty to use the default compass/crawler-google-places
```

`scraper.py` loads this `.env` automatically — no other wiring needed.

## Run

Live, for just this module (does **not** flip the project-wide `USE_MOCK_DATA`,
so nothing else in the project is affected):

```bash
python apify_data/scraper.py --lat 47.6340 --lon -122.3401 --key venue_a --live
```

Without `--live` (and with `USE_MOCK_DATA=true`) it returns the demo dataset, so
you can develop offline. On a live error (bad token/actor) it prints a warning
and falls back to demo data instead of crashing.

## Use as a library
```python
from apify_data.scraper import scrape_and_store, scrape_nearby

# fetch + write apify_data/venue_a_scraped.json
places, path = scrape_and_store(47.6340, -122.3401, venue_key="venue_a", force_live=True)

# or just get the list back
places = scrape_nearby(47.6340, -122.3401, force_live=True)
```

## Config
| env var | meaning |
|---|---|
| `APIFY_TOKEN` | Apify API token — required for live scraping |
| `APIFY_ACTOR_ID` | optional; defaults to `nwua9Gu5YrADL7ZDj` (compass/crawler-google-places) |
| `USE_MOCK_DATA` | `"true"` (default) → demo fallback. Project-wide flag; prefer `--live` for this module |

Tunable defaults live at the top of `scraper.py`:
`DEFAULT_SEARCH_TERMS = ["parking lot", "bus stop"]`, `DEFAULT_RADIUS_KM = 0.8`
(0.8 km radius ≈ 1-mile diameter).
