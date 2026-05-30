# SiteLens Design Doc

## 1. Project Overview

**Project name:** SiteLens  
**Tagline:** Turn any event venue into an evidence-backed planning packet.  
**Hackathon theme fit:** AI agents + Box + Apify/AWS + developer/event workflow  
**MVP use case:** Compare two candidate venues for a 100-person developer event or hackathon.

SiteLens is a site intelligence agent for DevRel and event teams. It compares two candidate event venues by combining:

1. **Map / satellite visual signals**  
   The system uses static map or satellite snapshots to extract visible site signals such as nearby water, dense built environment, road access, green space, and visible parking constraints.

2. **Live nearby-place data from Apify**  
   The system uses Apify to collect nearby restaurants, coffee shops, parking, hotels, bars, convenience stores, and other places relevant to event logistics.

3. **Event evaluation checklist from Box**  
   The system reads an event venue checklist from Box. This checklist acts as the user's internal planning standard.

4. **AI agent reasoning**  
   The agent compares two venues across event-specific criteria and generates a venue trade-off report, organizer action checklist, attendee logistics email, and evidence packet.

5. **Box output package**  
   The generated report, action checklist, attendee email, POI summary, and map snapshots are saved back to Box as a shareable planning packet.

SiteLens should not be described as a generic site-selection platform. For the hackathon MVP, it is specifically a **DevRel event venue intelligence agent**.

---

## 2. Problem Statement

DevRel, event marketing, community, and startup teams frequently organize in-person events such as meetups, hackathons, workshops, product launches, recruiting events, and customer sessions.

Venue selection is not only about price or capacity. Event organizers also need to understand:

- How easy it is for attendees to arrive
- Whether food, coffee, hotels, and after-party options are nearby
- Whether parking or rideshare logistics may be a problem
- Whether the surrounding area fits the event atmosphere
- What should be communicated to attendees before the event
- What organizer actions are needed to reduce logistics risk

Today this work is manual. Organizers check Google Maps, venue pages, nearby restaurants, parking options, reviews, satellite views, and internal event checklists, then rewrite the findings into planning docs.

SiteLens automates this workflow.

---

## 3. Target Users

### Primary MVP user

**DevRel / Event Marketing team**

Example user story:

> As a DevRel event organizer planning a 100-person AI developer event, I want to compare two venue candidates using map evidence, nearby-place data, and my team's event checklist, so that I can make a better venue decision and generate attendee instructions faster.

### Secondary future users

- Startup teams planning launch events
- University clubs planning hackathons
- Recruiting teams planning candidate events
- Community teams planning meetups
- Field marketing teams planning customer workshops
- Real estate or operations teams doing lightweight site checks

---

## 4. One-Sentence Pitch

**SiteLens compares event venues using map/satellite signals, live nearby-place data from Apify, and event requirements stored in Box, then generates an evidence-backed venue planning packet saved back to Box.**

---

## 5. Demo Scenario

### Scenario

A DevRel team is planning a 100-person AI developer event in Seattle. They have two possible venues. Both look reasonable, but they have different trade-offs.

The team cares about:

- Easy attendee arrival
- Food and coffee nearby
- Parking / rideshare risk
- After-party options
- Public transit access
- Good event atmosphere
- Clear attendee communication

SiteLens compares both venues and generates a planning packet.

### Suggested demo input

```txt
Use case:
100-person AI developer event

Venue A:
1700 Westlake Ave N #200, Seattle, WA 98109

Venue B:
[Choose another real Seattle event-space address]

Event goals:
- easy arrival
- nearby food and coffee
- after-party networking
- low logistics risk
- clear attendee communication
```

### Demo output

SiteLens creates a Box folder:

```txt
/SiteLens/devrel-venue-review/
  venue_comparison_report.md
  venue_a_site_packet.md
  venue_b_site_packet.md
  nearby_places_summary.csv
  organizer_action_checklist.md
  attendee_logistics_email.md
  venue_a_map.png
  venue_a_satellite.png
  venue_b_map.png
  venue_b_satellite.png
```

---

## 6. MVP Scope

### In scope

The MVP supports:

1. Comparing exactly **two venues**
2. One use case: **developer event / hackathon venue evaluation**
3. Reading one checklist file from Box
4. Getting or loading map/satellite images for both venues
5. Getting or loading Apify nearby-place data for both venues
6. Running AI reasoning over:
   - venue addresses
   - map/satellite visual observations
   - POI summaries
   - Box checklist
7. Generating:
   - venue comparison report
   - site packet for each venue
   - organizer action checklist
   - attendee logistics email
   - nearby places CSV
8. Uploading the output package to Box

### Out of scope

Do not implement these in MVP:

- General-purpose site selection
- Retail revenue prediction
- Real foot traffic prediction
- True remote sensing classification
- Sentinel/Landsat downloading
- NDVI/NDBI/NDWI calculation
- Multi-temporal change detection
- Dynamic interactive GIS dashboard
- User authentication system
- Multi-user collaboration
- Database persistence
- More than two venues
- Multiple use-case templates

### Important language

Use this wording:

> SiteLens uses map and satellite visual signals as one evidence layer.

Do not claim:

> SiteLens performs professional remote sensing classification.

---

## 7. Success Criteria

The demo is successful if:

1. The user enters two venue addresses and clicks **Generate Comparison**.
2. The app shows a clear venue trade-off summary.
3. The app shows visible evidence:
   - map/satellite observations
   - nearby POI counts
   - event checklist criteria
4. The app generates an attendee logistics email.
5. The app generates an organizer action checklist.
6. The app saves the final packet to Box.
7. The pitch clearly explains:
   - Box as the planning workspace
   - Apify as the live nearby-place data source
   - AI agent as the multi-step reasoning and report-generation workflow

---

## 8. System Architecture

```txt
Frontend: React + TypeScript
  |
  | POST /api/analyze-venues
  v
Backend: FastAPI or Node/Express
  |
  |-- Box Tool
  |     - Read event_venue_checklist.md
  |     - Create output folder
  |     - Upload markdown/csv/png files
  |
  |-- Geo Tool
  |     - Address -> lat/lon
  |     - MVP can use hardcoded lat/lon fallback
  |
  |-- Map Snapshot Tool
  |     - Mapbox Static Images API
  |     - Fallback: local PNG snapshots
  |
  |-- Apify Places Tool
  |     - Query nearby places
  |     - Fallback: local JSON files
  |
  |-- Vision Evidence Tool
  |     - Analyze map/satellite images with multimodal model
  |     - Output structured visible site signals
  |
  |-- Reasoning / Report Agent
        - Compare venues
        - Generate reports and action items
        - Produce structured markdown outputs
```

---

## 9. Recommended Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS or simple CSS
- Basic form + results page

### Backend

Choose one:

**Option A: FastAPI**
- Good if the team is comfortable with Python
- Easier CSV and file handling
- Easy to call OpenAI/Claude/Gemini SDKs

**Option B: Node/Express**
- Good if team wants TypeScript end-to-end
- Good for Box SDK and Apify client

Recommended for this team: **FastAPI backend + React frontend**

### APIs / services

- **Box API / SDK**
  - Read checklist file
  - Create output folder
  - Upload files

- **Apify**
  - Google Maps / places scraping actor
  - Fallback to local JSON

- **Mapbox Static Images API**
  - Generate static map/satellite snapshots
  - Fallback to local PNGs

- **LLM / Vision**
  - GPT-4o / GPT-4.1 vision
  - Gemini vision
  - Claude vision
  - Any one is acceptable for MVP

### Optional AWS usage

The hackathon requires Box and either AWS or Apify. Since SiteLens uses Apify, AWS is optional.

If the team wants an AWS story, use one small AWS component:

- Deploy backend to AWS Lambda
- Or store generated artifacts temporarily in S3
- Or use Amazon Bedrock for LLM reasoning

Do not add AWS unless core MVP is stable.

---

## 10. Data Flow

```txt
1. User enters two venue addresses and event use case.
2. Backend reads event_venue_checklist.md from Box.
3. Backend geocodes both addresses.
4. Backend gets map/satellite snapshots for both venues.
5. Backend sends snapshots to a vision model to extract visible site signals.
6. Backend calls Apify for nearby POI data.
7. Backend aggregates POI results by category.
8. Report Agent compares venues against checklist and event goals.
9. Backend generates markdown/csv/png outputs.
10. Backend creates a SiteLens folder in Box.
11. Backend uploads all generated files to Box.
12. Frontend shows recommendation, trade-off matrix, and Box upload result.
```

---

## 11. Agent Workflow

SiteLens should be described as an agent because it performs a multi-step workflow using tools.

### Agent steps

#### 1. Planner Agent

Input:
- Event use case
- Event goals
- Box checklist

Output:
- Evaluation dimensions

For MVP, use fixed dimensions:

```txt
1. Accessibility
2. Nearby Amenities
3. Event Atmosphere
4. Logistics Risk
5. Attendee Communication Needs
```

#### 2. Geo Tool

Input:
- Venue address

Output:
- latitude
- longitude
- normalized address

Fallback:
- hardcoded demo coordinates

#### 3. Map Evidence Tool

Input:
- latitude
- longitude

Output:
- map snapshot image
- satellite snapshot image

Fallback:
- local PNG images

#### 4. Vision Evidence Agent

Input:
- map/satellite snapshot

Output JSON:

```json
{
  "water_nearby": true,
  "green_space_level": "low | medium | high | unknown",
  "building_density": "low | medium | high | unknown",
  "road_access": "weak | moderate | strong | unknown",
  "visible_parking": "limited | moderate | strong | unknown",
  "land_use_context": "commercial / office / residential / industrial / mixed / unknown",
  "observations": [
    "The site appears close to a large water body.",
    "The surrounding area appears highly built-up."
  ],
  "risks": [
    "Parking may be limited.",
    "Traffic may be heavier around major roads."
  ],
  "confidence": "low | medium | high"
}
```

#### 5. Apify Places Tool

Input:
- venue address
- categories

Categories:

```txt
restaurants
coffee
parking
hotels
bars
convenience stores
public transit
```

Output:

```json
{
  "restaurants": [...],
  "coffee": [...],
  "parking": [...],
  "hotels": [...],
  "bars": [...],
  "convenience": [...],
  "transit": [...]
}
```

#### 6. POI Aggregator

Input:
- raw places

Output:

```json
{
  "restaurants_count": 18,
  "coffee_count": 7,
  "parking_count": 2,
  "hotels_count": 5,
  "bars_count": 8,
  "average_rating": 4.3,
  "top_places": [
    {
      "name": "...",
      "category": "restaurant",
      "rating": 4.6,
      "review_count": 328,
      "address": "..."
    }
  ]
}
```

#### 7. Decision Agent

Input:
- checklist
- venue A visual signals
- venue B visual signals
- venue A POI summary
- venue B POI summary

Output:

```json
{
  "overall_recommendation": "...",
  "venue_a_summary": "...",
  "venue_b_summary": "...",
  "tradeoff_matrix": [
    {
      "criterion": "Accessibility",
      "venue_a": "Strong",
      "venue_b": "Medium",
      "reason": "..."
    }
  ],
  "organizer_actions": [
    "Add parking guidance to attendee email."
  ],
  "attendee_logistics_email": "..."
}
```

#### 8. Report Agent

Generates files:

- `venue_comparison_report.md`
- `venue_a_site_packet.md`
- `venue_b_site_packet.md`
- `organizer_action_checklist.md`
- `attendee_logistics_email.md`
- `nearby_places_summary.csv`

#### 9. Box Output Tool

Creates Box folder and uploads generated files.

---

## 12. Frontend Design

### Page 1: Input Form

Fields:

```txt
Event Name
Use Case
Venue A Name
Venue A Address
Venue B Name
Venue B Address
Box Checklist File ID or Box Folder ID
```

Button:

```txt
Generate Venue Packet
```

### Page 2: Results

Cards:

1. **Overall Recommendation**
2. **Venue A Snapshot**
3. **Venue B Snapshot**
4. **Trade-off Matrix**
5. **Organizer Action Items**
6. **Attendee Logistics Email**
7. **Box Output Files**

### Trade-off Matrix UI

Columns:

```txt
Criterion | Venue A | Venue B | Evidence / Reason
```

Rows:

```txt
Accessibility
Nearby Amenities
Event Atmosphere
Logistics Risk
Attendee Communication Needs
```

### Visual layout

Suggested layout:

```txt
---------------------------------------------------
SiteLens
Compare event venues with map, place, and Box evidence
---------------------------------------------------

[Venue A card]       [Venue B card]
Map image            Map image
POI counts           POI counts
Visual signals       Visual signals

[Overall Recommendation]

[Trade-off Matrix]

[Organizer Actions]

[Attendee Email Draft]

[Saved to Box]
```

---

## 13. Backend API Design

### POST `/api/analyze-venues`

Request:

```json
{
  "event_name": "Seattle AI Developer Meetup",
  "use_case": "100-person AI developer event",
  "event_goals": [
    "easy arrival",
    "food and coffee nearby",
    "after-party networking",
    "low logistics risk",
    "clear attendee communication"
  ],
  "venue_a": {
    "name": "Venue A",
    "address": "1700 Westlake Ave N #200, Seattle, WA 98109"
  },
  "venue_b": {
    "name": "Venue B",
    "address": "..."
  },
  "box_checklist_file_id": "optional-file-id",
  "box_output_parent_folder_id": "required-folder-id"
}
```

Response:

```json
{
  "overall_recommendation": "...",
  "venue_a": {
    "name": "Venue A",
    "address": "...",
    "visual_signals": {},
    "poi_summary": {},
    "site_packet_markdown": "..."
  },
  "venue_b": {
    "name": "Venue B",
    "address": "...",
    "visual_signals": {},
    "poi_summary": {},
    "site_packet_markdown": "..."
  },
  "tradeoff_matrix": [],
  "organizer_actions": [],
  "attendee_logistics_email": "...",
  "box_outputs": [
    {
      "name": "venue_comparison_report.md",
      "box_file_id": "...",
      "url": "..."
    }
  ]
}
```

### GET `/api/health`

Response:

```json
{
  "status": "ok"
}
```

---

## 14. Environment Variables

Create `.env.example`:

```bash
# LLM
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Box
BOX_CLIENT_ID=
BOX_CLIENT_SECRET=
BOX_DEVELOPER_TOKEN=
BOX_OUTPUT_PARENT_FOLDER_ID=
BOX_CHECKLIST_FILE_ID=

# Apify
APIFY_TOKEN=
APIFY_ACTOR_ID=

# Mapbox
MAPBOX_TOKEN=

# Runtime
USE_MOCK_DATA=true
```

For hackathon stability, implement `USE_MOCK_DATA=true` mode.

---

## 15. Fallback Strategy

A stable demo matters more than live API purity.

### Required fallbacks

#### 1. Geocoding fallback

Create:

```txt
backend/data/demo_venues.json
```

Example:

```json
{
  "venue_a": {
    "name": "thinkspace Seattle",
    "address": "1700 Westlake Ave N #200, Seattle, WA 98109",
    "lat": 47.634,
    "lon": -122.340
  },
  "venue_b": {
    "name": "Demo Venue B",
    "address": "...",
    "lat": 47.6,
    "lon": -122.3
  }
}
```

#### 2. Map image fallback

Store:

```txt
backend/static/demo/venue_a_map.png
backend/static/demo/venue_a_satellite.png
backend/static/demo/venue_b_map.png
backend/static/demo/venue_b_satellite.png
```

#### 3. Apify fallback

Store:

```txt
backend/data/venue_a_places.json
backend/data/venue_b_places.json
```

#### 4. Box fallback

If Box upload fails, save outputs locally:

```txt
outputs/devrel-venue-review/
```

Still show the generated files in the frontend.

However, for final demo, Box upload should work because Box is a required sponsor integration.

---

## 16. Box Integration Details

### Required Box actions

1. Read checklist file
2. Create output folder
3. Upload generated files

### Box folder structure

```txt
SiteLens/
  devrel-venue-review/
    venue_comparison_report.md
    venue_a_site_packet.md
    venue_b_site_packet.md
    nearby_places_summary.csv
    organizer_action_checklist.md
    attendee_logistics_email.md
    venue_a_map.png
    venue_a_satellite.png
    venue_b_map.png
    venue_b_satellite.png
```

### Checklist file

Create this file in Box before demo:

`event_venue_checklist.md`

```md
# Event Venue Checklist

For a 100-person developer event, evaluate:

## Accessibility
- Is the venue easy to reach by car, rideshare, or public transit?
- Are arrival instructions likely to be simple?
- Are there major traffic risks?

## Nearby Amenities
- Are there restaurants nearby?
- Are there coffee shops nearby?
- Are there hotels nearby for out-of-town attendees?
- Are there convenience stores nearby?

## Event Atmosphere
- Does the surrounding area fit a developer meetup or hackathon?
- Is the area professional, social, or isolated?
- Are there nearby places for informal networking?

## Logistics Risk
- Is parking likely to be limited?
- Are food options likely to be crowded?
- Is the area hard to navigate?
- Are there environmental or access constraints?

## Attendee Communication
- What should attendees be told before arriving?
- Should the organizer recommend rideshare or public transit?
- Should the organizer include parking instructions?
- Should the organizer include food or after-party details?
```

---

## 17. Apify Integration Details

### Actor

Use an Apify Google Maps / Places scraper actor.

The exact actor may vary depending on the available Apify marketplace actor and account configuration.

For MVP, create a wrapper function:

```python
def fetch_nearby_places(address: str, categories: list[str]) -> dict:
    if USE_MOCK_DATA:
        return load_mock_places(address)
    else:
        return call_apify_actor(address, categories)
```

### Query strategy

For each venue, query:

```txt
restaurants near {address}
coffee near {address}
parking near {address}
hotels near {address}
bars near {address}
convenience stores near {address}
public transit near {address}
```

### Fields to normalize

Normalize all place results to:

```json
{
  "name": "...",
  "category": "restaurant",
  "rating": 4.5,
  "review_count": 120,
  "address": "...",
  "url": "...",
  "source": "Apify Google Maps"
}
```

### POI summary

Compute:

```json
{
  "category_counts": {
    "restaurants": 12,
    "coffee": 5,
    "parking": 2,
    "hotels": 3,
    "bars": 8,
    "convenience": 2,
    "transit": 4
  },
  "top_places": [],
  "average_rating": 4.3
}
```

---

## 18. Mapbox Integration Details

### Static map

Use Mapbox Static Images API to generate:

1. Map style image
2. Satellite style image

Function:

```python
def get_static_map_image(lat: float, lon: float, style: str, output_path: str) -> str:
    if USE_MOCK_DATA:
        return load_local_image(style)
    else:
        # Call Mapbox Static Images API
        return downloaded_image_path
```

### Recommended image settings

```txt
width: 800
height: 600
zoom: 15
marker: venue location
```

For satellite image:

```txt
style: satellite-streets-v12 or satellite-v9
```

For map image:

```txt
style: streets-v12
```

---

## 19. Vision Evidence Prompt

Use this prompt for map/satellite image analysis.

```txt
You are a site intelligence analyst helping evaluate event venues.

Analyze the provided map or satellite image as visual evidence only. Do not overclaim. Extract visible site signals relevant to a 100-person developer event.

Return strict JSON with these fields:

{
  "water_nearby": true/false/null,
  "green_space_level": "low" | "medium" | "high" | "unknown",
  "building_density": "low" | "medium" | "high" | "unknown",
  "road_access": "weak" | "moderate" | "strong" | "unknown",
  "visible_parking": "limited" | "moderate" | "strong" | "unknown",
  "land_use_context": "commercial_office" | "residential" | "industrial" | "mixed" | "unknown",
  "observations": [
    "Short evidence-based observation."
  ],
  "risks": [
    "Short risk inferred from visible evidence."
  ],
  "confidence": "low" | "medium" | "high"
}

Rules:
- Only mention things that are visible or reasonably inferable from the image.
- Do not claim exact traffic, crime, demographic, or foot traffic.
- Do not call this NDVI or professional remote sensing.
- If uncertain, use "unknown" or low confidence.
```

---

## 20. Decision Agent Prompt

Use this prompt after collecting checklist, visual signals, and POI summaries.

```txt
You are SiteLens, an AI site intelligence agent for DevRel and event teams.

Your task is to compare two candidate venues for a 100-person developer event.

Inputs:
1. Event use case and goals
2. Event venue checklist from Box
3. Venue A visual signals from map/satellite evidence
4. Venue B visual signals from map/satellite evidence
5. Venue A nearby-place summary from Apify
6. Venue B nearby-place summary from Apify

Output a structured comparison.

Important:
- Do not make unsupported claims.
- Prefer evidence-backed reasoning.
- Focus on practical event planning trade-offs.
- Do not simply say one venue is good and one is bad.
- Explain what each venue is better for.
- Generate organizer actions and attendee communication.

Return JSON with this schema:

{
  "overall_recommendation": "Short recommendation with nuance.",
  "venue_a_positioning": "What Venue A is best for.",
  "venue_b_positioning": "What Venue B is best for.",
  "tradeoff_matrix": [
    {
      "criterion": "Accessibility",
      "venue_a_rating": "Strong | Medium | Weak",
      "venue_b_rating": "Strong | Medium | Weak",
      "evidence": "Evidence-based explanation."
    }
  ],
  "key_risks": [
    {
      "venue": "A | B | Both",
      "risk": "Short risk.",
      "evidence": "Why this risk was identified.",
      "mitigation": "Action to reduce risk."
    }
  ],
  "organizer_actions": [
    "Concrete action item."
  ],
  "attendee_logistics_email": "A ready-to-send attendee logistics email.",
  "evidence_sources": [
    "Box event checklist",
    "Apify nearby places",
    "Map/satellite visual evidence"
  ]
}
```

---

## 21. Markdown Report Templates

### venue_comparison_report.md

```md
# SiteLens Venue Comparison Report

## Event
{event_name}

## Use Case
{use_case}

## Overall Recommendation
{overall_recommendation}

## Venue Positioning
### Venue A: {venue_a_name}
{venue_a_positioning}

### Venue B: {venue_b_name}
{venue_b_positioning}

## Trade-off Matrix

| Criterion | Venue A | Venue B | Evidence |
|---|---|---|---|
| Accessibility | Strong | Medium | ... |
| Nearby Amenities | Strong | Strong | ... |
| Event Atmosphere | Medium | Strong | ... |
| Logistics Risk | Medium | Medium | ... |
| Attendee Communication Needs | High | Medium | ... |

## Key Risks and Mitigations

{key_risks}

## Organizer Action Items

{organizer_actions}

## Evidence Sources

- Box checklist: event_venue_checklist.md
- Apify nearby-place data
- Map/satellite visual evidence
```

### venue_a_site_packet.md / venue_b_site_packet.md

```md
# Site Packet: {venue_name}

## Address
{address}

## Map / Satellite Observations
{visual_observations}

## Nearby Place Summary
{poi_summary}

## Strengths
{strengths}

## Risks
{risks}

## Recommended Organizer Actions
{actions}
```

### organizer_action_checklist.md

```md
# Organizer Action Checklist

- [ ] Add parking/rideshare guidance to attendee page.
- [ ] Include venue entrance instructions.
- [ ] Confirm food plan and nearby backup options.
- [ ] Add after-party logistics.
- [ ] Include arrival buffer due to traffic risk.
```

### attendee_logistics_email.md

```md
# Attendee Logistics Email

Subject: Getting to {event_name}

{attendee_logistics_email}
```

---

## 22. File / Repo Structure

Recommended repo:

```txt
sitelens/
  README.md
  design-doc.md
  .env.example

  frontend/
    package.json
    src/
      App.tsx
      api.ts
      components/
        VenueForm.tsx
        ResultCards.tsx
        TradeoffMatrix.tsx
        BoxOutputList.tsx
      styles.css

  backend/
    requirements.txt
    app/
      main.py
      config.py
      models.py
      services/
        box_service.py
        apify_service.py
        mapbox_service.py
        vision_service.py
        report_service.py
        agent_service.py
      data/
        demo_venues.json
        venue_a_places.json
        venue_b_places.json
      static/
        demo/
          venue_a_map.png
          venue_a_satellite.png
          venue_b_map.png
          venue_b_satellite.png
      outputs/
```

---

## 23. Backend Module Responsibilities

### `main.py`

- FastAPI app
- Routes:
  - `GET /api/health`
  - `POST /api/analyze-venues`

### `models.py`

Define Pydantic models:

```python
class VenueInput(BaseModel):
    name: str
    address: str

class AnalyzeVenuesRequest(BaseModel):
    event_name: str
    use_case: str
    event_goals: list[str]
    venue_a: VenueInput
    venue_b: VenueInput
    box_checklist_file_id: str | None = None
    box_output_parent_folder_id: str | None = None
```

### `box_service.py`

Functions:

```python
read_checklist(file_id: str) -> str
create_output_folder(parent_folder_id: str, folder_name: str) -> str
upload_file(folder_id: str, local_path: str, file_name: str) -> dict
```

### `apify_service.py`

Functions:

```python
fetch_nearby_places(address: str, categories: list[str]) -> dict
load_mock_places(venue_key: str) -> dict
summarize_places(raw_places: dict) -> dict
```

### `mapbox_service.py`

Functions:

```python
geocode_address(address: str) -> tuple[float, float]
get_map_snapshots(lat: float, lon: float, venue_key: str) -> dict
```

### `vision_service.py`

Functions:

```python
analyze_site_image(image_path: str) -> dict
```

### `agent_service.py`

Functions:

```python
compare_venues(inputs: dict) -> dict
```

### `report_service.py`

Functions:

```python
generate_comparison_report(result: dict) -> str
generate_site_packet(venue: dict) -> str
generate_action_checklist(result: dict) -> str
generate_attendee_email(result: dict) -> str
write_outputs_to_disk(files: dict) -> list[str]
```

---

## 24. Team Division

The team has four people: Jingyi, Simin, Kone, and Phohanh.
The split should use each person's background while still keeping the implementation parallel and hackathon-friendly.

Team backgrounds:

- **Jingyi**: Remote sensing / GIS + Computer Science
- **Simin**: Journalism / Finance + Computer Science
- **Kone**: Logistics / Computer Vision + Computer Science
- **Phohanh**: Computer Science (frontend focus)

The recommended split is:

```txt
Jingyi:   Geospatial reasoning + agent/product framing
Kone:     Map / vision / Apify / backend evidence pipeline
Phohanh:  Frontend implementation
Simin:    Decision narrative + report content + Box output polish
```

This split is intentionally based on each person's strongest domain fit, not on personal attributes.
With Phohanh joining and owning the React frontend, Simin can focus entirely on the content and storytelling layer — where her journalism and finance background adds the most value.

---

### Jingyi: Geospatial Reasoning Lead + Agent/Product Framing

Jingyi should own the part that makes SiteLens different from a generic map summary or RAG app.

Responsibilities:

- Define the core venue evaluation criteria:
  - Accessibility
  - Nearby Amenities
  - Event Atmosphere
  - Logistics Risk
  - Attendee Communication Needs
- Define the map/satellite visual signal schema:
  - water nearby
  - green space level
  - building density
  - road access
  - visible parking
  - land use context
- Design and refine the **Vision Evidence Prompt**
- Design and refine the **Decision Agent Prompt**
- Make sure the AI does not overclaim:
  - Do not call RGB map screenshots NDVI
  - Do not claim professional remote sensing classification
  - Use “map/satellite visual signals as one evidence layer”
- Validate whether the generated site observations are geographically reasonable
- Own the product framing:
  - SiteLens is not a generic site-selection tool
  - SiteLens is a DevRel event venue intelligence agent
  - SiteLens generates a Box planning packet, not just a map summary
- Prepare the final pitch and demo story

Key deliverables:

- `agent_service.py` prompt logic or prompt constants
- visual signal schema
- evaluation criteria
- polished sample report wording
- final 2-minute pitch
- README sections:
  - What it does
  - Why map/satellite evidence matters
  - Why this is an agent workflow

Success metric:

> Jingyi should make sure SiteLens sounds like a credible geospatial intelligence workflow, not just “AI looked at a map.”

---

### Kone: Map / Vision / Logistics Evidence Pipeline Lead

Kone should own the technical pipeline that turns venue addresses into usable evidence.

This fits Kone's logistics and computer vision background because this module combines spatial access, venue logistics, map images, visual evidence, and backend API integration.

Responsibilities:

- Implement backend FastAPI routes
- Implement or wire the map/geospatial pipeline:
  - geocoding fallback
  - Mapbox Static Images API
  - local map/satellite PNG fallback
- Implement or wire the vision evidence pipeline:
  - send map/satellite snapshots to vision model
  - parse structured JSON visual signals
  - handle fallback/mock visual signal outputs
- Implement Apify nearby-place data pipeline:
  - restaurants
  - coffee
  - parking
  - hotels
  - bars / after-party options
  - convenience stores
  - public transit
- Normalize POI data into a clean summary:
  - category counts
  - top places
  - ratings
  - review counts
- Own logistics-related interpretation support:
  - parking / rideshare risk
  - arrival convenience
  - after-party logistics
  - access constraints
- Implement fallback strategy:
  - mock venue coordinates
  - cached Apify JSON
  - local image files
- Wire backend services together so the demo works even if live APIs fail

Key deliverables:

- `main.py`
- `mapbox_service.py`
- `vision_service.py`
- `apify_service.py`
- `models.py`
- local fallback data:
  - `demo_venues.json`
  - `venue_a_places.json`
  - `venue_b_places.json`
  - map/satellite PNGs
- backend `/api/analyze-venues` endpoint

Success metric:

> Kone should make sure SiteLens has a stable evidence pipeline: address → map/visual evidence → POI data → structured venue evidence.

---

### Phohanh: Frontend Implementation Lead

Phohanh should own the React frontend from input to results display.

This fits Phohanh's CS background and frontend preference — the UI is the judges' first impression of SiteLens and needs to be clean, fast, and intuitive.

Responsibilities:

- Build the React frontend:
  - venue input form
  - loading state
  - results page
  - trade-off matrix
  - risk cards
  - organizer actions section
  - attendee logistics email section
  - Box output file list
- Design the result page so judges immediately understand:
  - what evidence was used
  - what each venue is better for
  - what risks exist
  - what the organizer should do next
- Wire the frontend to the backend `/api/analyze-venues` endpoint
- Start with mock data, then switch to live backend when ready
- Own frontend styling and layout polish
- README/demo screenshots if time allows

Key deliverables:

- `frontend/src/App.tsx`
- `VenueForm.tsx`
- `ResultCards.tsx`
- `TradeoffMatrix.tsx`
- `BoxOutputList.tsx`
- frontend styling

Success metric:

> Phohanh should make sure the judges can understand the value of SiteLens within 10 seconds of seeing the UI.

---

### Simin: Decision Narrative + Report Content + Box Output Polish Lead

Simin should own the part that turns raw AI output into a credible, professional planning artifact.

With Phohanh handling the frontend, Simin can focus entirely on what her journalism and finance background does best: structuring information, writing clearly under constraints, framing trade-offs, and making the output feel like a real deliverable — not just AI-generated text.

Responsibilities:

- Define and refine what goes inside each report file:
  - `venue_comparison_report.md` — executive summary, trade-off framing
  - `organizer_action_checklist.md` — action-oriented, prioritized
  - `attendee_logistics_email.md` — concise, attendee-friendly tone
- Improve report readability:
  - concise executive summary
  - clear trade-off framing (not just pros/cons)
  - evidence-backed risk explanations
  - action-oriented recommendations
- Own the “decision packet” feel:
  - not just data
  - not just AI text
  - a professional planning artifact a DevRel team would actually use
- Write README sections from the user's perspective:
  - What SiteLens does for event organizers
  - What the output looks like and why it matters
- Collaborate with Phohanh on what report data the UI should display
- Collaborate with Jingyi on final pitch wording and demo story

Key deliverables:

- report content templates and wording
- `organizer_action_checklist.md` structure
- `attendee_logistics_email.md` tone/format
- README user-facing sections
- demo narrative polish

Success metric:

> Simin should make sure that the Box output files feel like something a real event organizer would save and share — not just an AI dump.

---

### Shared Responsibilities

All four team members should jointly decide and validate:

- The second venue address
- The exact demo story
- The Box checklist content
- The fallback data quality
- The final GitHub README
- The final pitch wording
- End-to-end demo testing

Everyone should help avoid scope creep. The MVP should remain:

```txt
Two venue comparison
+ developer event use case
+ map/satellite evidence
+ Apify nearby places
+ Box checklist input
+ Box planning packet output
```

---

### Collaboration Plan

Recommended order of collaboration:

1. **Kone** gets backend mock endpoint working.
2. **Phohanh** builds frontend against the mock endpoint.
3. **Jingyi** finalizes prompts, schema, and sample output expectations.
4. **Kone** plugs in fallback data first, then live APIs if time allows.
5. **Simin** refines report content, wording, and decision packet structure.
6. **Jingyi + Phohanh** align on what data fields the UI should surface from the report.
7. **All four** test the end-to-end demo and prepare the pitch.

Do not wait for live integrations before building the UI.  
The frontend should first work with mock data, then switch to real backend outputs when available.

---

### Final Responsibility Summary

| Member | Background | Main Role | Core Output |
|---|---|---|---|
| **Jingyi** | Remote sensing / GIS + CS | Geospatial reasoning + agent/product framing | visual signal schema, prompts, evaluation criteria, pitch |
| **Kone** | Logistics / CV + CS | Map/vision/Apify/backend evidence pipeline | backend API, map snapshots, vision signals, POI summaries, fallbacks |
| **Phohanh** | CS (frontend focus) | Frontend implementation | React UI, venue form, results page, trade-off matrix, styling |
| **Simin** | Journalism / Finance + CS | Decision narrative + report content + Box output polish | report templates, organizer checklist, attendee email, README copy |



## 25. Implementation Plan

### Phase 0: Setup

Tasks:

1. Create GitHub repo.
2. Create frontend and backend folders.
3. Add `.env.example`.
4. Create `design-doc.md`.
5. Create Box folder and checklist file.
6. Confirm Apify token and Box token.
7. Confirm Mapbox token or prepare local map images.

### Phase 1: Backend skeleton

Tasks:

1. Implement FastAPI app.
2. Add `/api/health`.
3. Add `/api/analyze-venues` returning mock response.
4. Connect frontend to backend mock response.

Goal:

Frontend can display a fake venue comparison.

### Phase 2: Fallback data first

Tasks:

1. Add local demo venue data.
2. Add local POI JSON for Venue A and Venue B.
3. Add local map/satellite images.
4. Implement mock data loader.

Goal:

End-to-end demo works without any external API except LLM.

### Phase 3: Agent and reports

Tasks:

1. Implement decision agent prompt.
2. Generate JSON comparison.
3. Generate markdown reports.
4. Save outputs locally.

Goal:

Given two venue inputs, backend generates realistic reports.

### Phase 4: Box integration

Tasks:

1. Read checklist from Box.
2. Create output folder.
3. Upload markdown/csv/png files.
4. Return Box output links.

Goal:

Final packet appears in Box.

### Phase 5: Apify integration

Tasks:

1. Implement Apify actor call.
2. Normalize output.
3. Use fallback if Apify fails.

Goal:

Live POI data works when available.

### Phase 6: Mapbox integration

Tasks:

1. Implement geocoding or hardcoded venue coordinates.
2. Implement static image download.
3. Use fallback if Mapbox fails.

Goal:

Live map image works when available.

### Phase 7: Polish demo

Tasks:

1. Improve UI.
2. Add loading state.
3. Add clear error/fallback messages.
4. Add README.
5. Prepare 2-minute pitch.
6. Test demo several times.

---

## 26. Suggested Claude Code Prompts

Use these prompts one by one in Claude Code.

### Prompt 1: Scaffold backend

```txt
Create a FastAPI backend for the SiteLens project based on design-doc.md.

Implement:
- backend/app/main.py
- backend/app/models.py
- backend/app/config.py
- backend/app/services/report_service.py
- backend/requirements.txt

Add:
- GET /api/health
- POST /api/analyze-venues

For now, /api/analyze-venues should return a realistic mock response matching the design doc schema.
```

### Prompt 2: Scaffold frontend

```txt
Create a React + TypeScript + Vite frontend for SiteLens.

Implement:
- VenueForm component
- ResultCards component
- TradeoffMatrix component
- BoxOutputList component
- API client that calls POST /api/analyze-venues

The UI should show:
- two venue inputs
- use case and goals
- overall recommendation
- venue cards
- trade-off matrix
- organizer actions
- attendee logistics email
- generated Box files
```

### Prompt 3: Add fallback data

```txt
Add mock/fallback data support for SiteLens.

Create:
- backend/app/data/demo_venues.json
- backend/app/data/venue_a_places.json
- backend/app/data/venue_b_places.json

Implement apify_service.py with:
- load_mock_places
- summarize_places
- fetch_nearby_places that uses mock data when USE_MOCK_DATA=true

Return normalized POI summaries by category.
```

### Prompt 4: Add agent reasoning

```txt
Implement agent_service.py for SiteLens.

It should accept:
- event_name
- use_case
- event_goals
- venue A visual signals
- venue B visual signals
- venue A POI summary
- venue B POI summary
- checklist text

It should call the configured LLM and return structured JSON:
- overall_recommendation
- venue_a_positioning
- venue_b_positioning
- tradeoff_matrix
- key_risks
- organizer_actions
- attendee_logistics_email
- evidence_sources

Use the prompt and schema from design-doc.md.
```

### Prompt 5: Add Box integration

```txt
Implement box_service.py for SiteLens.

Functions:
- read_checklist(file_id)
- create_output_folder(parent_folder_id, folder_name)
- upload_file(folder_id, local_path, file_name)

Use BOX_DEVELOPER_TOKEN for MVP.

Update /api/analyze-venues to:
- read checklist from Box if file id is provided
- generate report files locally
- create output folder in Box
- upload markdown/csv/png files
- return uploaded file metadata
```

### Prompt 6: Add Mapbox integration

```txt
Implement mapbox_service.py.

Functions:
- geocode_address(address)
- get_map_snapshots(lat, lon, venue_key)

Use Mapbox Static Images API if MAPBOX_TOKEN is available.
If USE_MOCK_DATA=true or Mapbox fails, return local fallback image paths.
```

### Prompt 7: Add polish

```txt
Polish SiteLens for hackathon demo.

Add:
- loading state
- error messages
- fallback indicators
- nicer trade-off matrix
- generated file links
- README with setup, architecture, sponsor usage, and demo script
```

---

## 27. README Requirements

The README should include:

```md
# SiteLens

## What it does
SiteLens compares two event venues using map/satellite visual signals, nearby-place data from Apify, and event planning checklists stored in Box. It generates an evidence-backed venue planning packet and saves it back to Box.

## Why it matters
Event teams spend time manually checking maps, nearby restaurants, parking, after-party options, and logistics risks. SiteLens turns that into a repeatable agent workflow.

## How we use Box
- Read event checklist from Box
- Save generated venue comparison packet back to Box

## How we use Apify
- Collect nearby places such as restaurants, coffee shops, parking, hotels, and bars

## Agent workflow
- Planner
- Map evidence
- Places evidence
- Box checklist
- Decision agent
- Report agent
- Box upload

## Demo
Compare two Seattle venues for a 100-person AI developer event.
```

---

## 28. Final Demo Script

Use this for a 2-minute presentation.

```txt
Most AI agents reason over text. But many real-world decisions depend on places.

We built SiteLens, a site intelligence agent for DevRel and event teams. When planning a developer event, organizers usually check maps, nearby restaurants, parking, after-party options, and internal event checklists manually. SiteLens automates that workflow.

For the demo, we compare two Seattle venues for a 100-person AI developer event. SiteLens reads our event venue checklist from Box, uses map and satellite snapshots to extract visible site signals, and uses Apify to collect nearby places like restaurants, coffee shops, parking, hotels, and bars.

Then the agent generates a venue trade-off report. It does not simply say one venue is good and one is bad. It explains what each venue is better for, identifies logistics risks, and produces concrete organizer actions.

The most useful part is that SiteLens also generates an attendee logistics email, such as whether to recommend rideshare, include parking instructions, or mention nearby after-party options.

Finally, SiteLens saves the complete planning packet back to Box: the comparison report, individual site packets, nearby places summary, organizer checklist, attendee email, and map snapshots.

So SiteLens turns venue research from a manual map-checking process into an evidence-backed planning workflow.
```

---

## 29. Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Box auth takes too long | High | Use developer token for MVP; test early |
| Apify actor slow or unreliable | Medium | Cache POI JSON fallback |
| Mapbox token/billing issue | Medium | Store local map/satellite PNGs |
| Vision model overclaims | Medium | Use conservative prompt; allow unknown |
| Output feels like generic summary | High | Emphasize trade-offs, action items, attendee email |
| Scope grows too large | High | Only support developer event venue comparison |
| Venue B choice weak | Medium | Pick a second venue that is plausible, not obviously bad |
| Box upload fails during demo | High | Also save local outputs; retry upload |

---

## 30. Venue B Selection Guidance

Choose Venue B carefully. Do not compare thinkspace to an obviously bad industrial warehouse.

Good Venue B should be:

- A real Seattle event space
- Plausible for developer events
- Different enough from thinkspace to create trade-offs
- Not obviously better or worse

Possible types:

- Capitol Hill event space
- Fremont event space
- Ballard event space
- Downtown coworking/event space
- University District event space

The comparison should feel like:

```txt
Venue A: stronger professional / office / weekday event fit
Venue B: stronger social / after-party / neighborhood energy fit
```

Not:

```txt
Venue A is clearly good; Venue B is clearly bad.
```

---

## 31. Final MVP Definition

By the end of the hackathon, SiteLens should be able to:

1. Accept two venue addresses.
2. Use or load map/satellite evidence.
3. Use or load Apify nearby-place data.
4. Read an event venue checklist from Box.
5. Generate a nuanced venue comparison.
6. Generate organizer action items.
7. Generate an attendee logistics email.
8. Save the complete planning packet to Box.
9. Present the output in a clean UI.
10. Explain why Box, Apify, and AI agents are essential to the workflow.

---

## 32. What Not to Say in Pitch

Avoid:

```txt
We built a site selection tool.
We built a remote sensing model.
We predict foot traffic.
We know which venue is objectively best.
We do professional GIS analysis.
```

Say:

```txt
We built a site intelligence agent.
We use map and satellite visual signals as one evidence layer.
We compare venues for a specific event use case.
We generate planning packets, risks, and attendee logistics.
We save the evidence-backed workflow back to Box.
```
