# Scraper API — for the frontend

The scraper side exposes **one HTTP endpoint**. The frontend's job is simple:
**take the address the user typed and POST it to this endpoint.** The endpoint
geocodes the address, feeds it to the Google Maps scraper, and (optionally) runs
the scrape — the frontend doesn't deal with coordinates or Apify at all.

## Endpoint

```
POST  http://localhost:8500/scrape
Content-Type: application/json
```

> Dev URL is `localhost:8500`. Put the base URL in an env var (e.g.
> `NEXT_PUBLIC_SCRAPER_API`) so it's easy to change for deploy. CORS is already
> enabled, so the browser can call it directly.

## Request body

| Field | Required | Meaning |
|---|---|---|
| `address` | ✅ | The address the user typed, e.g. `"1700 Westlake Ave N, Seattle, WA"`. |
| `radius_km` | optional | Search radius in km (default comes from the scraper's `input.json`). |
| `search_terms` | optional | `string[]` of what to find, e.g. `["parking lot","bus stop"]`. |
| `key` | optional | Output name; results saved as `<key>_scraped.json`. |
| `run` | optional | `true` = also run the scrape now and wait for it. `false` (default) = just save the input, scrape later. |
| `live` | optional | `true` = real Apify data; otherwise demo data. |
| `upload_box` | optional | `true` = also upload the results to Box. |

Minimal call = just `{ "address": "..." }`.

## Response

```json
{
  "ok": true,
  "address": "1700 Westlake Ave N, Seattle, WA",
  "coordinates": [-122.3390679, 47.6343777],
  "input": { "...the updated scraper input..." },
  "scraped": 183,                              // only when run=true
  "output_file": ".../venue_a_scraped.json",   // only when run=true
  "box_file_id": "12345"                        // only when upload_box=true
}
```
On error: `{ "ok": false, "error": "..." }` with a 4xx/5xx status.

## Drop-in frontend call (TypeScript)

```ts
const SCRAPER_API =
  process.env.NEXT_PUBLIC_SCRAPER_API ?? "http://localhost:8500";

export async function sendAddressToScraper(address: string) {
  const res = await fetch(`${SCRAPER_API}/scrape`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ address, run: true, live: true }),
  });
  if (!res.ok) throw new Error(`scraper endpoint failed: ${res.status}`);
  return res.json(); // { ok, coordinates, scraped, output_file, ... }
}
```

## Test it without the frontend

```bash
curl -X POST http://localhost:8500/scrape \
  -H 'Content-Type: application/json' \
  -d '{"address":"Space Needle, Seattle, WA"}'
```

## Two things to plan for

- **`run: true` is slow.** A live scrape takes a few minutes — the request stays
  open the whole time. Show a loading state and use a long timeout. If you want a
  snappy UI, send `run: false` (returns instantly after saving the input) and
  kick off the scrape separately.
- **It's a separate service** from the main backend (port 8500, not 8000). Start
  it with `python3 apify_data/server.py`.
