# UrbanPulse — Build Plan

Phased plan with effort in **person-days**, so you can map it to your actual team size and deadline. Sequenced by dependency, not by module number.

> **Assumptions to correct me on:** ~4–6 people, at least one comfortable with ML training, one with frontend. Effort totals ~34 person-days on the critical path; a 5-person team with genuine parallelism lands the must-have set in roughly 10–12 calendar days.

---

## The one rule: vertical slice before vertical depth

Do **not** build modules 1→14 in order. Build the thinnest possible end-to-end path first — one video, one detection class, one dot on a map — then thicken it. Teams that build seven excellent detectors and wire them together on the last night demo nothing.

```
P1 vertical slice ──► everything else is thickening a working pipe
```

---

## P0 — Contracts & walking skeleton · 2 pd

Nothing intelligent; everything connected.

- [ ] Repo layout per ARCHITECTURE.md §10, `git init`, `.gitignore` for `data/`
- [ ] `contracts/event.schema.json` wired into both sides as a real validator (`jsonschema`)
- [ ] `docker-compose.yml`: PostGIS + MQTT broker (Mosquitto) + FastAPI + React dev server
- [ ] Edge stub publishes a hardcoded event → ingest writes it → API serves it → dashboard renders it
- [ ] `make demo` / `docker compose up` starts everything from cold

**Exit:** a fake event travels the full path. Now the pipe exists and every later phase is an increment.

## P1 — Vertical slice · 3 pd

- [ ] `CameraSource` (video file) + `GpsSource` (CSV trace), time-synchronized
- [ ] COCO YOLOv8n via `cv2.dnn` on ONNX — vehicles and persons, no training
- [ ] Emit real `traffic_state` events with bus GPS
- [ ] PostGIS storage with GiST index; Leaflet map plots live events over WebSocket

**Exit:** real video in, real dots on a real map. **This is the milestone that guarantees you have something to show.** Hit it early.

## P2 — Geometry layer · 2 pd · ⚠ unblocks 6 modules

See ARCHITECTURE.md §2.2. Highest leverage in the project; do not defer it.

- [ ] Calibration script: pick 4 road-plane points, derive homography, persist per camera
- [ ] `pixel_to_road_plane()` → `(lateral_m, forward_m)`
- [ ] `project_subject_position()`: bus GPS + heading + offsets → subject lat/lon
- [ ] OSM import into PostGIS + map-match/snap to centreline
- [ ] Populate `geometry` and `location.subject` on every event

**Exit:** a detection's own position on the map, in metres, not the bus's.

## P3 — Infrastructure detector · 4 pd · parallel with P2

- [ ] RDD2022 (India subset) + Roboflow pothole sets → unified YOLO dataset
- [ ] Handle the partial-label problem (ARCHITECTURE.md §8) — decide and document
- [ ] Fine-tune `yolo-infra`: pothole, crack, waterlogging, signboard, zebra, divider
- [ ] Export ONNX, INT8 quantize, benchmark fps on your actual demo machine
- [ ] Defect analyzer emits `road_defect` events with `estimated_size_m2`

**Exit:** potholes detected on your own city footage with a measured mAP you can quote.

## P4 — Traffic & safety analyzers · 3 pd

- [ ] ByteTrack on `yolo-dyn`; track-based counting (no double-count)
- [ ] Density as **vehicles per 100 m of lane** via geometry, not per frame
- [ ] Congestion classifier: density + ground speed + dwell → `free_flow…jam`
- [ ] Pedestrian risk: crossing-zone polygon + person + no yielding vehicle
- [ ] **Ego-motion compensation** (ARCHITECTURE.md §2.4) → ground-frame velocity
- [ ] Rash driving on ground-frame accel / jerk / weaving / time-headway

**Exit:** congestion levels track reality on your footage, and rash-driving alerts don't fire every time the bus brakes.

## P5 — ANPR · 3 pd

- [ ] Fine-tune plate detector (~500 Indian plate images)
- [ ] Range gate from geometry before invoking OCR
- [ ] PaddleOCR/EasyOCR with per-character confidences
- [ ] **Multi-frame voting across the track** → `aggregate_confidence`, `frames_voted`
- [ ] Stage the demo incident deliberately: a clip where a vehicle passes close and readable

**Exit:** a plate read with a defensible confidence score, on a repeatable clip.

## P6 — Edge hardening · 3 pd

- [ ] SQLite outbox + MQTT QoS1 persistent session, delta-sync, exponential backoff
- [ ] Priority lane so incidents overtake queued potholes
- [ ] **Dead-zone demo: pull the network, keep detecting, reconnect, watch it drain.** Rehearse this — it's your most convincing 30 seconds
- [ ] Face + non-flagged-plate blur, **before any persist**
- [ ] Envelope encryption for plate evidence (ARCHITECTURE.md §5.2)
- [ ] ECDSA signing + hash chain; central verifies and detects `seq` gaps
- [ ] Bandwidth meter both sides → live reduction ratio on the dashboard

**Exit:** offline resilience, privacy and integrity all demonstrable as live actions rather than claims.

## P7 — Fusion · 3 pd

- [ ] DBSCAN in UTM (or haversine radians) — **space only**, time as the confidence axis
- [ ] Asset inventory with `candidate → confirmed → missing → repaired` lifecycle
- [ ] OSM prior seeding for expected crossings and signals
- [ ] Pass/miss counting with `visibility_ok` gating → **absence detection**
- [ ] Severity scoring with weights in config, road class from OSM join
- [ ] Work-order queue, severity-ranked

**Exit:** multiple buses over one pothole raise one high-confidence event; a removed sign gets flagged after N clean passes.

## P8 — Analytics · 3 pd

- [ ] Congestion heatmap aggregated over space+time
- [ ] Hashed plate tokens → O-D matrix + link travel times
- [ ] Synthetic GTFS + route-delay computation vs schedule
- [ ] Infrastructure deficiency report grouped by ward/road
- [ ] Incident report export (PDF/CSV) with evidence references

**Exit:** every analytics line in the PS has a screen behind it.

## P9 — Demo hardening · 4 pd

- [ ] **Offline Leaflet tiles** — verify with the network unplugged (ARCHITECTURE.md §7)
- [ ] Pre-seed DB with synthetic fleet history so maps aren't empty
- [ ] `sim/fleet_replay.py`: 3–4 simulated buses on overlapping routes
- [ ] Dashboard polish; single-command cold start
- [ ] Metrics slide: mAP per class, fps, bandwidth ratio, consensus precision — **measured**
- [ ] `docs/demo_script.md`: a timed run order with a fallback if live inference stalls
- [ ] Rehearse end-to-end twice on the actual demo machine

---

## Parallelization

| Role | Owns |
|---|---|
| ML | P3 (detector), P5 (plates/OCR) — start dataset prep on day 1; downloads and training are the long poles |
| Edge / CV | P1, P2 (geometry), P4 (analyzers, ego-motion) |
| Backend | P0, P6 (queue, crypto), P7 (fusion), P8 (analytics) |
| Frontend | P1 map, then P9; builds against the schema with seeded data, never blocked on the edge |
| Anyone | Record real bus footage + GPS trace — **day 1, weather and daylight dependent** |

Two hard scheduling facts: **dataset download and training must start on day 1** (RDD2022 is large, training is wall-clock you can't compress), and **footage collection is weather-dependent** — a monsoon afternoon is a gift for waterlogging data and a disaster for a filming schedule.

---

## Kill list, in order

When you run short, cut from the top. Decide now, not at 2am.

1. Signboard OCR legibility check
2. Divider-gap detection
3. Incident report PDF export (CSV is enough)
4. O-D matrix (keep link travel times — cheaper, still impressive)
5. Waterlogging as a *scored* class (keep detection, drop severity integration)

**Never cut:** P1 slice, P2 geometry, bandwidth story, fleet consensus, privacy+integrity, offline map tiles.

---

## Risk register

| Risk | Mitigation |
|---|---|
| Venue network fails | Everything offline: local tiles, local broker, no cloud calls. Test unplugged. |
| Live inference stalls in the demo | Pre-recorded fallback run captured in advance; `demo_script.md` names the switch point. |
| Pothole model generalizes poorly | Train on RDD2022's India subset; validate on *your own* footage, not a held-out split of the same dataset. |
| Rash-driving false positives | Ego-motion compensation (P4). Without it this module is noise. |
| Consensus never clusters | Wrong `eps` or unprojected coordinates (ARCHITECTURE.md §2.3). Verify on hand-made overlapping traces first. |
| Demo laptop reboots | `docker compose up` cold start, rehearsed. |
| Judge asks about privacy | §5 answers it as implemented behaviour, not intent. |

---

## Open questions for you

1. **Days until internal submission**, and is it judged as a live demo, a video, or a deck? Changes P9 substantially.
2. **Team size and skill split** — lets me re-cut the parallelization table to real names.
3. **Your city**, for OSM extract, bus routes and footage collection.
4. **Demo machine GPU** — decides whether live multi-camera inference is realistic or you pre-compute detections and replay them.
