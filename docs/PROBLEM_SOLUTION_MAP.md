# UrbanPulse — Problem → Solution → Accountability Map

For every problem we detect: what fails today, what we detect, **who is legally responsible**, how the issue reaches them, and how we verify it was fixed.

Detection is the easy half. This document is the other half.

---

# Part 1 — Who actually owns a road in an Indian city?

Before you can send a pothole to anyone, you have to answer "whose pothole is it?" That is not obvious, because urban road ownership is **fragmented**:

| Agency | Owns | Example |
|---|---|---|
| **Municipal corporation** | Most city roads, by zone → ward | BBMP (Bengaluru), GHMC (Hyderabad), MCGM (Mumbai), GCC (Chennai), MCD (Delhi) |
| **State PWD** | State highways and major arterials inside city limits | Public Works Department |
| **NHAI** | National highways passing through the city | — |
| **Development authority** | Roads in new layouts, pre-handover to the corporation | BDA, HUDA, DDA |
| **Cantonment board / Port trust / Airport authority / Railways** | Pockets inside the city | — |
| **Private / apartment associations** | Internal layout roads | — |

And a second, independent axis of responsibility:

| Party | When they're liable |
|---|---|
| **Road contractor** | The segment was built/resurfaced under a work contract still inside its **Defect Liability Period** |
| **Utility agency** | The defect coincides with a badly restored trench they cut (water board, electricity, gas, telecom) |
| **Agency maintenance wing** | Everything else — routine maintenance budget |

## 1.1 The Defect Liability Period is your leverage

Road works in India are tendered with a **Defect Liability Period (DLP)** — commonly **2 to 5 years** depending on the corporation and road type (bitumen typically shorter, concrete/white-topping longer). During DLP, the contractor is contractually obliged to repair defects **at their own cost**, with penalties or security-deposit forfeiture for non-performance.

In practice, contractors escape this constantly, for one reason:

> The municipality cannot prove **when** the defect appeared or **exactly where** it is. Without a dated, located, photographic record, the contractor says "that's normal wear" or "that appeared after my period ended" — and the city pays for the repair out of maintenance budget.

**This is precisely the gap a bus fleet closes.** Because buses pass the same road every day, UrbanPulse knows the **date a pothole first appeared** — to within one day. Nothing else can produce that datum:

| Source | Can establish date of first appearance? |
|---|---|
| Fixed CCTV | No — doesn't see road surface |
| Quarterly inspection | No — 90-day uncertainty |
| Citizen complaint | No — reports when someone noticed, not when it formed |
| **Bus fleet, daily passes** | **Yes — to the day** |

So the output isn't "there's a pothole." It's:

```
Pothole, 0.42 m², MG Road near km 3.2
First observed:   2026-07-14  (absent on 2026-07-13 pass — 4 clean passes)
Segment resurfaced: 2025-03-02 under work order BBMP/RD/2024-25/1187
Contractor:       [name], DLP 36 months, expires 2028-03-02
→ LIABILITY: CONTRACTOR. Repair at contractor cost. Evidence pack attached.
```

That is a legally useful artifact, and it is the single strongest thing this project produces.

Pothole-related fatalities are a documented and litigated problem in India, and courts have repeatedly directed municipal accountability for them. A tamper-evident, timestamped evidentiary chain is therefore not decoration — it is the thing that makes the liability enforceable.

---

# Part 2 — The routing engine: from GPS point to responsible party

Every event, regardless of type, passes through the same six-stage resolution chain in `central/alerting`. This is the mechanism behind Module 10.

```
EVENT  (lat, lon, type, severity, first_observed, evidence)
  │
  ├─► [1] SPATIAL RESOLUTION                                        PostGIS
  │     ST_DWithin / ST_ClosestPoint against the road network
  │     → road_segment_id, road_name, road_class, chainage (km mark)
  │     → ward_id      (ST_Contains against ward polygons)
  │     → zone_id, special_zone flags (school zone, cantonment, port)
  │
  ├─► [2] JURISDICTION RESOLUTION                              rule table
  │     (road_class, ward, special_zone) → owning agency
  │       NH            → NHAI
  │       SH / arterial → State PWD
  │       collector / local → Municipal corporation
  │       inside cantonment/port polygon → that board
  │     → owning_agency_id
  │
  ├─► [3] LIABILITY RESOLUTION            ← answers "which contractor?"
  │     a) utility check (most specific wins)
  │        SELECT * FROM utility_cuts
  │         WHERE ST_DWithin(geom, event.geom, 5)
  │           AND event.first_observed BETWEEN restored_on
  │                                    AND restored_on + warranty
  │        → liability = UTILITY
  │     b) contract check
  │        SELECT * FROM work_contracts
  │         WHERE segment_id = event.road_segment_id
  │           AND event.first_observed BETWEEN completed_on AND dlp_end
  │        → liability = CONTRACTOR   (+ work_order_no, dlp_end)
  │     c) else
  │        → liability = AGENCY_MAINTENANCE
  │
  ├─► [4] SEVERITY & SLA
  │     severity = w₁·size + w₂·repeat_count + w₃·road_class
  │              + w₄·recency + w₅·school_zone_flag
  │     SLA lookup: (defect_type, severity, road_class) → due_in_hours
  │
  ├─► [5] RECIPIENT RESOLUTION
  │     (agency, ward, defect_type) → officer + escalation chain
  │       corporation road defect → ward Assistant/Junior Engineer
  │       regulatory signage      → Traffic Police, jurisdiction PS
  │       drainage                → Stormwater Drain division
  │       incidents               → Traffic Police control room
  │
  └─► [6] DISPATCH
        • internal  — severity-ranked work order in the UrbanPulse queue
        • external  — auto-file into the city's existing grievance system
        • notify    — email / SMS / WhatsApp with a signed evidence link
        • contractor— DLP notice: evidence pack + statutory repair deadline
```

## 2.1 Why we file into the *existing* grievance system

Cities already run complaint platforms (BBMP Sahaaya, MCGM's pothole app, CPGRAMS at the centre, Swachhata, and various state portals). Municipal staff already work those queues daily.

**We integrate rather than replace.** UrbanPulse auto-files a complaint — with GPS, photo, size, first-observed date and liability finding already filled in — into the workflow officers already use. No new bureaucracy, no retraining, no adoption barrier. That's the difference between a pilot that survives and a dashboard nobody opens.

## 2.2 Loop closure — the part nobody else has

```
work_order:  raised → acknowledged → assigned → in_progress → resolved
                                                     │
                    absence detection over N clean passes
                                                     ▼
                                          auto-verified RESOLVED
```

Today a contractor marks a job "complete" and **nobody independently checks.** Re-inspection costs a site visit, so it doesn't happen.

UrbanPulse buses drive past that spot tomorrow anyway. If the defect is gone across N passes with good visibility, the work order **auto-verifies as resolved**. If it's still there past SLA, it **auto-escalates** with a receipt:

```
Reported 2026-07-14 · SLA 48 h · marked "resolved" by contractor 2026-07-17
Still detected on 2026-07-18, 07-19, 07-20 — 31 bus passes, 19 detections
→ ESCALATE to Executive Engineer. False-completion flag raised.
```

Automated, independent verification of public works, at zero marginal cost. That is the strongest deployment argument in the project.

---

# Part 3 — Problem by problem

Each block: what fails today → what we detect → what we measure → who's responsible → how it reaches them → what they do → how we verify.

---

## 3.1 Potholes and damaged road surface

**Today:** A pothole forms after the first heavy rain. Nobody records it. It is found when a two-wheeler hits it, or on a quarterly survey four months later. Contractor liability is unenforceable because there's no date. Repair is unprioritised — whoever complains loudest gets fixed.

**Detect:** `yolo-infra` on the front camera at 3 fps (Module 1). Cross-fleet DBSCAN consensus at ~15 m confirms it across independent passes, killing shadow/tar-patch false positives.

**Measure:** size in m² via road-plane geometry · exact GPS after map-matching · **first-observed date** from the first pass that saw it (and the last clean pass that didn't) · confirmation count · growth rate over successive passes.

> Growth rate is a free bonus of repetition: a pothole widening 30% in ten days is structurally failing and deserves priority over a stable one of the same size. No other data source can see that.

**Responsible:** utility → contractor under DLP → agency maintenance, resolved in that order (Part 2 §3).

**Reaches them:** severity-ranked work order to the ward Assistant Engineer, auto-filed into the city grievance system, with the evidence pack. If contractor-liable, a DLP notice is generated naming the work order number and repair deadline.

**They do:** patch or resurface; contractor bears cost if inside DLP.

**Verify:** N clean passes → auto-resolved. Still present past SLA → escalate with the pass-count receipt.

---

## 3.2 Waterlogging

**Today:** Reported by citizens *during* the flood, when it's too late to act. No record of which spots flood repeatedly, so the same junction floods every monsoon for a decade.

**Detect:** `yolo-infra` waterlogging class, corroborated by the adaptive vision layer's rain condition flag (Module 12). Cross-referenced with the bus's own speed drop.

**Measure:** extent along the road · recurrence count across rain events · **onset speed** (how quickly it appears after rain starts) · whether the road became impassable (from ego speed).

**Responsible — two different owners, and the distinction matters:**

| Cause | Signal | Owner |
|---|---|---|
| Blocked / undersized storm drain | recurs at the same point every rain event | Stormwater Drain division |
| Road camber or level defect | localised pooling, no drain nearby | Roads division |

Recurring at the same point across many events is a **drainage design failure**, not routine maintenance — it must escalate to engineering, not the patching crew. Distinguishing these is only possible with repeat observation.

**Reaches them:** two channels at once —
- *Real-time:* live flood map to the **traffic police control room** and **city disaster management cell** during heavy rain, so they can close roads and reroute. A fleet of buses is a live, moving flood-depth sensor network — this is arguably the highest-value real-time output in the whole system.
- *Post-event:* recurrence report to SWD engineering with a ranked list of chronic flood points.

**Verify:** the point stops appearing in subsequent rain events.

---

## 3.3 Faded and missing zebra crossings

**Today:** Nobody has an inventory of road markings. Crossings fade over 2–3 years and are repainted only when someone complains, or never.

**Detect:** `yolo-infra` zebra class. "Faded" = detected with degraded confidence/contrast over successive passes — a *trend*, not a single reading. "Missing" = OSM prior or fleet-built inventory says a crossing exists here, and N passes with good visibility fail to see it (Module 2 logic, `ARCHITECTURE.md` §2.5).

**Measure:** fade trajectory over weeks · pedestrian volume at that location (Module 5) · **school-zone flag** · vehicle speeds through it.

**Responsible:** corporation's road-marking contract, with traffic police consulted on placement (they own regulatory decisions about where crossings go).

**Reaches them:** marking work order to corporation, notification to traffic police. Priority multiplied by the school-zone flag and by measured pedestrian volume — a faded crossing outside a school with 200 children/day crossing outranks a pristine one on an empty road.

**Verify:** detection confidence returns to baseline after repainting.

---

## 3.4 Missing or damaged road dividers

**Today:** A gap in a median enables wrong-side entry and head-on collisions. Found after an accident.

**Detect:** divider presence per frame, then **continuity analysis** along the segment — a gap is a run of frames where the divider should be present (based on prior passes and OSM `dual_carriageway` tagging) and isn't. This is structural reasoning, not object detection, which is why it's harder than the rest.

**Measure:** gap length in metres · whether wrong-side vehicle movement is observed through it (Module 3 + 6 give this directly) · accident-history overlay if available.

**Responsible:** corporation roads division; PWD if a state highway.

**Reaches them:** high-priority safety work order, plus traffic police notification since they may need to barricade temporarily before a permanent fix.

**Verify:** continuity restored on later passes.

---

## 3.5 Damaged, obscured or missing traffic signboards

**Today:** No sign inventory. A stolen or twisted STOP sign is discovered by a collision.

**Detect:** signboard detection + optional OCR legibility check (Module 2). Missing via inventory absence detection; obscured via detection with degraded confidence plus an occluding object (tree branch, hoarding, banner).

**Measure:** sign type · condition class (intact / damaged / obscured / illegible / missing) · GPS · how long it has been in that state.

**Responsible — routes by sign type, and this split is important:**

| Sign type | Owner |
|---|---|
| Regulatory (STOP, no-entry, speed limit, one-way) | **Traffic police** — in most Indian cities they own regulatory signage |
| Informational / street name / directional | Municipal corporation |
| Highway signage | NHAI / PWD |

A missing regulatory sign is a liability event and routes to traffic police immediately. A missing street-name sign is a routine corporation ticket. Same detector, completely different urgency and recipient.

**Verify:** sign reappears in the inventory as `CONFIRMED`.

---

## 3.6 Vehicle density and congestion

**Today:** Known only at the few junctions with CCTV or loop detectors. Signal timings are set from surveys years old.

**Detect:** `yolo-dyn` + ByteTrack (Module 3), plus — critically — **the bus's own GPS speed**, which is an exact congestion measurement requiring no CV at all.

**Measure:** vehicles per 100 m of lane by class · mean ground speed · ego-speed profile · dwell time below threshold · time-of-day pattern across weeks.

**Responsible / reaches them:** three consumers, three timescales —

| Recipient | Timescale | Action |
|---|---|---|
| Traffic police control room | minutes | adjust signal timing, deploy personnel |
| Transport planning dept | months | corridor improvement, lane reallocation |
| Transit operator | weeks | route and headway planning |

**Verify:** post-intervention density and ego-speed measured on the same segment — the system evaluates its own recommendations.

---

## 3.7 Traffic bottlenecks

**Today:** Identified anecdotally. The *cause* is usually never diagnosed, so the same junction is "fixed" repeatedly without improvement.

**Detect:** sustained low ego speed + high density + long dwell (Module 4).

**Measure — and this is the useful part, separating pattern from incident:**

| Pattern | Diagnosis | Route to |
|---|---|---|
| Same place, same time, every weekday | Structural — capacity, geometry, signal timing | Transport planning |
| Same place, random times | Illegal parking, encroachment, badly sited bus stop | Traffic police enforcement / corporation |
| One-off | Incident or breakdown | Control room, real-time |

Distinguishing structural from incidental congestion is what turns a heatmap into a diagnosis. It requires repeat observation over weeks — which the fleet gives you for free.

**Bonus:** where our *own* buses lose the most time, that segment becomes a costed case for a bus priority lane or signal priority. The transit operator can fund that from its own operating savings.

---

## 3.8 Origin–destination patterns

**Today:** Derived from decade-old household surveys, or not at all. Bus routes are planned on intuition.

**Detect:** hashed plate tokens matched across the fleet — never storing identities:

```
plate_token = HMAC-SHA256(normalised_plate, daily_rotating_salt)[:16]

bus A, zone 1, 08:10 → token X
bus B, zone 4, 08:35 → token X
   → one O-D observation + a measured 25-min corridor travel time
```

Irreversible, and unlinkable across days because the salt rotates.

**Measure:** zone-to-zone flow matrix by time of day · **measured** link travel times (a far stronger congestion signal than density alone).

**Responsible / reaches them:** metropolitan planning authority and the transit operator — for route rationalisation, new route design, and identifying corridors that justify mass transit investment.

**Note the incentive alignment:** the bus operator who owns the fleet gets direct planning value from its own data. That's what makes this deployable rather than a favour to another department.

---

## 3.9 Route delays (transit performance)

**Today:** Passengers know buses are late. The operator often can't say *where* the time is lost.

**Detect:** bus GPS trace vs GTFS `stop_times` schedule.

**Measure:** delay per stop-to-stop segment · delay distribution by time of day · bus bunching · which segments contribute most lost minutes fleet-wide.

**Responsible / reaches them:** operator's operations control room (real-time bunching correction, schedule adjustment) and planning (signal-priority requests at the specific segments where minutes are lost).

**The compounding insight:** overlay route-delay hotspots on the congestion heatmap *and* the defect map. Where all three coincide, you have a maintenance argument with a rupee figure: *"this 400 m stretch costs our fleet 1,100 bus-minutes per week, and it's failing because of a contractor-liable defect."* That sentence is what "actionable insight for transport authorities" means.

---

## 3.10 Vulnerable pedestrians and school children crossing

**Today:** A crossing gets a signal or a warden after a child is injured. Risk is never quantified beforehand.

**Detect:** person detection + trajectory into the carriageway + approaching vehicle with insufficient stopping distance (Module 5). Ground-frame vehicle speed from the geometry + ego-motion layers makes "insufficient" a real calculation rather than a guess.

**Measure:** near-miss risk events per week at that location · time-of-day clustering (school opening/closing peaks) · vehicle speeds through the zone · whether a marked crossing exists there at all (links to §3.3).

**Responsible / reaches them:**
- *Recurring pattern:* infrastructure request to corporation — pedestrian signal, speed table, refuge island, repainted crossing — justified with a number: *"41 risk events/week, 08:15–08:45, 84% of vehicles above 40 km/h."*
- *Time-patterned:* traffic police, to post a warden during school hours.
- *Notification:* the school authority, so they can adjust gate timing or supervision.

**The point:** today the case for a pedestrian signal is anecdotal, so it loses to other budget lines. UrbanPulse makes it a measured risk rate. Quantified risk is fundable; anecdote is not.

**Verify:** risk-event rate at that location after the intervention.

---

## 3.11 Rash driving

**Today:** Enforced only where police physically stand. Most of the network, most of the time, is unobserved.

**Detect:** ground-frame trajectory analysis (Module 6) — longitudinal acceleration, jerk, lateral weaving, time-headway — computed **after ego-motion compensation**, without which the bus's own braking triggers constant false positives.

**Measure:** behaviour type · severity · plate (Module 7) with confidence and `frames_voted` · GPS · time · repeat occurrences of the same token across the fleet.

**Responsible / reaches them — with an honest legal boundary:**

Camera evidence from a device not notified by the state transport authority generally **cannot directly generate an e-challan.** So:
- *What we do:* provide traffic police with hotspot maps for enforcement deployment, and repeat-offender intelligence.
- *What we don't claim:* automatic prosecution. The challan remains a human enforcement decision, and evidentiary use requires the system to be formally notified.

State this boundary yourself in the viva. Overclaiming here is the fastest way to lose credibility with a BEL panel.

**Two outputs that are immediately actionable without any legal change:**
1. **Hotspot deployment maps** — where and when rash driving concentrates, so limited enforcement staff go to the right places.
2. **Own-driver scoring** — run the identical trajectory analysis on the **ego vehicle**. This grades your own bus drivers on harsh braking, cornering and speeding, using only GPS. It needs no camera, no legal clearance, and it delivers immediate value to the fleet operator: driver training, insurance negotiation, fuel savings, passenger comfort. Cheapest high-value feature in the project — and it's the one that gets a transit authority to say yes to the pilot.

---

## 3.12 Hit-and-run

**Today:** Unsolved when there's no witness. The victim gets no compensation, the offender no consequence.

**Detect:** collision-signature detection in the trajectory analysis (Module 6) → triggers the cascade.

**The cascade, in order, within seconds:**

1. **Ring buffer dump** — the last ~15 s is already in memory, so we recover the moments *before* impact. A dashcam that starts recording on trigger cannot do this; it's the reason we hold a buffer.
2. **Stage-2 ANPR** on that track only, gated to readable range, with multi-frame character voting → plate + `aggregate_confidence` + `frames_voted`.
3. **Evidence sealing** — plate crop and text encrypted under the command centre's public key. The edge holds no decryption key; every unwrap is logged.
4. **Priority uplink** — jumps the outbox queue ahead of thousands of queued potholes.
5. **Central alert** — traffic police control room, immediately.

**Then the capability nothing else has — fleet-wide pursuit trace:**

```
08:14:22  bus 12, Junction A  — collision detected, token X, conf 0.91
08:19:40  bus 7,  Ring Road   — token X observed, heading north
08:31:05  bus 22, Highway exit— token X observed
   → the fleeing vehicle's post-incident path, from buses that were
     simply driving their routes
```

A fleet of buses is a passive, city-wide plate-observation network. A vehicle fleeing an incident will pass other buses. That turns an unsolvable case into a traceable one.

**Responsible / reaches them:** traffic police control room (immediate alert + evidence), emergency services if injury is detected, and the plate → registered-owner lookup via **VAHAN** — which is a restricted, police-only integration. We provide the plate and the evidence; the lookup and the FIR are police actions.

**Why this matters beyond enforcement:** hit-and-run compensation under the amended Motor Vehicles Act depends on the case being pursued. Identifying the vehicle is what lets a victim's family actually claim.

---

# Part 4 — Database schema for the accountability layer

```sql
-- Spatial + jurisdiction
agencies        (id, name, type)          -- corporation|pwd|nhai|traffic_police|utility|swd
wards           (id, name, zone_id, geom POLYGON)
road_segments   (id, geom LINESTRING, osm_way_id, name, road_class,
                 ward_id, owning_agency_id, lanes, is_dual_carriageway)
special_zones   (id, kind, geom POLYGON)  -- school|hospital|cantonment|port|market

-- Liability
contractors     (id, name, contact, license_no, blacklist_flag)
work_contracts  (id, work_order_no, contractor_id, segment_id,
                 work_type, completed_on, dlp_months, dlp_end,
                 contract_value, security_deposit)
utility_cuts    (id, utility_agency_id, geom, cut_on, restored_on,
                 warranty_months, permit_no)

-- Routing
officers        (id, agency_id, ward_id, role, name, contact, escalates_to)
sla_rules       (defect_type, severity_band, road_class,
                 due_hours, escalate_after_hours, channel)

-- Work management
work_orders     (id, asset_id, liability, responsible_party_id,
                 raised_at, due_at, state, escalation_level,
                 external_ticket_ref)
escalations     (id, work_order_id, level, at, to_officer_id, reason)
verifications   (id, work_order_id, passes_clean, verified_at, method)
disclosure_log  (id, incident_id, unwrapped_by, at, justification)
```

The join that answers the user's question is exactly this:

```sql
SELECT c.name AS contractor, wc.work_order_no, wc.dlp_end
FROM   events e
JOIN   road_segments  s  ON ST_DWithin(s.geom, e.geom, 20)
JOIN   work_contracts wc ON wc.segment_id = s.id
JOIN   contractors    c  ON c.id = wc.contractor_id
WHERE  e.first_observed BETWEEN wc.completed_on AND wc.dlp_end;
```

---

# Part 5 — What data is real, what is synthetic

Be explicit about this. Stating it is a strength; being caught assuming it is fatal.

| Data | Real availability | Our approach |
|---|---|---|
| Road network + classification | **OpenStreetMap, free** | Real |
| Ward / zone boundaries | Published shapefiles for most metros | Real |
| Road class → agency rules | Derivable from policy | Real rule table |
| **Work contracts + DLP** | Inside corporation works-management systems; not a public API | **Real schema, synthetic seed — declared as an integration point** |
| Contractor contacts | Internal | Synthetic |
| Utility cut permits | Internal to each utility | Synthetic |
| Officer directory | Partially public | Synthetic |
| Grievance system API | Exists per city, varies | Adapter interface, mock endpoint |
| VAHAN plate → owner | Restricted, police-only | Integration point; never demoed |
| GTFS schedule | Some operators publish | Synthetic for demo |

The framing to use:

> **The schema and the join logic are our contribution. The contract data is an integration with systems the corporation already runs.** We built the accountability engine; plugging in the real works database is a data-sharing agreement, not an engineering problem.

That is an honest, complete answer, and it's what separates a deployable design from a demo.

---

# Part 6 — The one-slide summary

```
       DETECT              LOCATE           ATTRIBUTE          DISPATCH           VERIFY
   ┌───────────┐      ┌────────────┐     ┌───────────┐     ┌───────────┐    ┌───────────┐
   │ YOLO on   │      │ IPM + GPS  │     │ PostGIS   │     │ ranked    │    │ absence   │
   │ bus feed  │─────►│ → exact    │────►│ ward,     │────►│ work order│───►│ detection │
   │ + fleet   │      │ defect     │     │ agency,   │     │ + evidence│    │ over next │
   │ consensus │      │ position   │     │ contractor│     │ + SLA     │    │ N passes  │
   └───────────┘      └────────────┘     │ under DLP │     └───────────┘    └───────────┘
                                         └───────────┘                            │
                                                                    ┌─────────────┴────────┐
                                                              auto-close          escalate
                                                              if fixed         if past SLA
```

Every arrow in that chain is a component we build. Most projects stop at the second box.

**The closing line:** *we don't just find the pothole — we find who owes the repair, hand them dated photographic evidence, and check tomorrow whether they did it.*
