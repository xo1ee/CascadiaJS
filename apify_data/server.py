"""
Standalone HTTP endpoint — the bridge from the frontend to the scraper.

Flow: the frontend POSTs an address → this endpoint geocodes it → writes the
location into input.json → (optionally) runs the scraper. Standard library only
(http.server), lives entirely in apify_data, no dependency on the rest of the
project.

Run it (separate from the main backend):
    python apify_data/server.py                 # http://localhost:8500
    python apify_data/server.py --port 8600

Then the frontend POSTs JSON to it:
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

Response:
    {
      "ok": true,
      "address": "...",
      "coordinates": [lon, lat],
      "input": { ...updated input.json... },
      "scraped": 183,                       // only if run=true
      "output_file": ".../venue_a_scraped.json",
      "box_file_id": "..."                  // only if upload_box=true
    }

With "run": false (the default) it just writes input.json; run the scraper
afterwards with:  python apify_data/scraper.py --live
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import scraper
from geocode import geocode


class Handler(BaseHTTPRequestHandler):
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # CORS preflight
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            return self._send(400, {"ok": False, "error": f"bad JSON body: {e}"})

        address = (req.get("address") or "").strip()
        if not address:
            return self._send(400, {"ok": False, "error": "missing 'address'"})

        # 1) address -> coordinates
        try:
            lat, lon = geocode(address)
        except Exception as e:
            return self._send(502, {"ok": False, "error": f"geocoding failed: {e}"})

        # 2) write the location into input.json
        cfg = scraper.update_input(
            lat,
            lon,
            radius_km=req.get("radius_km"),
            search_terms=req.get("search_terms"),
        )

        resp = {
            "ok": True,
            "address": address,
            "coordinates": [lon, lat],  # [lng, lat], as stored in customGeolocation
            "input": cfg,
        }

        # 3) optionally run the scraper right away
        if req.get("run"):
            places = scraper.run_scraper(cfg, force_live=bool(req.get("live")))
            key = req.get("key", "venue")
            path = scraper.save_results(places, key)
            resp["scraped"] = len(places)
            resp["output_file"] = str(path)
            if req.get("upload_box"):
                from box_uploader import upload_file
                resp["box_file_id"] = upload_file(path)

        self._send(200, resp)

    def log_message(self, fmt, *args):  # keep the console quiet
        return


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="HTTP endpoint: address → input.json (+ optional scrape).")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8500)
    args = p.parse_args()

    print(f"apify_data endpoint on http://{args.host}:{args.port}  — POST JSON with an 'address'")
    HTTPServer((args.host, args.port), Handler).serve_forever()
