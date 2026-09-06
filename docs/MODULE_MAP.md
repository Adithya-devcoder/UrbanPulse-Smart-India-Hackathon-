# UrbanPulse — Module Map & Reconciliation

Maps your 13-module plan onto architecture components, and flags status per module.
Use this as the single reconciliation point between your module list and `ARCHITECTURE.md`.

**Legend:** ✅ covered · ⚠️ needs an addition to work · ❌ PS requirement with no module behind it

---

## 1. Module → component map

| # | Your module | Architecture component | Status |
|---|---|---|---|
| 1 | Road defect detection | `perception/stage1_infra` + `geometry` + `analyzers/defect` | ⚠️ S/M/L needs distance normalisation (§3) |
| 2 | Signboard condition | `stage1_infra` + `fusion/inventory` + OSM priors | ⚠️ reference DB must be fleet-built (§4) |
| 3 | Vehicle density & classification | `stage1_dyn` (COCO) + `tracker` (ByteTrack) | ✅ no training needed |
| 4 | Traffic bottleneck | `analyzers/congestion` + **ego GPS speed** | ⚠️ speed estimation under-specified (§5) |
| 5 | Vulnerable pedestrian | `stage1_dyn` + `analyzers/pedestrian_risk` | ✅ |
| 6 | Rash driving & incidents | `analyzers/driving_incident` + **ego-motion compensation** | ⚠️ will not work without §6 |
| 7 | ANPR & offender tracking | `perception/stage2_anpr` + multi-frame voting | ✅ |
| 8 | Edge-AI processing | `edge/` whole node + `sources/` abstraction | ⚠️ bandwidth metric must be measured (§7) |
| 9 | Centralised GIS | `central/api` + `db` + `dashboard` | ✅ |
| 10 | Central alerting & priority | `central/alerting` — **new component** | ⚠️ needs dedupe + SLA state (§8) |
| 11 | Privacy-preserving processing | `privacy/` filter, pre-persist | ✅ |
| 12 | **Adaptive vision layer** | `perception/quality` — **new, see §2** | ⚠️ train/test mismatch risk |
| 13 | Fleet-consensus incident reconstruction | `fusion/consensus` + `fusion/incident_link` | ⚠️ co-witnessing is rare (§9) |
| — | Comms & offline-first | `queue/` + `uplink/` | ✅ |
| — | **O-D patterns** | — | ❌ PS-mandated, no module |
| — | **Route delay estimation** | — | ❌ PS-mandated, no module |
| — | **Severity ranking / work queue** | — | ❌ dropped from previous list |
| — | **Evidence integrity** | `integrity/` | ❌ TLS ≠ tamper-evidence |

---

## 2. Module 12 — Adaptive Vision Layer, done correctly

Good instinct. Indian conditions genuinely need it — monsoon, fog, night, glare. But the obvious implementation *reduces* accuracy.

### The trap

Your detector was trained on ordinary images. If you apply CLAHE at inference, you feed it a pixel distribution it has never seen. That's a **train/test distribution mismatch**, and it commonly costs more mAP than the poor visibility did. Enhancement makes images look better *to humans*; CNNs do not share our preferences.

### The correct strategy — two layers, in this priority

**Primary: fix it at training time (zero inference cost).** Train with heavy photometric augmentation so the model is natively robust:

```python
A.Compose([
    A.RandomRain(p=0.15), A.RandomFog(p=0.15),
    A.RandomBrightnessContrast(p=0.4), A.RandomGamma(p=0.3),
    A.MotionBlur(blur_limit=7, p=0.2), A.ISONoise(p=0.2),
])
```

This is strictly better than test-time enhancement: it costs nothing per frame, and the model learns the invariance instead of you hand-engineering it.

**Secondary: adaptive enhancement as a fallback for extreme frames only.**

### Pipeline insertion point

```
FrameScheduler ──► QualityAssessor ──► [conditional enhance] ──► Stage-1 detection
                        │
                        └──► quality_score ──────────────────────► event.frame_quality
```

Assess on a **downscaled frame** (160×90) so it's nearly free:

| Condition | Cheap metric | Response | Cost |
|---|---|---|---|
| Low light | mean luminance | gamma correction (LUT) | negligible |
| Low contrast | RMS contrast | CLAHE (tile-based) | cheap |
| Haze / fog | dark-channel transmission estimate | dehaze — **expensive**, gate at ≤1 fps or skip in favour of augmentation | high |
| Motion blur | Laplacian variance | **do not enhance — lower confidence or drop the frame** | negligible |

That last row is the one to internalise: **motion blur is unrecoverable.** Sharpening blurred frames manufactures edges and *creates* false pothole detections. The correct response to a bad frame is to trust it less, not to prettify it.

### The elegant payoff: quality-weighted consensus

Let `quality_score` ride along in the event and flow into fusion:

```
event_weight = detection_confidence × frame_quality
asset_confidence = Σ(event_weight) over corroborating observations
```

A detection from a rain-streaked, low-light frame contributes less to consensus than one from a clean daylight frame. This connects Module 12 to Module 13 with one multiplication, and it's the kind of detail that reads as engineering maturity rather than feature-listing.

### Non-negotiable: measure it

Build a small validation set of genuinely degraded frames (night, rain, fog) and report **mAP with vs without** the adaptive layer, per condition. If it doesn't improve mAP, it's decoration — cut it and say the augmentation strategy covers it. Never ship an enhancement you haven't measured.

---

## 3. Module 1 — "Small/Medium/Large" needs distance normalisation

Raw bounding-box area is scale-dependent: the *same* pothole reads Large at 5 m and Small at 40 m. The word "visible" in your spec is honest hedging, but the classification will still be wrong often enough to undermine the map.

**Full fix:** the IPM/homography geometry layer → area in m² (`ARCHITECTURE.md` §2.2).

**Cheap fix, ~20 lines, if you don't want full calibration:** for objects on the ground plane, distance is a monotonic function of the bbox's bottom row in the image. Calibrate a 1-D curve (place objects at 5/10/20/30 m, record bottom rows) and normalise:

```
distance      ≈ f(bbox_bottom_row)          # 1-D lookup / fitted curve
area_normed   = bbox_area × distance²        # cancels the 1/d² scaling
S / M / L     = threshold(area_normed)
```

This is a poor man's IPM. It gets you defensible S/M/L without a 4-point calibration, and you can upgrade to the full homography later without changing the analyzer's interface.

---

## 4. Module 2 — where does the reference map come from?

Your spec says *"a reference map/database is used to identify expected signs that may be missing."* The unanswered question is where that database comes from — municipalities generally don't have a sign inventory, which is part of why the problem exists.

Two sources, combined:

1. **OSM priors** — OpenStreetMap already carries `highway=crossing`, `traffic_signals`, and often `traffic_sign` nodes. Free seed data.
2. **Fleet-built inventory** — every confirmed detection registers an asset; after *k* independent confirmations it becomes `CONFIRMED` and joins the baseline.

Then absence is a state transition, gated on visibility (`ARCHITECTURE.md` §2.5) so a truck occlusion doesn't count as a miss. Say this explicitly in your writeup — "we build the reference map ourselves from fleet observations" is a much stronger answer than assuming one exists.

---

## 5. Module 4 — your best congestion sensor isn't a camera

Your spec lists "speed estimation" without saying whose speed or how. Vision-based speed from a moving platform is noisy and hard.

**The bus's own GPS speed is an exact, free congestion measurement.** If the bus is crawling, traffic is congested — no CV required, no error, already in your data stream.

```
congestion = f( ego_speed_profile,          ← GPS, exact and free
                vehicle_density_per_100m,   ← CV
                dwell_time_below_threshold ) ← GPS
```

Use ego speed as the primary signal and CV density as the corroborating one. Most teams reach for the camera and miss that the vehicle is already instrumented — this is both simpler and more accurate than what you had planned.

---

## 6. Module 6 — the missing step that decides whether it works

Your spec says "Trajectory/Motion Analysis" with no mention of compensating for the bus's own motion. This is the single most likely module to silently fail in your demo.

When the bus brakes, **every** vehicle in frame appears to accelerate toward it. Image-space thresholds for "sudden braking" and "swerving" will fire on the bus's own behaviour continuously.

```
v_relative = d/dt[ road_plane_position(target) ]
v_ground   = v_relative + v_bus              ← GPS speed + heading
```

Threshold on ground-frame accel / jerk / weaving / time-headway. Cross-validate ego-motion with sparse optical flow on static background. Without this step, Module 6 produces noise — and note it depends on the geometry layer, which is another reason to build that early.

---

## 7. Module 8 — you dropped the number, keep the number

Your previous list had a dedicated bandwidth-optimisation module with an explicit before/after comparison. Now it's folded into Module 8 as the qualitative *"raw video is not continuously uploaded."*

That's a regression. The PS says **"minimizing bandwidth through intelligent edge processing"** — it wants the reduction demonstrated, and a measured ratio is your single most persuasive proof point:

| | Raw | UrbanPulse |
|---|---|---|
| 4× 1080p @ 4 Mbps, 12 h | ~86 GB/day | — |
| ~500 events × (0.5 KB JSON + 15 KB crop) | — | ~8 MB/day |
| ~10 incident clips × 5 s | — | ~6 MB/day |
| **Total** | **~86 GB/day** | **~15 MB/day** (~5,700×) |

Put a byte counter in `uplink/` and a live reduction figure on the dashboard. A running counter beats any slide.

---

## 8. Module 10 — alert routing needs dedupe and lifecycle

Good addition; the failure mode is **alert fatigue**. Without these three things, a municipal officer gets paged about the same pothole every single day until they mute the system:

- **Deduplication** — route on the fused *asset*, never on raw events. One asset → one alert, updated in place.
- **Immediate vs digest** — incidents page instantly; defects arrive as a daily prioritised digest. Different channels, different urgency.
- **Lifecycle state** — `raised → acknowledged → in_progress → resolved`, with the auto-close hook from absence detection (§4) closing work orders when a defect stops being reported.

Plus **severity ranking**, which vanished from your list (previously module 14). Module 10's "priority" needs an actual score to sort by:

```
severity = w₁·norm(size) + w₂·norm(repeat_count) + w₃·road_class + w₄·recency
```

Weights in a config file. Sorted output = a work queue, not a scatter of dots. This is what "actionable insights for transport authorities" means in the PS.

---

## 9. Module 13 — co-witnessing is rarer than you think

Incident reconstruction from multiple buses is genuinely impressive, but check the base rate: two buses being at the same place within a ~30 s window requires dense route overlap. On a trunk corridor with 5-minute headways it happens; on most of the network it won't. If you demo this on a normal route, nothing will correlate.

**Two things to do:**

1. **Be explicit about the domain** — "on trunk corridors with headways under ~6 minutes, corroboration probability is high." Stating the condition is stronger than implying it works everywhere. For the demo, stage two buses on one corridor.

2. **Add the variant that doesn't need simultaneity** — link by plate across *time*:

```
bus A @ 08:10, MG Road    → token X, rash driving
bus B @ 08:22, Ring Road  → token X, rash driving
bus D @ 08:41, Airport Rd → token X, rash driving
   → repeat-offender trajectory across the city, 3 independent witnesses
```

Far more likely than co-witnessing, and arguably more valuable: *"this vehicle drove dangerously at four locations across the city this morning"* is a stronger enforcement artifact than one corroborated event. Same machinery, higher hit rate.

**Also keep consensus for defects.** Your Module 1 now says "multi-frame confirmation" — that's within a single bus, so it can't catch a shadow that fools that bus consistently. Cross-fleet defect consensus is what makes the pothole map trustworthy, it runs constantly (unlike incidents, which are rare), and it reuses the exact same DBSCAN code. Nearly free; don't lose it.

---

## 10. Two PS requirements with no module at all

Both are named explicitly in the problem statement and both vanished from this revision.

**Origin–destination patterns.** Solve with hashed plate tokens — no identities stored:

```
plate_token = HMAC-SHA256(normalised_plate, daily_rotating_salt)[:16]
```

Irreversible, unlinkable across days. Token co-occurrence across buses yields the O-D matrix *and* measured link travel times — which is a stronger congestion input than density alone. Reuses Module 7's output and Module 13's matching logic.

**Route delay estimation.** Bus GPS trace vs a GTFS `stop_times` schedule → per-segment delay. Synthesise a small GTFS feed for your city's routes for the demo. Cheap, and it lets you overlay delay hotspots on the congestion heatmap — where they coincide, you have a maintenance argument with a rupee figure attached.

---

## 11. Stack gaps

| Gap | Add | Why |
|---|---|---|
| **OpenStreetMap + osm2pgsql** | data source | Road classification for severity, crossing priors for absence detection, map-matching. Your Module 2 says "GIS reference data" — this is it, and it's free |
| **Evidence storage** | filesystem or MinIO, refs in Postgres | Thousands of JPEG blobs inside Postgres becomes a performance and backup problem. Store bytes outside, keys inside |
| **Event integrity** | ECDSA signing + hash chain | JWT/TLS/RBAC secure the *channel and access*. They do not make evidence **tamper-evident at rest**. For ANPR that may feed enforcement, that gap is worth closing — ~40 lines (`ARCHITECTURE.md` §5.3) |
| **GTFS + GPS trace** | data sources | Needed for §10 and for the `GpsSource` abstraction |
| **Docker Compose** | orchestration | One-command cold start. Not cosmetic — it's what saves you when the demo laptop reboots |
| **Albumentations** | training | The augmentation strategy in §2 |

### Role clarity in your stack list

You list PyTorch, ONNX Runtime, TensorRT, and OpenCV together. Pin down which runs where, or you'll get asked:

- **PyTorch** — training only, never on the edge node
- **ONNX Runtime** — edge inference. Good choice; faster and broader op support than `cv2.dnn`
- **TensorRT** — NVIDIA Jetson/GPU only. With no hardware you won't run it. Present it as the *deployment path*, not a demo claim
- **OpenCV** — decode, preprocessing, the entire adaptive vision layer, geometry/IPM, tracking support, blur, evidence encoding

That last line matters for your framing: switching inference to ONNX Runtime doesn't weaken the "OpenCV-centric CV" story, because Modules 11, 12, the geometry layer and all preprocessing are genuinely OpenCV. Just describe it accurately.

Also: pick **Recharts** over Chart.js — it's React-native (component-based, no imperative canvas refs) and will cost you less integration time.
