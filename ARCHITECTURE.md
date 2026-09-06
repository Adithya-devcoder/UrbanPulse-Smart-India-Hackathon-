# UrbanPulse — System Architecture

**SIH Problem Statement 26124** · Bharat Electronics Limited
*AI-Powered Mobile Urban Intelligence Platform Using Public Transport Fleet*

---

## 0. Design constraints

| Constraint | Consequence |
|---|---|
| **Software-only, no hardware** | The onboard node is a real, separately-deployed process fed by recorded video + a synchronized GPS trace through a `CameraSource`/`GpsSource` abstraction. Swapping to live cameras = swapping one module. Never fake the architecture, only the sensors. |
| **Bandwidth is a scored requirement** | The uplink is a metered chokepoint with instrumentation. We report a measured reduction ratio, not an estimate. |
| **Evidence may feed enforcement** | Every event is signed at the edge and hash-chained. Plates are sealed under an authority key, not stored in plaintext. |
| **Edge compute is finite** | **3 models total, not 7.** A per-camera frame budget, not "run everything on every frame." |

---

## 1. Topology

```
┌────────────────── BUS EDGE NODE (one process per bus) ───────────────────┐
│                                                                          │
│  CameraSource ──► FrameScheduler ──► Stage-1 ──► Geometry ──► Analyzers   │
│  GpsSource          (per-camera     ├ yolo-dyn   (IPM,        (5 rule     │
│  (file | rtsp)       fps budget)    └ yolo-infra  localize)    engines)   │
│                                          │                          │     │
│                                   Stage-2 on trigger                │     │
│                                   plate → OCR → vote                │     │
│                                                                     ▼     │
│  PrivacyFilter ─► EvidenceEncoder ─► IntegritySigner ─► SQLite ─► Uplink  │
│                                                         queue        │    │
└──────────────────────────────────────────────────────────────────────│────┘
                                                     MQTT QoS1 over TLS │
┌───────────────────── CENTRAL PLATFORM ────────────────────────────────▼───┐
│  IngestGateway — authN, signature + hash-chain verify, idempotent dedupe  │
│        ▼                                                                  │
│  PostGIS ──► FusionEngine ──────► AnalyticsEngine ──► FastAPI ──► React   │
│  event       consensus clustering  congestion heatmap            Leaflet  │
│  store       asset inventory       O-D matrix (hashed)                    │
│              absence detection     route delay vs GTFS                    │
│              severity scoring      work-order queue                       │
└───────────────────────────────────────────────────────────────────────────┘
```

`contracts/event.schema.json` is the **single source of truth** between the two halves. Edge validates on write, central validates on ingest. This is what prevents the 3am "frontend expected `lat`, backend sent `latitude`" failure.

---

## 2. The seven corrections to the module plan

### 2.1 Three models, not seven — merge by *motion class*, split by *frame rate*

Seven separate YOLOs cannot co-run on one edge device. But you don't need them, because your classes split naturally into things that move and things that don't:

| Model | Classes | Training needed | Cameras / rate |
|---|---|---|---|
| `yolo-dyn` | car, bus, truck, motorcycle, autorickshaw, person, bicycle | **None** — COCO-pretrained covers all but autorickshaw | Front @ 10 fps, rear @ 5 fps |
| `yolo-infra` | pothole, road_crack, waterlogging, signboard, zebra_crossing, divider | Custom, one unified dataset | Front @ 3 fps, sides @ 2 fps |
| `plate` + OCR | license_plate → characters | Custom detector, pretrained OCR | Stage-2, on trigger only |

Two consequences worth internalizing:

- **Modules 3, 4, 5 and 6 need zero model training.** COCO YOLOv8 already gives you vehicles and persons at good accuracy. All your training budget goes to `yolo-infra` and the plate detector. This is the difference between a working demo and a week lost to labelling.
- Static infrastructure doesn't need 30 fps. A pothole at 40 km/h is visible for ~2 s; 3 fps gives you 6 chances. Dynamic objects need high rate for tracking continuity. The rate split *is* the compute budget.

At 40 km/h the bus covers 11 m/s, so front @ 10 fps ≈ one frame per 1.1 m of road — comfortable overlap for defect coverage without redundancy.

### 2.2 The geometry layer is the highest-leverage component in the system

**This is the single most important thing missing from the module table.** Add it before anything else that depends on measurement.

A bounding box in pixels is meaningless as a severity proxy: a pothole 5 m ahead and one 40 m ahead differ ~64× in box area for identical physical size. Module 14's "bbox area as size proxy" will rank distant large potholes below nearby small ones.

Fix: **inverse perspective mapping.** Assume a locally flat road plane, fix camera height `h`, pitch `θ` and intrinsics, and compute a homography `H` once per camera:

```python
H = cv2.getPerspectiveTransform(image_quad, road_plane_quad)  # calibrate once
```

Take the bottom-centre of each bbox (where the object meets the road) and map it through `H` to get metric offsets `(lateral_m, forward_m)` relative to the bus. Calibrate `H` from anything of known dimension in-frame — lane width (3.5 m standard), zebra stripe pitch, a measured object placed on the ground during a calibration recording.

~100 lines of OpenCV. Look at what it unlocks:

| Module | Without geometry | With geometry |
|---|---|---|
| 1 Road defects | pixel blob | **defect area in m²** |
| 3/4 Density | vehicle count per frame | vehicles per **100 m of lane** — a real density unit |
| 6 Rash driving | image-space motion | **ground-frame velocity** (see 2.4) |
| 7 ANPR | fire OCR and hope | fire OCR **only inside the readable range** |
| 12 Consensus | cluster on bus GPS | cluster on **defect GPS** (see 2.3) |
| 14 Severity | scale-dependent noise | **defensible m² × road-class score** |

One component, six modules. Build it in phase 2.

### 2.3 GPS marks the bus, not the defect

The event's GPS is the bus's position. The pothole is 10–30 m ahead, and at 1 Hz GPS the bus has moved another ~11 m by the time you tag it. That's 15–40 m of error — larger than the ~15 m DBSCAN radius Module 12 needs, so consensus clusters either never form or merge two adjacent potholes into one.

```
subject_pos = bus_pos + R(heading) · (lateral_m, forward_m)   # from 2.2
subject_pos = snap_to_road_centreline(subject_pos)            # OSM map-match
```

Then two DBSCAN bugs to avoid:
- **Don't cluster on raw lat/lon with a Euclidean metric.** A degree of longitude at 13°N is ~108 km; a degree of latitude ~111 km. Project to UTM (Zone 43N/44N for most of India) or use `metric="haversine"` with `eps` in radians (`eps_m / 6_371_000`).
- **Don't add timestamp as a third dimension.** Seconds and metres have no common scale — the distance function becomes meaningless. Cluster in **space only**, then use time as the axis along which confidence accumulates (independent passes over hours/days) and along which repairs are detected (asset stops being reported → closed).

### 2.4 "Rash driving" from a moving camera needs ego-motion compensation

This is the module most likely to silently not work in your demo. When the bus brakes, *every* vehicle in frame appears to accelerate toward the camera. Image-space "sudden acceleration/direction change" thresholds will fire constantly on the bus's own behaviour.

With the geometry layer, tracked positions are already in road-plane metres relative to the bus. Differentiate for relative velocity, then add the bus's own velocity vector from GPS:

```
v_ground(target) = d/dt[road_plane_pos(target)] + v_bus(from GPS heading + speed)
```

Now `rash` is defined on ground-frame quantities that mean something: longitudinal acceleration, jerk, lateral weaving amplitude, and time-headway to the vehicle ahead. Cross-check ego-motion with sparse optical flow on static background (`cv2.calcOpticalFlowPyrLK` on road/building features) — it validates the GPS-derived estimate and covers GPS dropout.

### 2.5 "Missing" anything requires a temporal baseline, not a frame

Modules 1 and 2 ask for **missing** dividers, **missing** zebra crossings, **missing** signboards. A detector reports what it sees; absence is not a detection. A single frame with no signboard is indistinguishable from a frame where a truck occluded it.

Two-source baseline:

1. **OSM prior** — OpenStreetMap already contains `highway=crossing` nodes, `traffic_signals`, and often `traffic_sign` tags. Seed expected asset locations for free.
2. **Fleet-built inventory** — every confirmed detection registers an asset at a map-matched location. After *k* independent confirmations, the asset is `CONFIRMED` and becomes part of the expected baseline.

Absence is then a state transition on an inventory record:

```
for each bus pass through the asset's visibility window:
    if not detected and visibility_ok(pass):
        asset.consecutive_misses += 1
if asset.consecutive_misses >= N:      # N ≈ 3–5 clean passes
    raise event(subtype="missing_<asset_type>", confidence=f(misses, quality))
```

`visibility_ok` is the part that keeps false alarms down: daylight, no large occluding bbox overlapping the expected image region, bus in the correct lane, speed below a motion-blur threshold. A miss during a truck occlusion doesn't count.

This is a genuinely strong answer to a hard PS requirement, it composes directly with your Module 12 consensus, and no other team will have it. It's also self-healing — a repaired pothole stops being reported and auto-closes the work order.

### 2.6 ANPR has a hard range limit — so aggregate over the track

OCR needs roughly 20+ px of character height. On 1080p with a normal lens that's a vehicle within ~10–15 m. Firing OCR on every plate-shaped blob wastes compute and produces garbage that pollutes your confidence score.

Gate on the geometry layer (`forward_m < range_limit`), then **vote across the track**:

```
for each frame where the tracked vehicle is in readable range:
    read = ocr(plate_crop)                    # per-character confidences
accumulate per-character confidence-weighted votes across all reads
plate_text = argmax per position
aggregate_confidence = f(char confidences, agreement rate, frames_voted)
```

A 7-frame vote is dramatically more accurate than any single read, and it produces exactly the *"registration number with a confidence score"* the PS asks for — derived, not invented. Store `frames_voted` in the event; it's the number a judge will ask about.

### 2.7 Jetson Nano won't run this

Nano is EOL, 4 GB, ~0.5 TFLOPS — it will not carry two detectors plus tracking plus OCR. In the writeup, name **Jetson Orin Nano class** as the deployment target. In the demo, run on laptops and **report only numbers you measured on the machine you measured them on.** An honest "18 fps on an RTX 3050 laptop, projected to Orin Nano via TensorRT INT8" beats an unverifiable Jetson claim, and BEL evaluators know these boards.

---

## 3. Four PS requirements with no module behind them

Your table lists these under Module 9's description but nothing computes them.

### 3.1 Origin–destination matrix → hashed plate re-identification

O-D normally needs ticketing data you don't have. But a fleet of buses with ANPR is a distributed re-ID network: a plate seen by bus A at point 1 and by bus B at point 2 is one O-D observation of *traffic* flow.

Privacy-preserving by construction — you never need the identity, only the match:

```
plate_token = HMAC-SHA256(normalized_plate_text, daily_rotating_salt)[:16]
```

Irreversible, unlinkable across days (rotating salt bounds long-term tracking), and sufficient for matching. Plaintext plates exist only inside sealed evidence for flagged incidents (§5.2). Two outputs fall out of the same data:

- **O-D matrix** between zones, from token co-occurrence
- **Link travel times** from timestamp deltas on matched tokens — which is a *measured* congestion input, far stronger than inferring congestion from density alone

Ship this with the privacy rationale stated up front. "We built mass plate tracking" and "we built a hashed, salt-rotating, irreversible flow estimator" are the same code and completely different answers in a viva.

### 3.2 Route delay → GPS vs schedule

Bus GPS trace vs a GTFS `stop_times` schedule → per-segment delay, per-route delay distribution, worst-offending segments. Synthesize a small GTFS feed for your city's routes for the demo (`sim/gtfs_synth.py`). Cross-reference delay hotspots against the congestion heatmap — when they coincide, that's your "actionable insight" slide.

### 3.3 Infrastructure deficiency report → inventory + absence

Falls out of §2.5 for free: the inventory table *is* the deficiency report. Group by ward/road, sort by severity.

### 3.4 Severity scoring needs a road-class input

Module 14 wants "road category (arterial vs minor)". Source it from OSM's `highway=*` tag via PostGIS spatial join on the map-matched way:

```
severity = w₁·norm(area_m²) + w₂·norm(repeat_count) + w₃·road_class_weight + w₄·recency
```

Keep the weights in a config file, not in code — a judge will ask "why those numbers", and "they're tunable per municipality, here's the file" is the right answer.

---

## 4. Edge node internals

```
edge/
├── sources/          CameraSource (file|rtsp|dir), GpsSource (csv|nmea|gpsd)
│                     ── the ONLY module that changes for real hardware
├── scheduler/        per-camera fps budget, frame dropping under load
├── perception/       stage1_dyn, stage1_infra, tracker (ByteTrack), stage2_anpr
├── geometry/         calibration, homography/IPM, localization, map-match
├── analyzers/        defect, congestion, pedestrian_risk, driving_incident, signage
├── privacy/          face+plate blur, plate sealing
├── evidence/         crop encoder, ring-buffer clip extractor
├── integrity/        ECDSA signer, hash chain
├── queue/            SQLite store-and-forward (Module 11)
└── uplink/           MQTT QoS1 persistent session, backoff, delta-sync
```

**Ordering rule: `PrivacyFilter` runs before `EvidenceEncoder`.** Blurring must happen before anything touches disk or the wire — if unblurred frames are written to disk first, the audit story collapses and a judge who asks "when exactly do you blur?" will find it.

**Cabin cameras are not processed.** The PS mentions they exist, but every required detection is external. Say this explicitly — it's a free privacy win, not a gap.

**Ring buffer for incident clips.** Keep the last ~15 s of encoded frames in memory per camera. When an incident triggers, you need the seconds *before* it — you cannot start recording after detecting a hit-and-run.

### Store-and-forward (Module 11)

```sql
CREATE TABLE outbox (
  event_id     TEXT PRIMARY KEY,        -- UUID from edge, idempotency key
  seq          INTEGER NOT NULL,        -- per-device monotonic, gap = tamper/loss
  payload      BLOB NOT NULL,
  created_at   INTEGER NOT NULL,
  attempts     INTEGER DEFAULT 0,
  state        TEXT DEFAULT 'pending'   -- pending|inflight|acked
);
```

`event_id` generated at the edge makes ingest idempotent, so retries after a dropped ACK can't duplicate. Flush oldest-first on reconnect, with a size cap and a **priority lane** — a hit-and-run alert must not sit behind 4000 queued potholes. Two queues, or a priority column.

### Bandwidth accounting (Module 13)

Instrument both sides of the chokepoint and print the ratio:

| | Raw | UrbanPulse |
|---|---|---|
| 4× 1080p H.264 @ 4 Mbps, 12 h | ~86 GB/day | — |
| ~500 events × (0.5 KB JSON + 15 KB JPEG crop) | — | ~8 MB/day |
| ~10 incident clips × 5 s @ 1 Mbps | — | ~6 MB/day |
| **Total** | **~86 GB/day** | **~15 MB/day** |

That's ~5700×. Measure your real numbers with a byte counter in `uplink/` — a live counter on the dashboard is worth more than the slide.

---

## 5. Privacy & integrity

### 5.1 Anonymization
Face blur + non-flagged plate blur at the edge, before disk. Log counts per event (`faces_blurred`, `plates_blurred`) so anonymization is auditable rather than asserted. Retention: raw frames never persist beyond the ring buffer; evidence crops expire on a configured TTL unless linked to an open incident.

### 5.2 Selective disclosure via key escrow
Your plan says "unblur if legally flagged" — that requires the plaintext to have survived somewhere, which reopens the privacy hole. Do it properly with envelope encryption:

```
content_key  = random 256-bit
ciphertext   = AES-256-GCM(plate_crop + plate_text, content_key)
wrapped_key  = ECIES-P256(content_key, command_centre_public_key)
```

The edge holds no decryption key. Only the command centre's private key opens it, and every unwrap is logged. This is a real chain-of-custody design, it's ~30 lines with `cryptography`, and for a defence-electronics evaluator it is the most credible thing in your submission.

### 5.3 Tamper-evident event chain
```
payload_hash = SHA256(canonical_json(event_without_integrity_block))
chain_hash   = SHA256(payload_hash || prev_chain_hash)
signature    = ECDSA-P256(chain_hash, device_private_key)
```
Central verifies the signature and that `seq` is gap-free per device. Modified event → hash mismatch. Deleted event → sequence gap. Fabricated event → no valid device signature. Use **canonical** JSON (sorted keys, fixed separators) or verification fails on serialization differences — a subtle bug that will cost you an evening.

---

## 6. Central platform

```
central/
├── ingest/      MQTT subscriber, signature + chain verify, idempotent upsert
├── fusion/      consensus clustering, asset inventory, absence detection, severity
├── analytics/   congestion heatmap, O-D matrix, route delay, link speeds
├── api/         FastAPI — REST + WebSocket for live event push
└── db/          PostGIS models, migrations, OSM road import
```

Schema core:

| Table | Role |
|---|---|
| `events` | raw immutable events, PostGIS `geography(Point,4326)`, GiST index |
| `assets` | fused inventory: type, location, state (`candidate/confirmed/missing/repaired`), confidence, pass/miss counts |
| `incidents` | driving events with sealed evidence refs and disclosure audit log |
| `plate_tokens` | hashed token, zone, timestamp — for O-D and link travel times |
| `roads` | OSM ways with `highway` class, for map-matching and severity |
| `work_orders` | severity-ranked, generated from `assets`, with lifecycle state |

**Fusion is idempotent and re-runnable.** Run it as a scheduled job over a time window, not inline on ingest — you will want to re-run it after tuning `eps` without re-ingesting, especially at 2am during the build.

Dashboard: React + **Leaflet**, not Mapbox — see §7 on offline. Views: live GIS map, congestion heatmap, defect map, work-order queue, incident detail with evidence, route-delay view, bandwidth counter, fleet status.

---

## 7. Two practical traps

**Offline maps.** Mapbox needs a network and a token. Venue Wi-Fi will fail, or the token will rate-limit during judging. Use Leaflet with a locally-seeded tile cache (or a `tileserver-gl` container with a pre-downloaded region extract) so the map renders with the network cable unplugged. Test it unplugged.

**An empty map is not a demo.** Fleet consensus with one bus shows nothing, and a heatmap needs volume. Pre-seed the DB with synthetic fleet history over your city, and run **at least 3–4 simulated buses on overlapping routes** in the live portion so consensus visibly fires during the demo. `sim/fleet_replay.py` orchestrates the edge processes.

---

## 8. Data sources

### Models & datasets

| Target | Dataset | Note |
|---|---|---|
| Road damage | **RDD2022** | ~47k images, vehicle-mounted perspective, **has an India subset**. Exactly your use case — start here. |
| Potholes | Roboflow Universe pothole sets | Merge with RDD2022 for volume |
| Indian road context | **IDD** (Indian Driving Dataset) | Hyderabad, includes autorickshaw; good for calibration footage |
| Traffic signs | Mapillary Traffic Sign Dataset | Global with India coverage |
| Zebra crossings | Mapillary Vistas (`marking--crosswalk-zebra`) | One of few sources with the class labelled |
| Plates | Roboflow Indian plate sets | ~500 images fine-tunes a detector adequately |
| Waterlogging | scarce — build small custom set | Lowest-confidence class; see §9 |
| Vehicles / persons | **COCO-pretrained, no training** | Already covered |

Merging datasets creates *partial labels* (an RDD2022 image has potholes labelled but not signboards, so signboards become false negatives during training). Mitigate by keeping per-source class masks in the loss, or accept it and train `yolo-infra` on the union with the known limitation stated. Don't discover this after training.

### Demo footage
**Go record real footage on a real bus route in your own city.** A phone on a dashboard plus a GPS-logger app for a synchronized trace gets you an authentic multi-kilometre run in an afternoon. Local footage lands far better with judges than YouTube dashcam clips, and it gives you honest calibration data for §2.2. Fall back to `yt-dlp` dashcam footage plus an OSM-route-synthesized GPS trace only if you must.

---

## 9. Descope deliberately

14 modules is more than any team ships well. Choose, and say you chose.

**Nail these** — they carry the demo: road damage detection, vehicle density + congestion heatmap, fleet consensus (12), absence detection (§2.5), GIS dashboard, bandwidth story (13), severity work-orders (14), privacy + integrity (§5).

**Weaken honestly:**
- *Waterlogging* — almost no training data. Keep the class, report lower confidence, be upfront.
- *Missing road dividers* — requires structural continuity reasoning, not object detection. A defensible weak version: detect median/divider presence per frame and flag *gaps* in the continuity along a road segment.
- *Signboard OCR legibility* — nice-to-have. Cut first if time is short.

**Drop and say why:** cabin analytics (not required by any detection; excluding it is a privacy feature).

A team that says "we deprioritized waterlogging because the public data doesn't exist, here's our plan to collect it" reads as more competent than one claiming all 14 work equally. State the tradeoff before a judge finds it.

---

## 10. Repo layout

```
urbanpulse/
├── contracts/          event.schema.json  ← shared source of truth
├── edge/               onboard node (see §4)
├── central/            platform (see §6)
├── dashboard/          React + Leaflet
├── ml/                 dataset prep, training, ONNX export
├── sim/                fleet_replay, gps_synth, gtfs_synth, bandwidth_meter
├── data/               videos, traces, tiles  (gitignored)
├── docs/               ARCHITECTURE.md, BUILD_PLAN.md, demo_script.md
└── docker-compose.yml  one command to start everything
```

One-command startup is not cosmetic. When the demo laptop reboots twenty minutes before judging, `docker compose up` is the difference between presenting and not.
