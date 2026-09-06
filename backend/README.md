# URBANPULSE — AI-Powered Urban Road Intelligence Backend
**Smart India Hackathon (SIH)**

URBANPULSE converts public transport buses into mobile urban sensing units. As buses traverse the city, onboard front, rear, and side cameras stream video frames to AI/YOLO modules. The **UrbanPulse Central Backend** ingests these multi-camera detections, correlates observations across space and time, safely stores evidence frames, runs module-aware OCR text extraction, calculates dynamic road risk indices, coordinates action response teams, and generates official PDF incident dossiers.

---

## Key Features & Capabilities

1. **5 Core AI Ingestion Modules Supported**:
   - **Pothole / Road Defect**: Multi-camera spatial correlation ($\le 25\text{m}$, $\le 5\text{min}$) prevents duplicate incidents. Co-location evaluates submerged waterlogged pothole risk.
   - **Damaged / Missing Traffic Signs**: Tracks sign health with OCR reading on speed limit and warning signs.
   - **Vehicle Density & Classification**: Aggregates car, bike, bus, and truck counts with speed and trajectory tracking.
   - **Traffic Bottlenecks**: Analyzes multi-bus segment velocity and density trends rather than single transient delays.
   - **Vulnerable Pedestrian Situations**: Ingests crossing states and safety hazard levels (LOW/MEDIUM/HIGH) with AI event reconstructions.
2. **Special Intelligence Case — Waterlogged Pothole**:
   - Probabilistic assessment ($84\%$) fusing road depression cues, standing water radar/sensor flags, and historical road condition archives.
3. **Showcase Incident INC-2048**:
   - Pre-seeded high-fidelity demonstration dossier: *Possible Hit-and-Run on Anna Salai* with 2 tracked vehicles (`TN 09 BX 4412` & `TN 07 CP 8821`), 6 evidence frames, and 5 chronological timeline events.
4. **Automated ReportLab PDF Export**:
   - Generates publication-quality, branded municipal incident reports at `GET /api/v1/incidents/{id}/export` with AI disclaimer notices, vehicle intel, OCR readouts, timeline logs, and embedded evidence snapshots.
5. **Pluggable Architecture**:
   - **Storage**: Local filesystem storage (`storage/evidence/`) with an abstraction layer for simple migration to AWS S3 / MinIO.
   - **OCR Engine**: Pluggable OCR service supporting `pytesseract` / `easyocr` with fallback.
   - **Database**: Automatic SQLite fallback for local developer setups and full PostgreSQL / PostGIS support for staging/production.

---

## Project Structure

```
urbanpulse-backend/
│
├── app/
│   ├── main.py                    # FastAPI entrypoint, middleware, static files, lifecycle
│   ├── core/
│   │   ├── config.py              # App settings (Pydantic Settings), CORS, paths
│   │   └── errors.py              # Uniform error envelope & exception handlers
│   ├── db/
│   │   ├── session.py             # Database engine, sessionmaker, ping check
│   │   └── base.py                # Declarative Base
│   ├── models/
│   │   ├── incident.py            # Incidents (INC-2048, types, status, waterlogged prob)
│   │   ├── observation.py         # AI camera observations (multi-camera detections)
│   │   ├── evidence.py            # Evidence frames, image paths, OCR outputs, bounding boxes
│   │   ├── evidence_timeline.py   # Chronological AI event reconstruction timeline
│   │   ├── vehicle.py             # Vehicle intelligence & classifications
│   │   ├── road.py                # Road & Road Segment entities with risk metrics
│   │   ├── camera.py              # Camera & Bus fleet models
│   │   ├── action.py              # Action Center items (assignment, ETA, resolution)
│   │   └── notification.py        # System alerts & notifications
│   ├── schemas/
│   │   ├── common.py              # Standard API envelopes & pagination
│   │   ├── ai_ingestion.py        # Generic & module-specific AI detection payloads
│   │   ├── incident.py            # Incident request/response schemas
│   │   ├── evidence.py            # Evidence & timeline schemas
│   │   ├── vehicle.py             # Vehicle schemas
│   │   ├── road.py                # Road risk & segment schemas
│   │   ├── camera.py              # Camera & Bus schemas
│   │   ├── heatmap.py             # Geographic heatmap schemas
│   │   ├── analytics.py           # Dashboard KPIs & analytics trend schemas
│   │   ├── action.py              # Action center schemas
│   │   ├── notification.py        # Notification schemas
│   │   └── search.py              # Global search response schema
│   ├── integrations/
│   │   ├── storage/               # Local filesystem storage + S3/MinIO interface
│   │   │   └── local_storage.py
│   │   └── ocr/                   # Pluggable OCR engine (pytesseract/EasyOCR/fallback)
│   │       └── ocr_service.py
│   ├── services/
│   │   ├── ai_ingestion_service.py # Ingestion pipeline, correlation, module processing
│   │   ├── incident_service.py    # Incident queries, status lifecycle, timeline builder
│   │   ├── road_risk_service.py   # Multi-factor road risk calculation & updates
│   │   ├── heatmap_service.py     # Clustered geospatial risk queries
│   │   ├── analytics_service.py   # KPIs, incident distributions, AI performance stats
│   │   ├── action_service.py      # Action dispatching & resolution workflow
│   │   ├── notification_service.py# System alert triggers
│   │   ├── search_service.py      # Global multi-entity search
│   │   ├── pdf_report_service.py  # ReportLab branded PDF export engine
│   │   └── seed_service.py        # Rich SIH demo dataset loader
│   └── api/
│       ├── health.py              # GET /health
│       └── v1/
│           ├── router.py          # Unified API v1 router
│           ├── ai_ingestion.py    # POST /api/v1/ai/detections (Multipart & JSON)
│           ├── dashboard.py       # GET /api/v1/dashboard/kpis, summary
│           ├── incidents.py       # GET /api/v1/incidents, details, status, PDF export
│           ├── roads.py           # GET /api/v1/roads, details, recalculate risk
│           ├── cameras.py         # GET /api/v1/cameras, buses
│           ├── vehicles.py        # GET /api/v1/vehicles
│           ├── heatmap.py         # GET /api/v1/heatmap
│           ├── analytics.py       # GET /api/v1/analytics/overview, trends, ai-stats
│           ├── notifications.py   # GET /api/v1/notifications, mark read
│           ├── actions.py         # GET/POST/PATCH /api/v1/actions
│           └── search.py          # GET /api/v1/search
├── storage/
│   └── evidence/                  # Stored evidence images
├── tests/                         # Pytest test suite (21 passing tests)
├── scripts/
│   └── verify_live.py             # Automated end-to-end verification script
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start & Running

### Option 1: Local Python (Fastest for Dev & Demo)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the FastAPI server (auto-creates tables and seeds demo data on port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Docker Compose (PostgreSQL + PostGIS)
```bash
docker-compose up --build
```

---

## Interactive API Documentation
Once running, open your browser:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## Complete API Reference

| Area | Method | Path | Description |
|---|---|---|---|
| **Health** | `GET` | `/health` | System health and database connectivity |
| **AI Ingestion** | `POST` | `/api/v1/ai/detections` | Ingest detection metadata + camera frame file |
| **Dashboard** | `GET` | `/api/v1/dashboard/kpis` | Active Incidents, High-Risk Roads, Potholes, AI Detections |
| **Dashboard** | `GET` | `/api/v1/dashboard/summary` | Dashboard summary alias |
| **Incidents** | `GET` | `/api/v1/incidents` | List incidents (filters: status, module, severity, road_id) |
| **Incidents** | `GET` | `/api/v1/incidents/{id}` | Full incident dossier (vehicles, timeline, evidence frames) |
| **Incidents** | `PATCH` | `/api/v1/incidents/{id}/status` | Transition status (Under Review $\to$ Verified $\to$ Assigned $\to$ Resolved) |
| **Incidents** | `GET` | `/api/v1/incidents/{id}/evidence` | Evidence frames & timeline events |
| **PDF Export** | `GET` | `/api/v1/incidents/{id}/export` | Generate & download official PDF report |
| **Roads** | `GET` | `/api/v1/roads` | List roads with multi-factor risk scores |
| **Roads** | `GET` | `/api/v1/roads/{id}` | Road detail with segments and active incident count |
| **Roads** | `POST` | `/api/v1/roads/{id}/recalculate-risk` | Recalculate dynamic risk based on underlying metrics |
| **Cameras** | `GET` | `/api/v1/cameras` | List fleet cameras (e.g. `CAM-042`) |
| **Cameras** | `GET` | `/api/v1/cameras/{id}` | Camera details & latest frame timestamp |
| **Fleet** | `GET` | `/api/v1/buses` | List buses and onboard camera rigs |
| **Vehicles** | `GET` | `/api/v1/vehicles` | List vehicle observations with plates & speeds |
| **Vehicles** | `GET` | `/api/v1/vehicles/{id}` | Vehicle observation details |
| **Heatmap** | `GET` | `/api/v1/heatmap` | Geographic risk heatmap points (`time_range`, `risk_type`) |
| **Analytics** | `GET` | `/api/v1/analytics/overview` | Trends, distributions, response times, AI accuracy |
| **Analytics** | `GET` | `/api/v1/analytics/trends` | Historical incident trend points |
| **Analytics** | `GET` | `/api/v1/analytics/ai-performance` | Detection stats and per-module breakdown |
| **Notifications**| `GET` | `/api/v1/notifications` | List alerts (filter `unread_only`) |
| **Notifications**| `PATCH` | `/api/v1/notifications/{id}/read` | Mark alert as read |
| **Notifications**| `POST` | `/api/v1/notifications/mark-all-read` | Mark all alerts read |
| **Action Center**| `GET` | `/api/v1/actions` | List response dispatches and unit assignments |
| **Action Center**| `POST` | `/api/v1/actions` | Dispatch new response unit for incident |
| **Action Center**| `PATCH` | `/api/v1/actions/{id}` | Update action status & resolution notes |
| **Action Center**| `GET` | `/api/v1/actions/incident/{id}` | Actions linked to specific incident |
| **Search** | `GET` | `/api/v1/search?q={query}` | Global unified search (incidents, roads, vehicles, cameras) |

---

## How AI Modules Send Data

AI modules (YOLOv8 / Tracking) send detection results via `POST /api/v1/ai/detections`.

### Example 1: JSON Payload (e.g. Road Defect)
```bash
curl -X POST "http://localhost:8000/api/v1/ai/detections" \
  -H "Content-Type: application/json" \
  -d '{
    "module": "road_defect",
    "incident_type": "Pothole / Road Defect",
    "bus_id": "BUS-104",
    "camera_id": "CAM-042",
    "camera_position": "front",
    "latitude": 13.0604,
    "longitude": 80.2496,
    "location_name": "Anna Salai",
    "confidence": 0.91,
    "severity": "High",
    "defect_type": "deep_pothole",
    "defect_size_cm": 40.0
  }'
```

### Example 2: Multipart Form-Data (With Evidence Camera Image)
```python
import requests
import json

url = "http://localhost:8000/api/v1/ai/detections"

metadata = {
    "module": "vehicle_density",
    "bus_id": "BUS-104",
    "camera_id": "CAM-042",
    "camera_position": "front",
    "latitude": 13.0604,
    "longitude": 80.2496,
    "location_name": "Anna Salai",
    "confidence": 0.94,
    "vehicles": [
        {
            "track_id": "Vehicle A",
            "vehicle_type": "car",
            "color": "Silver",
            "license_plate": "TN 09 BX 4412",
            "speed_kmh": 48.0,
            "direction": "Northbound",
            "lane": "Lane 2",
            "confidence": 0.92
        }
    ]
}

with open("evidence_frame.jpg", "rb") as img_file:
    files = {"image": ("evidence_frame.jpg", img_file, "image/jpeg")}
    data = {"data": json.dumps(metadata)}
    response = requests.post(url, data=data, files=files)
    print(response.json())
```

---

## Frontend Integration Guide

Replace mock/simulated frontend hooks with real backend API endpoints:

| Frontend Feature | Backend API Endpoint |
|---|---|
| Dashboard KPIs Cards | `GET /api/v1/dashboard/kpis` |
| Live City Map & Incidents | `GET /api/v1/incidents?status=Active` |
| Risk Heatmap Overlay | `GET /api/v1/heatmap?time_range=7_days&risk_type=all` |
| Incident Dossier (INC-2048) | `GET /api/v1/incidents/INC-2048` |
| Export Dossier PDF | `GET /api/v1/incidents/INC-2048/export` |
| Road Risk Analytics Table | `GET /api/v1/roads` |
| Action Center Dispatches | `GET /api/v1/actions` |
| Notification Bell Alerts | `GET /api/v1/notifications?unread_only=true` |
| Global Navbar Search | `GET /api/v1/search?q={query}` |

---

## Testing & Verification

Run the automated test suite:
```bash
pytest -v
```

Run the live end-to-end verification script:
```bash
python scripts/verify_live.py
```
