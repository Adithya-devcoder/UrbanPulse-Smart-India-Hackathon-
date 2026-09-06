# UrbanPulse — How It Works

A ground-up explanation of the problem, the solution, the tech stack, and the complete data flow.
Read this before touching code. It's also your viva prep — every "why did you do it that way?" is answered here.

---

# Part 1 — The problem

## 1.1 What cities do today

A city needs to know three things about its roads, continuously:

1. **What's broken** — potholes, cracks, waterlogging, missing signs, faded crossings
2. **What's congested** — where, when, how badly, and why
3. **What's dangerous** — rash driving, hit-and-run, children crossing unsafely

Today they get this from three sources, and all three fail in the same way:

| Source | Spatial coverage | Temporal coverage | Problem |
|---|---|---|---|
| **Fixed CCTV** | A few hundred points | 24/7 | Sees intersections, not road surface. A city may have 500 cameras across 5,000 km of road — that's 0.01% coverage. Mounted to watch traffic, angled uselessly for tarmac. |
| **Manual inspection** | Whole network, eventually | Once a quarter, maybe | Accurate and expensive. By the time the survey van arrives, the pothole is four months old. |
| **Citizen complaints** | Wherever people complain | Random | Reactive — arrives *after* someone's bike is damaged. Biased: articulate neighbourhoods get repairs, poor ones don't. No severity data, no verification, no photo, no coordinates. |

## 1.2 The real diagnosis

Look at that table again. Every existing source trades spatial coverage against temporal coverage, and none of them wins both.

> **The city's road-intelligence problem is a coverage problem wearing a technology costume.**

Better AI on 500 CCTV cameras still gives you 500 points. The bottleneck was never the algorithm — it's that nothing looks at the other 99.99% of the road, often enough to notice change.

## 1.3 Why buses are the answer

Public transport buses have a coverage profile that is the exact **inverse** of CCTV, and it's the profile you actually need:

- **They cover the network.** Bus routes are designed to reach everywhere people live and work. Between them, a city fleet traverses nearly every arterial and collector road in the city.
- **They repeat.** This is the crucial property, and the one most teams miss. A bus doesn't pass a given stretch of road once — it passes it 20, 40, 60 times a day, and again tomorrow. Same road, same camera angle, over and over.
- **They already have the hardware.** Modern buses already carry front/rear/side/cabin cameras and GPS. That investment is sunk. The cameras are used as dumb recorders — footage pulled only after an accident, to settle an insurance claim.
- **They're already connected and tracked.** Most transit fleets already run GPS/AVL for passenger ETA systems.

So the sensor network is **already deployed, already moving, already powered, already connected — and nobody is reading it.**

## 1.4 Why repetition is the whole game

This deserves its own section, because it's the intellectual core of the project.

A single dashcam frame from a moving bus is a *bad* sensor reading. Shadows look like potholes. Wet tar patches look like potholes. Manhole covers look like potholes. Any detector you train will produce false positives on Indian roads — that's not a skill issue, it's the data.

Now add repetition:

- Bus 12 reports a pothole at a location at 08:14
- Bus 7 reports one within 15 m at 09:02
- Bus 12 again at 11:40, bus 31 at 14:20

Four independent observations, different times, different lighting, different vehicles, different angles. That is no longer a guess — it's a measurement. Meanwhile the shadow that fooled bus 12 once at 08:14 never gets a second vote and dies as a low-confidence candidate.

> **Repetition converts a mediocre detector into a reliable data source.** And repetition is available *only* because buses run fixed routes.

It also buys you something nothing else can do: **change detection**. If a sign was seen on 40 previous passes and isn't seen on the next 5 clean passes, the sign is *gone*. If a pothole reported for three weeks stops being reported, it was *repaired*. Absence, appearance, and repair all become observable — but only against a baseline that repetition builds.

Everything else in UrbanPulse is engineering. This is the idea.

## 1.5 Why processing must happen on the bus

The obvious architecture — stream all video to a server, run AI there — is not merely inefficient. It is impossible. Here's the arithmetic:

```
4 cameras × 1080p H.264 @ 4 Mbps  = 16 Mbps  per bus, continuously
                    × 1,000 buses = 16 Gbps  sustained, over cellular
                                  ≈ 86 GB per bus per 12-hour day
```

Sixteen gigabits per second of mobile uplink is unaffordable at any realistic transit budget. And even if you paid for it:

- **Mobile networks drop.** Tunnels, flyover underpasses, urban canyons, rural route ends. A streaming architecture loses data exactly where coverage is worst — which correlates with where infrastructure is worst.
- **Privacy collapses.** You've just shipped every face and every licence plate in the city to a central server, continuously, with no legal basis.

So: **do the seeing on the bus, and transmit the meaning instead of the pixels.**

```
Raw video:     ~86 GB per bus per day
UrbanPulse:    ~15 MB per bus per day       (~5,700× reduction)
```

Edge AI here is not a buzzword to satisfy a checklist. It is the arithmetic that makes fleet-scale deployment possible at all. This is why the problem statement says *"minimizing bandwidth through intelligent edge processing"* — it's the load-bearing requirement.

---

# Part 2 — The solution

## 2.1 In three sentences

1. Each bus becomes a sensor that **understands** what it sees and emits small structured facts instead of video.
2. The central platform aggregates facts from the whole fleet and uses **route repetition** to turn noisy single observations into confident, verified, prioritised city-scale knowledge.
3. That knowledge is served as a live GIS map and a **ranked action queue**, so authorities act on measured evidence instead of complaints.

## 2.2 The division of labour

The system has two halves, and the boundary between them is conceptual, not just physical:

| | Edge (one per bus) | Central (one for the fleet) |
|---|---|---|
| **Question it answers** | *What did I just see, and where?* | *What is actually true, and what matters most?* |
| **Scope** | One vehicle, one moment | Whole fleet, all time |
| **Output** | Individual observations | Verified assets, rankings, analytics |

A single bus fundamentally **cannot** know whether a pothole is real (it might be a shadow) or whether it's important (it might be on a dead-end service lane). Truth needs corroboration; priority needs city context. Both require the fleet. That's why the split falls exactly there.

```
EDGE:     perceive → measure → localise → protect → package → buffer → transmit
CENTRAL:  verify → store → fuse → analyse → present
```

## 2.3 System topology

```
┌────────────────── BUS EDGE NODE (one process per bus) ───────────────────┐
│                                                                          │
│  CameraSource ──► FrameScheduler ──► Stage-1 ──► Geometry ──► Analyzers   │
│  GpsSource          (per-camera     ├ yolo-dyn   (IPM,        (5 rule     │
│  (file | rtsp)       fps budget)    └ yolo-infra  localise)    engines)   │
│                                          │                          │     │
│                                   Stage-2 on trigger                │     │
│                                   plate → OCR → vote                │     │
│                                                                     ▼     │
│  PrivacyFilter ─► EvidenceEncoder ─► IntegritySigner ─► SQLite ─► Uplink  │
│                                                         outbox       │    │
└──────────────────────────────────────────────────────────────────────│────┘
                                                     MQTT QoS1 over TLS │
                                                        ~15 MB/day/bus  │
┌───────────────────── CENTRAL PLATFORM ────────────────────────────────▼───┐
│  IngestGateway — authN, signature + hash-chain verify, idempotent upsert  │
│        ▼                                                                  │
│  PostGIS ──► FusionEngine ──────► AnalyticsEngine ──► FastAPI ──► React   │
│  event       consensus clustering  congestion heatmap            Leaflet  │
│  store       asset inventory       O-D matrix (hashed)                    │
│              absence detection     route delay vs GTFS                    │
│              severity scoring      work-order queue                       │
└───────────────────────────────────────────────────────────────────────────┘
```

## 2.4 Our software-only adaptation

We have no bus and no Jetson. So the edge node reads from a **recorded video file plus a synchronised GPS trace** instead of live cameras and a GNSS receiver.

Critically, this is confined to exactly one module — `sources/`. Everything downstream is bit-identical to a real deployment:

```python
class CameraSource(ABC):
    def frames(self) -> Iterator[Frame]: ...

class FileCameraSource(CameraSource):   # what we demo with
class RtspCameraSource(CameraSource):   # what a real bus uses
```

The edge node still runs as its own process, on its own machine, talking to central over a real MQTT broker through a metered link. **We simulate the sensors. We never simulate the architecture.** A real bus could join the fleet tomorrow by swapping one class.

---

# Part 3 — Tech stack, and why each piece

## 3.1 Edge node

| Concern | Technology | Why this one |
|---|---|---|
| Video decode, preprocessing, ring buffer | **OpenCV** | Frame I/O, resize, colour conversion, JPEG encode — all in one library |
| Inference runtime | **OpenCV `cv2.dnn`** on ONNX | Runs YOLO ONNX weights directly, so OpenCV genuinely *is* our CV runtime — no separate inference dependency on the edge |
| Dynamic-object detection | **YOLOv8n, COCO-pretrained** | car / bus / truck / motorcycle / bicycle / person already included — **zero training required** |
| Infrastructure detection | **YOLOv8s, custom-trained** | pothole / crack / waterlogging / signboard / zebra / divider — the only model we must train |
| Multi-object tracking | **ByteTrack** | Persistent IDs without a re-ID network; cheap enough for edge, and needed so we count each vehicle once |
| Road-plane geometry | **OpenCV `getPerspectiveTransform` / `perspectiveTransform`** | Inverse perspective mapping — pixels to metres (see §4.3) |
| Ego-motion estimation | **GPS velocity + `cv2.calcOpticalFlowPyrLK`** | Two independent estimates of the bus's own motion, cross-validated |
| Plate OCR | **PaddleOCR** (fallback EasyOCR) | Exposes **per-character confidences**, which our voting scheme requires |
| Durable local buffer | **SQLite** | Embedded, zero-config, ACID — a real queue that survives a power cut |
| Cryptography | **`cryptography`** — ECDSA P-256, AES-256-GCM | Event signing plus envelope encryption for sealed evidence |
| Uplink | **MQTT (Mosquitto)**, QoS 1, TLS | Persistent sessions survive disconnects; pub/sub is the natural fit for many-buses-to-one-centre fan-in |
| Model optimisation | **ONNX → INT8 quantisation** (TensorRT on real hardware) | 3–4× speedup for ~1–2% accuracy loss |

## 3.2 Central platform

| Concern | Technology | Why this one |
|---|---|---|
| API server | **FastAPI** | Async (needed for MQTT ingest + HTTP together), native WebSocket for live push, auto-generated OpenAPI docs |
| Database | **PostgreSQL + PostGIS** | Spatial indexes (GiST), `ST_DWithin` radius queries, road-network joins. A plain DB cannot answer "all defects within 15 m of this point" efficiently |
| Consensus clustering | **scikit-learn DBSCAN** | Density-based, needs no preset cluster count — correct choice when you don't know how many potholes exist |
| Road network & priors | **OpenStreetMap + osm2pgsql** | Free road classification (`highway=primary/residential`) for severity weighting, plus existing `highway=crossing` nodes as absence-detection priors |
| Schedule baseline | **GTFS** (synthetic for demo) | Standard transit format; `stop_times` gives the expected timings that route delay is measured against |
| Frontend | **React + Leaflet + leaflet.heat** | Leaflet works with locally-cached tiles — **Mapbox needs network and a token, which will fail at a demo venue** |
| Orchestration | **Docker Compose** | One command, cold start, reproducible |
| Fleet simulation | Custom Python harness | Runs 3–4 virtual buses on overlapping routes so consensus visibly fires |

## 3.3 The contract between them

`contracts/event.schema.json` is a JSON Schema validated by **both** sides — edge on write, central on ingest. Not documentation; an executable contract. It's what prevents the classic failure where the frontend expects `lat` and the backend sends `latitude`, discovered at 3 a.m.

---

# Part 4 — The full working: one pothole, end to end

This is the core of the system. Follow one pothole from photons to a municipal work order.

## Stage 0 — Input

Two time-synchronised streams:

- **Video frames** — 1080p, timestamped
- **GPS fixes** — lat, lon, speed, heading, ~1 Hz

Synchronisation is not a detail. A frame captured between two GPS fixes must be paired with an *interpolated* position — at 11 m/s, being one fix out means being 11 m wrong.

## Stage 1 — Frame scheduling

We cannot run AI on every frame of every camera. The scheduler allocates a budget:

| Camera | Model | Rate | Reasoning |
|---|---|---|---|
| Front | `yolo-dyn` | 10 fps | Tracking needs continuity — gaps break track IDs |
| Front | `yolo-infra` | 3 fps | Potholes don't move. At 11 m/s a pothole is visible ~2 s → ~6 chances to see it |
| Left / Right | `yolo-infra` | 2 fps | Signs and kerbside infrastructure are static; multiple daily passes cover the rest |
| Rear | `yolo-dyn` | 5 fps, on demand | Only during incident tracking |
| **Cabin** | **none** | **never** | No required detection needs it. Excluding it is a privacy feature, not a gap |

**The frame-rate split *is* the compute budget.** Getting this right is what lets two models co-run where seven could not.

## Stage 2 — Detection

`yolo-infra` runs on the frame and returns:

```
class="pothole"  confidence=0.87  bbox=[812, 640, 96, 74]  frame=[1920, 1080]
```

Note what we have: *"something pothole-shaped occupies these pixels."* That is nearly useless. Pixels are not a place, and pixel area is not a size.

## Stage 3 — Geometry: from pixels to metres

**This is the transformation that turns a detection into a measurement, and it is the highest-leverage component in the entire system.**

The camera sits at a fixed height with a fixed pitch, looking at a road that is locally flat. Under those conditions there is a fixed projective relationship — a **homography** — between the image plane and the road plane. Calibrate it once per camera using four known correspondences (standard lane width is 3.5 m, which is enough of a ruler):

```python
H = cv2.getPerspectiveTransform(image_quad, road_plane_quad)   # once, at calibration
```

Then take the **bottom edge** of the bounding box — where the object meets the ground — and push it through `H`:

```
pixel (860, 714)  ──H──►  (lateral = −1.2 m, forward = 14.3 m)
```

Intuitively, this un-warps the camera's perspective view into a **top-down bird's-eye map** of the road ahead. Map all four bbox corners and you get the pothole's real footprint: **0.42 m²**.

Why this matters so much — pixel area is a lie:

> A 0.4 m² pothole 5 m away and the same pothole 40 m away differ by roughly **64×** in bounding-box area. Ranking severity by bbox area doesn't just add noise, it *inverts* the ordering: a big distant hazard scores below a small nearby one.

One homography unlocks six modules:

| Module | Without geometry | With geometry |
|---|---|---|
| Road defects | pixel blob | **area in m²** |
| Vehicle density | count per frame (meaningless across speeds) | **vehicles per 100 m of lane** |
| Congestion | guesswork | measured ground speed |
| Rash driving | image-space motion | **ground-frame velocity** (§5) |
| ANPR | fire OCR and hope | fire only inside readable range |
| Fleet consensus | clusters on bus position | clusters on **defect position** |

## Stage 4 — Localisation: where is it on Earth?

GPS reports where the *bus* is. The pothole is 14.3 m ahead and 1.2 m left. So rotate the offset into world coordinates by the bus's heading and add:

```
pothole_position = bus_position + R(heading) · (lateral, forward)
pothole_position = snap_to_road_centreline(pothole_position)    # OSM map-match
```

Skip this and every defect is tagged **15–40 m** from its true location — the bus's own position plus a GPS fix that's up to a second stale. That error exceeds the ~15 m radius consensus clustering needs, so clusters either never form or wrongly merge two adjacent potholes.

Map-matching also attaches the OSM `way_id`, which hands us the road's classification for free — the arterial-vs-residential input that severity scoring needs later.

## Stage 5 — Analyzer: detections into an event

The same physical pothole appears in ~6 consecutive frames at decreasing `forward_m`. The defect analyzer deduplicates by road-plane position and emits **one event per physical defect**, carrying the best-confidence observation and the measured area.

## Stage 6 — Privacy filter

Before anything touches disk or network: detect faces and licence plates in the evidence crop and blur them. Record the counts (`faces_blurred: 3, plates_blurred: 2`) in the event so anonymisation is **auditable rather than asserted**.

**Ordering is load-bearing.** Blur must happen *before* persist. If unblurred frames hit the disk first, the privacy claim is theatre, and it's the first thing a sharp evaluator will probe.

## Stage 7 — Evidence packaging

Crop the pothole region, JPEG-encode: **~15 KB**. Not the frame. Not the video. A SHA-256 of the crop goes into the event, so the image cannot be swapped afterwards.

## Stage 8 — Integrity sealing

```
payload_hash = SHA256(canonical_json(event))
chain_hash   = SHA256(payload_hash ‖ prev_chain_hash)
signature    = ECDSA-P256(chain_hash, device_private_key)
seq          = monotonic per-device counter
```

Three tamper properties, from three cheap primitives:

| Attack | Detected by |
|---|---|
| Modify an event | hash mismatch |
| Delete an event | gap in `seq` |
| Fabricate an event | invalid device signature |

That's chain of custody — and for a defence-electronics evaluator, it's probably the most credible thing in the submission. (Use *canonical* JSON — sorted keys, fixed separators — or verification fails on harmless serialisation differences.)

## Stage 9 — Store-and-forward buffer

Write to a local SQLite outbox keyed by `event_id`. If the bus is in a tunnel, the event simply waits. Nothing is lost.

On reconnect, drain oldest-first — **except** that incidents ride a priority lane. A hit-and-run alert must not queue behind 4,000 potholes.

## Stage 10 — Uplink

MQTT QoS 1 over TLS. QoS 1 is at-least-once, so duplicates are possible — harmless, because `event_id` is generated at the edge and makes ingest idempotent.

On the wire: **~0.5 KB JSON + ~15 KB JPEG**, versus 16 Mbps of raw video.

---

### ─────  the network boundary  ─────

---

## Stage 11 — Ingest and verification

Central verifies the ECDSA signature against the registered device key, checks hash-chain linkage and `seq` continuity, then **upserts by `event_id`** so retries are safe. Failures go to a quarantine table — never silently dropped, because silent drops are indistinguishable from an attack.

## Stage 12 — Fusion: where truth is manufactured

This is the intelligence no single bus can have.

**Consensus clustering (fleet validation).** Project all defect events to UTM metres, run DBSCAN with `eps ≈ 15 m`:

```
bus 12 @ 08:14 ┐
bus 7  @ 09:02 ├──► one asset, 4 independent confirmations, confidence 0.94
bus 12 @ 11:40 │
bus 31 @ 14:20 ┘

bus 4  @ 07:31 ────► 1 observation, no corroboration, confidence 0.31 → stays candidate
```

The morning shadow that fooled bus 4 never gets a second vote. **This is how you get high precision out of a mediocre detector** — and it's the single most important thing to be able to explain.

Two clustering traps, both easy to hit:
- Don't cluster raw lat/lon with a Euclidean metric — a degree of longitude at 13°N is ~108 km, latitude ~111 km. Project to UTM, or use `metric="haversine"` with `eps` in radians.
- Don't add timestamp as a third dimension. Seconds and metres share no scale, so the distance function becomes meaningless. Cluster in **space only**; time is the axis along which confidence accumulates.

**Asset inventory.** Each cluster becomes a row with a lifecycle:

```
candidate ──(k confirmations)──► confirmed ──(N clean misses)──► repaired
                                     │
                                     └──(N clean misses, sign/marking)──► missing
```

This inventory **is** the city's road-asset database — built by the fleet, at no survey cost, something the municipality has never had.

**Absence detection.** A detector reports what it *sees*; absence is not a detection. A frame with no signboard is indistinguishable from a frame where a truck blocked the view. So we count, per confirmed asset, the passes where a bus went by **with good visibility** and failed to see it:

```
visibility_ok(pass) = daylight
                    ∧ no large occluding bbox over the expected region
                    ∧ bus in the correct lane
                    ∧ speed below motion-blur threshold

if consecutive_clean_misses ≥ N:   →  missing / repaired
```

This is the only honest way to answer the PS's demand for *missing* dividers, *missing* zebra crossings, *missing* signboards. It also auto-closes work orders when a pothole stops being reported — the system notices repairs without anyone telling it.

**Severity scoring.**

```
severity = w₁·norm(area_m²) + w₂·norm(repeat_count) + w₃·road_class_weight + w₄·recency
```

Weights live in a config file, not in code. When a judge asks "why those numbers?", the answer is "they're tunable per municipality — here's the file."

Sort by severity → a **prioritised work queue**, not a flat scatter of dots. That's the difference between data and a decision.

## Stage 13 — Analytics

| Output | How it's computed |
|---|---|
| **Congestion heatmap** | Aggregate density-per-100 m and mean ground speed over space×time cells |
| **O-D matrix + link travel times** | Hashed plate tokens matched across buses (§6) |
| **Route delay** | Bus GPS trace vs GTFS `stop_times` → per-segment delay distribution |
| **Deficiency report** | Asset inventory grouped by ward / road, sorted by severity |

The insight worth putting on a slide: overlay route-delay hotspots on the congestion heatmap. Where they coincide, you've located a bottleneck that is *measurably* costing the transit system time — a maintenance argument with a number attached.

## Stage 14 — Presentation

FastAPI serves REST plus a WebSocket for live push. React + Leaflet renders: live GIS map, congestion heatmap, defect map, severity-ranked work queue, incident detail with evidence, route-delay view, and a live bandwidth-reduction counter.

---

# Part 5 — Second walkthrough: a hit-and-run

Worth tracing separately, because it exercises completely different machinery.

**1. Detect and track.** `yolo-dyn` finds vehicles; ByteTrack assigns persistent IDs across frames.

**2. Measure in metres.** Geometry converts each track's position to road-plane coordinates every frame.

**3. Compensate for our own motion.** ← *the step everyone forgets*

The camera is on a moving bus. When the bus brakes, **every** vehicle in frame appears to accelerate toward it. Image-space "sudden acceleration" thresholds fire constantly on the bus's own behaviour, and the module becomes pure noise.

```
v_relative = d/dt[ road_plane_position(target) ]
v_ground   = v_relative + v_bus            ← from GPS speed + heading
```

Now we know how the *other* vehicle is actually moving over the ground, independent of what our bus is doing. Optical flow on static background features cross-validates the GPS estimate and covers GPS dropout.

**4. Detect the anomaly.** Threshold on ground-frame quantities that mean something: longitudinal acceleration, jerk, lateral weaving amplitude, time-headway to the vehicle ahead.

**5. Trigger cascade.** One detection sets off four things at once:

- **Ring buffer dump.** The last ~15 s of encoded frames is already held in memory, so we recover the seconds *before* the incident. You cannot get those by starting to record after detecting a hit-and-run — which is exactly why a dashcam is useless for this and we aren't one.
- **Stage-2 ANPR**, on that track only, and only in frames where `forward_m` is inside readable range.
- **Evidence sealing** (§6).
- **Priority uplink** — jumps the outbox queue.

**6. ANPR by multi-frame voting.**

OCR needs roughly 20 px of character height — about 10–15 m at 1080p. So gate on range first, then vote:

```
for each frame where the track is in readable range:
    read = ocr(plate_crop)                → per-character confidences
accumulate confidence-weighted votes per character position
plate_text            = argmax per position
aggregate_confidence  = f(char confidences, agreement rate, frames_voted)
```

A 7-frame vote is dramatically more accurate than any single read — and it **derives** the confidence score the PS demands, rather than inventing one. Store `frames_voted` in the event; it's the number an evaluator will ask for.

---

# Part 6 — Privacy and security by construction

Bus cameras see faces, innocent vehicles' plates, and (in a real deployment) passengers including children. A judge *will* ask. The answer has to be implemented behaviour, not intent.

## 6.1 Anonymise at the edge, before persist
Faces and non-flagged plates blurred before any disk write or transmission. Counts logged per event. Cabin feed never processed at all.

## 6.2 Sealed evidence with key escrow

"Blur everything, but un-blur if legally flagged" quietly requires the plaintext to have survived somewhere — which reopens the hole it claimed to close. Envelope encryption closes it properly:

```
content_key = random 256-bit
ciphertext  = AES-256-GCM(plate_crop ‖ plate_text, content_key)
wrapped_key = ECIES-P256(content_key, command_centre_public_key)
```

**The edge holds no decryption key — it cannot read back its own evidence.** Only the command centre's private key opens the envelope, and every unwrap is logged with who and when. That's lawful selective disclosure, about 30 lines of code.

## 6.3 Privacy-preserving O-D analysis

O-D patterns normally need ticketing data we don't have. But a fleet doing ANPR is a distributed re-identification network — which is also a mass-surveillance system if built carelessly. So we never keep the identity, only the match:

```
plate_token = HMAC-SHA256(normalised_plate, daily_rotating_salt)[:16]
```

Irreversible (no plate stored), and unlinkable across days (the rotating salt bounds long-term tracking). Sufficient for exactly what we need:

```
bus A sees token X in zone 1 @ 08:10
bus B sees token X in zone 4 @ 08:35
   → one O-D flow observation, and a measured 25-min corridor travel time
```

Two outputs from one mechanism: the O-D matrix, and **measured** link travel times — a far stronger congestion signal than density alone.

Same code, two framings. *"We track every vehicle across the city"* and *"we compute irreversible, salt-rotating, non-identifying flow statistics"* are the same implementation and completely different answers in a viva. Lead with the second, and mean it.

---

# Part 7 — Why this beats the obvious design

| | Naive approach | UrbanPulse |
|---|---|---|
| Where AI runs | Cloud, on streamed video | On the bus |
| Bandwidth per bus | ~86 GB/day | ~15 MB/day |
| Network dropout | Data lost | Buffered, replayed on reconnect |
| Detection unit | Per-frame dots on a map | Fused assets with lifecycle state |
| Truth model | One pass = one fact | Multi-bus consensus |
| False positives | Every shadow is a pothole | Uncorroborated observations die as candidates |
| "Missing" assets | Impossible | Absence detection against a fleet-built baseline |
| Repairs | Manual close-out | Auto-detected when reports stop |
| Severity | Pixel area (scale-dependent, inverts ordering) | m² × repeats × road class |
| Privacy | All faces/plates shipped to cloud | Blurred at edge; evidence sealed under authority key |
| Evidence | A video file | Signed, hash-chained, tamper-evident |
| Output | A map of dots | A ranked work queue |

---

# Part 8 — What a judge should see

Five moments, in this order:

1. **It works.** Video plays with detection overlays; dots appear on the map at the right places, with areas in m².
2. **It survives.** Unplug the network mid-run. Detection continues. Plug back in. The queue drains. Nothing lost. *(Thirty seconds, and the most convincing thing in the demo.)*
3. **It gets smarter with the fleet.** Three buses pass the same pothole; watch confidence climb 0.4 → 0.94 and the asset flip to `CONFIRMED`.
4. **It handles incidents properly.** Staged clip: plate read with `aggregate_confidence` and `frames_voted`, evidence sealed, alert raised at the centre, decryption logged.
5. **It's deployable.** The live bandwidth counter: 86 GB/day raw vs 15 MB/day transmitted.

Then the one-line close: **every bus already drives these roads every day — we just started reading what they see.**
