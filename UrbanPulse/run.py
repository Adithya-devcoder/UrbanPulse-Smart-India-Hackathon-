#!/usr/bin/env python3
import os
# Force X11/xcb backend — prevents blank white window on Wayland systems
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
os.environ.setdefault("DISPLAY", ":0")
"""
UrbanPulse — Unified Real-Time Urban Intelligence Platform v3
Smart India Hackathon (SIH)

Detections (simultaneously, single OpenCV window):
  1. Vehicle detection + tracking + density  (YOLO11n + ByteTrack)
  2. Obstacle detection — persons, cyclists, cattle proxy  (YOLOv8n COCO)
  3. Pothole detection + GPS location tagging  (custom best.pt)
  4. Waterlogging detection  (HSV + contour heuristic)
  5. Accident + Hit-and-Run detection  (velocity + direction model)
  6. Street sign detection + OCR text verification  (EasyOCR)

Outputs:
  - Single OpenCV window with all annotations
  - JSON event files per detection type
  - Per-road GPS reports with priority scores
  - live_state.json updated every 1s → Streamlit dashboard live-reload

Usage:
  python UrbanPulse/run.py
  python UrbanPulse/run.py --video path/to/video.mp4
  python UrbanPulse/run.py --headless        # no display window
"""

import cv2
import os
import sys
import json
import math
import glob
import time
import argparse
import numpy as np
from collections import deque
from datetime import datetime
from ultralytics import YOLO

# ── Location provider ──────────────────────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "phase2", "pothole"))
from location_provider import LocationProvider

# ── Backend bridge (YOLO → FastAPI → Supabase) ─────────────────────────
# Posts detection events to the backend in a background thread.
# Falls back silently if backend is not running.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from bridge import bridge as _backend_bridge
    BRIDGE_ENABLED = True
except Exception as _be:
    BRIDGE_ENABLED = False
    print(f"  ⚠ Bridge import error: {_be}")

def _post(event_type, loc, **extra):
    """Helper: post detection to backend bridge (non-blocking)."""
    if BRIDGE_ENABLED:
        _backend_bridge.post_detection(event_type, loc, extra)


# ══════════════════════════════════════════════════════════════════════
# CLI ARGUMENTS
# ══════════════════════════════════════════════════════════════════════

parser = argparse.ArgumentParser(description="UrbanPulse Unified Platform v3")
parser.add_argument("--video",    default="UrbanPulse/phase1/videos/traffic2.mp4")
parser.add_argument("--headless", action="store_true", help="No display window")
args = parser.parse_args()

# ══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════

BASE = "UrbanPulse"

# Model paths
VEHICLE_MODEL  = f"{BASE}/models/vehicle/yolo11n.pt"
POTHOLE_MODEL  = f"{BASE}/models/pothole/best.pt"
OBSTACLE_MODEL = f"{BASE}/models/obstacle/yolov8n.pt"   # COCO 80-class

# Output directories
STATE_DIR          = f"{BASE}/prototype/state"
REPORTS_DIR        = f"{BASE}/reports"
EVENT_DIR_POTHOLE  = f"{BASE}/phase2/pothole/events"
EVENT_DIR_WATER    = f"{BASE}/events/water"
EVENT_DIR_ACCIDENT = f"{BASE}/events/accident"
EVENT_DIR_OBSTACLE = f"{BASE}/events/obstacle"
EVENT_DIR_SIGN     = f"{BASE}/events/sign"

for d in [STATE_DIR, REPORTS_DIR, EVENT_DIR_POTHOLE, EVENT_DIR_WATER,
          EVENT_DIR_ACCIDENT, EVENT_DIR_OBSTACLE, EVENT_DIR_SIGN]:
    os.makedirs(d, exist_ok=True)

# ── Detection thresholds ──────────────────────────────────────────────
VEHICLE_CONF  = 0.40
POTHOLE_CONF  = 0.55
OBSTACLE_CONF = 0.40
SIGN_CONF     = 0.45

# ── Confirmation frames (multi-frame persistence = fewer false positives)
POTHOLE_CONFIRM  = 3
WATER_CONFIRM    = 10
OBSTACLE_CONFIRM = 4

# ── Spatial matching ──────────────────────────────────────────────────
POTHOLE_MAX_DIST  = 110
WATER_MAX_DIST    = 160
OBSTACLE_MAX_DIST = 120

# ── Traffic density ──────────────────────────────────────────────────
DENSITY_HIGH   = 15
DENSITY_MEDIUM = 7

# ── COCO class IDs ───────────────────────────────────────────────────
VEHICLE_CLASSES  = {2: "Car", 3: "Motorcycle", 5: "Bus", 7: "Truck"}
OBSTACLE_CLASSES = {
    0:  "Person",
    1:  "Cyclist",
    16: "Dog",
    17: "Horse",      # cattle proxy
    19: "Cow",
    9:  "Traffic Light",
    11: "Stop Sign",
    12: "Parking Meter",
}
SIGN_CLASSES = {9: "Traffic Light", 11: "Stop Sign", 12: "Parking Meter"}

# ── Accident heuristic (multi-condition, high precision) ─────────────
ACC_IOU_THRESH    = 0.35   # bounding box overlap
ACC_MIN_FRAMES    = 5      # overlap must persist N frames
ACC_VELOCITY_MIN  = 8.0    # px/frame — vehicles must have been moving
ACC_STOP_THRESH   = 3.0    # px/frame — "stopped" threshold after overlap
ACC_COOLDOWN      = 200    # frames between accident events

# ── Hit-and-run ──────────────────────────────────────────────────────
HTR_PROX_THRESH   = 120    # px — vehicle-to-person proximity
HTR_DISAPPEAR_WIN = 25     # frames — person must vanish within this window
HTR_ACCEL_THRESH  = 5.0    # px/frame — vehicle must accelerate away

# ── Processing cadence ────────────────────────────────────────────────
VEHICLE_SKIP  = 2
POTHOLE_SKIP  = 2
WATER_SKIP    = 3
OBSTACLE_SKIP = 3
SIGN_SKIP     = 10    # sign check is slow (OCR), every 10 frames

# ── State file update frequency ───────────────────────────────────────
STATE_EVERY   = 30    # traffic_state, every N frames
LIVE_EVERY    = 30    # live_state.json, every N frames

# ── Road segment resolution ───────────────────────────────────────────
GPS_ROUND = 3         # round GPS to this many decimals → segment ID

# ── Waterlogging HSV ─────────────────────────────────────────────────
WATER_HSV_LOWER  = np.array([ 95,  30,  40])
WATER_HSV_UPPER  = np.array([130,  90, 120])
WATER_MIN_AREA   = 6000
WATER_ASPECT_MAX = 3.0

# ── GIS sign reference (simulated — in production, use BBMP/MCD API) ──
# Key: GPS segment "lat_lon", value: list of expected sign texts
GIS_SIGNS = {
    "13.082_80.270": ["SPEED LIMIT 40", "NO PARKING"],
    "13.083_80.271": ["STOP", "ONE WAY"],
    "13.081_80.269": ["SCHOOL ZONE", "SPEED LIMIT 30"],
}

# ── HUD colors (BGR) ─────────────────────────────────────────────────
C_GREEN   = ( 30, 210,  30)
C_ORANGE  = (  0, 165, 255)
C_RED     = (  0,  40, 230)
C_BLUE    = (230, 130,  20)
C_MAGENTA = (220,  20, 220)
C_CYAN    = (200, 200,   0)
C_YELLOW  = (  0, 220, 220)
C_WHITE   = (240, 240, 240)
C_DARK    = ( 12,  12,  12)
C_HEADER  = (  0, 210, 255)
C_PURPLE  = (180,  50, 200)
C_TEAL    = (180, 200,   0)

# ══════════════════════════════════════════════════════════════════════
# STARTUP BANNER
# ══════════════════════════════════════════════════════════════════════

def banner():
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     UrbanPulse — Smart India Hackathon (SIH) v3              ║")
    print("║     AI-Powered Urban Road Intelligence Platform              ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Traffic · Potholes · Waterlogging · Accidents · Obstacles  ║")
    print("║  Street Signs · Hit-and-Run · Road Reports · Live Dashboard  ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

banner()

# ══════════════════════════════════════════════════════════════════════
# LOAD MODELS
# ══════════════════════════════════════════════════════════════════════

print("Loading AI models...")

vehicle_model  = YOLO(VEHICLE_MODEL)
print(f"  ✓ Vehicle / Traffic  → {VEHICLE_MODEL}")

pothole_model  = YOLO(POTHOLE_MODEL)
print(f"  ✓ Pothole Detection  → {POTHOLE_MODEL}")

obstacle_model = YOLO(OBSTACLE_MODEL)
print(f"  ✓ Obstacle Detection → {OBSTACLE_MODEL}  (COCO 80-class, persons/cyclists/cattle)")

print(f"  ✓ Waterlogging       → HSV + contour analysis")
print(f"  ✓ Accident / HTR     → Velocity + direction heuristic")

# EasyOCR for street sign text
OCR_ENABLED = False
ocr_reader  = None
print("  Loading EasyOCR for street signs...", end=" ", flush=True)
try:
    import easyocr
    ocr_reader  = easyocr.Reader(["en"], gpu=False, verbose=False)
    OCR_ENABLED = True
    print("✓")
except Exception as e:
    print(f"✗ ({e})")
    print("    Street sign OCR disabled. Install with: pip install easyocr")

print()

# ══════════════════════════════════════════════════════════════════════
# GPS / AVL PROVIDER
# ══════════════════════════════════════════════════════════════════════

gps = LocationProvider()

def road_segment_id(loc):
    """Convert GPS to road segment string key."""
    lat = round(loc["latitude"],  GPS_ROUND)
    lon = round(loc["longitude"], GPS_ROUND)
    return f"{lat}_{lon}"

# ══════════════════════════════════════════════════════════════════════
# RUNTIME STATE
# ══════════════════════════════════════════════════════════════════════

# ── Traffic
vc      = {"Car": 0, "Motorcycle": 0, "Bus": 0, "Truck": 0}
v_total = 0
density = "UNKNOWN"

# ── Velocity tracking  tid → deque[(frame, cx, cy, box)]
v_history    = {}
# Person tracking for hit-and-run  tid → deque[(frame, cx, cy)]
p_history    = {}

# ── Accident
overlap_ctr       = {}   # pair → consecutive frames
last_acc_frame    = -ACC_COOLDOWN
accidents         = 0
acc_events        = []

# ── Hit-and-run
htr_candidates    = {}   # person_tid → {"last_frame", "near_vehicle_tid", ...}
htr_count         = 0

# ── Potholes
potholes = {}
S = {"ph_next": 1, "ph_count": 0,
     "wt_next": 1, "wt_count": 0,
     "ob_next": 1, "ob_count": 0}

# ── Water
waters = {}

# ── Obstacles
obstacles = {}

# ── Signs
sign_alerts = []   # list of sign text mismatches

# ── Road reports  segment_id → report dict
road_reports = {}

# ── General
frame_num  = 0
fps        = 0.0
fps_t      = time.time()
fps_f      = 0
state_tick = 0
live_tick  = 0

# ══════════════════════════════════════════════════════════════════════
# UTILITY
# ══════════════════════════════════════════════════════════════════════

def cdist(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def iou_box(b1, b2):
    xa = max(b1[0], b2[0]); ya = max(b1[1], b2[1])
    xb = min(b1[2], b2[2]); yb = min(b1[3], b2[3])
    inter = max(0, xb-xa) * max(0, yb-ya)
    if inter == 0: return 0.0
    a1 = (b1[2]-b1[0])*(b1[3]-b1[1])
    a2 = (b2[2]-b2[0])*(b2[3]-b2[1])
    return inter / float(a1+a2-inter)

def velocity(history, lookback=4):
    """Average px/frame speed over last `lookback` frames."""
    h = list(history)
    if len(h) < 2: return 0.0
    recent = h[-min(lookback, len(h)):]
    dists  = [cdist((recent[i][1], recent[i][2]),
                    (recent[i-1][1], recent[i-1][2]))
              for i in range(1, len(recent))]
    return sum(dists) / len(dists) if dists else 0.0

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def collect_events(directory, prefix):
    events = []
    for p in glob.glob(os.path.join(directory, f"{prefix}-*.json")):
        try:
            with open(p) as f: events.append(json.load(f))
        except Exception: pass
    events.sort(key=lambda e: e.get("timestamp",""))
    return events

def priority_score(report):
    """Higher = more urgent."""
    return (report.get("potholes",    0) * 10 +
            report.get("waterlogging",0) *  8 +
            report.get("accidents",   0) * 25 +
            report.get("htr",         0) * 30 +
            report.get("obstacles",   0) *  3 +
            report.get("sign_issues", 0) *  5)

# ══════════════════════════════════════════════════════════════════════
# ROAD REPORT SYSTEM
# ══════════════════════════════════════════════════════════════════════

def update_road_report(segment_id, loc, event_type):
    """Accumulate events per road segment, update priority score."""
    if segment_id not in road_reports:
        road_reports[segment_id] = {
            "segment_id":   segment_id,
            "latitude":     loc["latitude"],
            "longitude":    loc["longitude"],
            "bus_id":       loc["bus_id"],
            "first_seen":   loc["timestamp"],
            "last_updated": loc["timestamp"],
            "potholes":     0,
            "waterlogging": 0,
            "accidents":    0,
            "htr":          0,
            "obstacles":    0,
            "sign_issues":  0,
            "events":       [],
            "priority_score": 0,
            "priority_level": "LOW"
        }

    r = road_reports[segment_id]
    r["last_updated"] = loc["timestamp"]

    if event_type == "POTHOLE":     r["potholes"]     += 1
    if event_type == "WATERLOGGING":r["waterlogging"]  += 1
    if event_type == "ACCIDENT":    r["accidents"]     += 1
    if event_type == "HTR":         r["htr"]           += 1
    if event_type == "OBSTACLE":    r["obstacles"]     += 1
    if event_type == "SIGN_ISSUE":  r["sign_issues"]   += 1

    r["events"].append({"type": event_type, "ts": loc["timestamp"]})
    r["events"] = r["events"][-50:]   # keep last 50

    score = priority_score(r)
    r["priority_score"] = score
    r["priority_level"] = ("CRITICAL" if score >= 80
                           else "HIGH"     if score >= 40
                           else "MEDIUM"   if score >= 15
                           else "LOW")

    # Write individual road report
    save_json(os.path.join(REPORTS_DIR, f"road_{segment_id}.json"), r)

def write_road_priority_state():
    """Write sorted priority list to state file."""
    sorted_roads = sorted(road_reports.values(),
                          key=lambda r: r["priority_score"], reverse=True)
    save_json(os.path.join(STATE_DIR, "road_priority.json"), {
        "generated":   datetime.now().isoformat(),
        "total_roads": len(sorted_roads),
        "roads":       sorted_roads
    })

# ══════════════════════════════════════════════════════════════════════
# STATE FILE WRITERS
# ══════════════════════════════════════════════════════════════════════

def write_traffic_state():
    save_json(os.path.join(STATE_DIR, "traffic_state.json"), {
        "vehicles": v_total, "density": density,
        "cars":     vc["Car"], "motorcycles": vc["Motorcycle"],
        "buses":    vc["Bus"], "trucks": vc["Truck"],
        "timestamp": datetime.now().isoformat()
    })

def write_pothole_state():
    events = collect_events(EVENT_DIR_POTHOLE, "POTHOLE")
    loc    = gps.get_location()
    if events:
        lat = events[-1]["latitude"]; lon = events[-1]["longitude"]
        state = {
            "potholes":    len(events), "status": "POTHOLES DETECTED",
            "bus_id":      events[-1]["bus_id"],
            "latitude":    lat, "longitude": lon,
            "timestamp":   events[-1]["timestamp"],
            "confidence":  events[-1]["confidence"],
            "video":       events[-1].get("video",""),
            "frame":       events[-1].get("frame", 0),
            "event_id":    events[-1]["event_id"],
            "all_locations": [{"lat": e["latitude"], "lon": e["longitude"],
                               "confidence": e["confidence"]} for e in events]
        }
    else:
        state = {
            "potholes": 0, "status": "NO POTHOLES DETECTED",
            "bus_id": loc["bus_id"],
            "latitude": loc["latitude"], "longitude": loc["longitude"],
            "timestamp": loc["timestamp"], "confidence": 0,
            "all_locations": []
        }
    save_json(os.path.join(STATE_DIR, "pothole_state.json"), state)

def write_water_state():
    events = collect_events(EVENT_DIR_WATER, "WATER")
    loc    = gps.get_location()
    if events:
        state = {
            "waterlog_count": len(events), "status": "WATERLOGGING DETECTED",
            "bus_id": events[-1]["bus_id"],
            "latitude": events[-1]["latitude"], "longitude": events[-1]["longitude"],
            "timestamp": events[-1]["timestamp"], "confidence": events[-1]["confidence"],
            "all_locations": [{"lat": e["latitude"], "lon": e["longitude"],
                               "confidence": e["confidence"]} for e in events]
        }
    else:
        state = {
            "waterlog_count": 0, "status": "NO WATERLOGGING DETECTED",
            "bus_id": loc["bus_id"],
            "latitude": loc["latitude"], "longitude": loc["longitude"],
            "timestamp": loc["timestamp"], "confidence": 0, "all_locations": []
        }
    save_json(os.path.join(STATE_DIR, "water_state.json"), state)

def write_accident_state():
    loc = gps.get_location()
    save_json(os.path.join(STATE_DIR, "accident_state.json"), {
        "accidents": accidents, "htr": htr_count,
        "status":    ("ACCIDENT/HTR DETECTED" if accidents+htr_count > 0
                      else "NO ACCIDENTS DETECTED"),
        "bus_id":    loc["bus_id"],
        "latitude":  loc["latitude"], "longitude": loc["longitude"],
        "timestamp": loc["timestamp"],
        "recent_alerts": acc_events[-5:]
    })

def write_live_state():
    """Written every LIVE_EVERY frames — dashboard reads this for live data."""
    loc = gps.get_location()
    save_json(os.path.join(STATE_DIR, "live_state.json"), {
        "frame":       frame_num,
        "fps":         round(fps, 1),
        "timestamp":   datetime.now().isoformat(),
        "bus_id":      loc["bus_id"],
        "latitude":    loc["latitude"],
        "longitude":   loc["longitude"],
        "vehicles":    v_total,
        "density":     density,
        "cars":        vc["Car"],
        "motorcycles": vc["Motorcycle"],
        "buses":       vc["Bus"],
        "trucks":      vc["Truck"],
        "potholes":    S["ph_count"],
        "waterlogging":S["wt_count"],
        "obstacles":   S["ob_count"],
        "accidents":   accidents,
        "htr":         htr_count,
        "sign_issues": len(sign_alerts),
        "active_road_issues": len([r for r in road_reports.values()
                                   if r["priority_level"] in ("HIGH","CRITICAL")])
    })

# ══════════════════════════════════════════════════════════════════════
# WATERLOGGING DETECTOR (HSV heuristic)
# ══════════════════════════════════════════════════════════════════════

def detect_waterlogging(frame):
    h, w   = frame.shape[:2]
    rs     = int(h * 0.45)
    roi    = frame[rs:, :]
    hsv    = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    mask   = cv2.inRange(hsv, WATER_HSV_LOWER, WATER_HSV_UPPER)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11,11))
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    results = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < WATER_MIN_AREA: continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        if bh / max(bw,1) > WATER_ASPECT_MAX: continue
        if y < 10: continue
        y_full = y + rs
        conf   = min(1.0, area / (w * h * 0.08))
        results.append({
            "box": [x, y_full, x+bw, y_full+bh],
            "conf": round(conf, 3),
            "center": (x+bw//2, y_full+bh//2)
        })
    return results

# ══════════════════════════════════════════════════════════════════════
# HUD OVERLAY
# ══════════════════════════════════════════════════════════════════════

def draw_hud(frame, h, w, ph_count, wt_count):
    loc = gps.get_location()

    # Top bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0,0), (w,52), C_DARK, -1)
    cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)
    header = (f"  URBANPULSE v3  |  Bus: {loc['bus_id']}"
              f"  |  GPS: {loc['latitude']:.4f}, {loc['longitude']:.4f}"
              f"  |  Frame: {frame_num}  |  FPS: {fps:.1f}")
    cv2.putText(frame, header, (8,34), cv2.FONT_HERSHEY_SIMPLEX,
                0.50, C_HEADER, 1, cv2.LINE_AA)

    # Left panel
    panel_w = 274
    ov2 = frame.copy()
    cv2.rectangle(ov2, (0,52), (panel_w,h), (8,8,8), -1)
    cv2.addWeighted(ov2, 0.76, frame, 0.24, 0, frame)
    cv2.line(frame, (panel_w,52), (panel_w,h), (50,50,50), 1)

    def T(text, y, color=C_WHITE, scale=0.50, bold=False):
        cv2.putText(frame, text, (10,y), cv2.FONT_HERSHEY_SIMPLEX,
                    scale, color, 2 if bold else 1, cv2.LINE_AA)

    def SH(text, y):
        cv2.rectangle(frame, (4,y-16), (panel_w-4,y+6), (30,30,30), -1)
        T(text, y, C_HEADER, 0.48, bold=True)
        return y+22

    y = 72

    y = SH("TRAFFIC INTELLIGENCE", y)
    d_col = C_RED if density=="HIGH" else C_ORANGE if density=="MEDIUM" else C_GREEN
    T(f"  Vehicles : {v_total}", y);         y += 17
    T(f"  Density  : {density}", y, d_col);  y += 17
    T(f"  Cars:{vc['Car']}  Bikes:{vc['Motorcycle']}  Buses:{vc['Bus']}  Trucks:{vc['Truck']}", y); y += 22

    y = SH("OBSTACLE DETECTION", y)
    ob_col = C_YELLOW if S["ob_count"] > 0 else C_WHITE
    T(f"  Confirmed : {S['ob_count']}", y, ob_col);  y += 17
    T(f"  Tracking  : {len(obstacles)}", y);          y += 22

    y = SH("POTHOLE DETECTION", y)
    ph_col = C_RED if ph_count > 0 else C_WHITE
    T(f"  Confirmed : {ph_count}", y, ph_col);        y += 17
    T(f"  Tracking  : {len(potholes)}", y);           y += 22

    y = SH("WATERLOGGING", y)
    wt_col = C_BLUE if wt_count > 0 else C_WHITE
    T(f"  Confirmed : {wt_count}", y, wt_col);        y += 17
    T(f"  Tracking  : {len(waters)}", y);              y += 22

    y = SH("SAFETY", y)
    ac_col = C_MAGENTA if accidents+htr_count > 0 else C_WHITE
    T(f"  Accidents : {accidents}", y, ac_col);        y += 17
    T(f"  Hit & Run : {htr_count}", y, ac_col);        y += 17
    si_col = C_ORANGE if sign_alerts else C_WHITE
    T(f"  Sign Issues: {len(sign_alerts)}", y, si_col); y += 22

    y = SH("ROAD REPORTS", y)
    critical = [r for r in road_reports.values() if r["priority_level"]=="CRITICAL"]
    high     = [r for r in road_reports.values() if r["priority_level"]=="HIGH"]
    T(f"  Roads tracked : {len(road_reports)}", y);    y += 17
    T(f"  Critical      : {len(critical)}", y,
      C_RED if critical else C_WHITE);                  y += 17
    T(f"  High priority : {len(high)}", y,
      C_ORANGE if high else C_WHITE);                   y += 22

    # Active alerts
    alerts = []
    if ph_count > 0:      alerts.append(f"POTHOLE x{ph_count}")
    if wt_count > 0:      alerts.append(f"WATERLOG x{wt_count}")
    if accidents > 0:     alerts.append(f"ACCIDENT x{accidents}")
    if htr_count > 0:     alerts.append(f"HIT&RUN x{htr_count}")
    if sign_alerts:       alerts.append(f"SIGN ERR x{len(sign_alerts)}")

    if alerts and y < h - 80:
        y = SH("!! ACTIVE ALERTS !!", y)
        for a in alerts:
            if y > h - 30: break
            T(f"  {a}", y, C_RED, bold=True); y += 18

    T("Smart India Hackathon | UrbanPulse v3", h-16, (70,70,70), 0.38)

    # Legend (bottom-right)
    lx, ly = w-230, h-105
    legends = [
        ("Vehicle",   C_GREEN),
        ("Obstacle",  C_YELLOW),
        ("Pothole",   C_RED),
        ("Waterlog",  C_BLUE),
        ("Accident",  C_MAGENTA),
        ("Sign",      C_PURPLE),
    ]
    ov3 = frame.copy()
    cv2.rectangle(ov3, (lx-6,ly-20), (w-4,h-4), (10,10,10), -1)
    cv2.addWeighted(ov3, 0.70, frame, 0.30, 0, frame)
    for i, (label, color) in enumerate(legends):
        yy = ly + i*17
        cv2.rectangle(frame, (lx,yy-2), (lx+13,yy+10), color, -1)
        cv2.putText(frame, label, (lx+17,yy+10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, C_WHITE, 1, cv2.LINE_AA)

# ══════════════════════════════════════════════════════════════════════
# OPEN VIDEO
# ══════════════════════════════════════════════════════════════════════

print(f"Video: {args.video}")
cap = cv2.VideoCapture(args.video)
if not cap.isOpened():
    print(f"ERROR: Cannot open: {args.video}")
    sys.exit(1)

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
vid_fps      = cap.get(cv2.CAP_PROP_FPS) or 30
print(f"  {total_frames} frames  |  {vid_fps:.0f} fps source")
print()
print("Press Q to quit the display window.")
print("Starting analysis...\n")

# Pre-create window so it appears before the first frame is ready
WIN_NAME = "UrbanPulse v3 — Urban Intelligence Platform"
if not args.headless:
    cv2.namedWindow(WIN_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_NAME, 1280, 720)
    cv2.moveWindow(WIN_NAME, 50, 50)

# ══════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════════════

while True:

    ret, frame = cap.read()
    if not ret: break

    frame_num += 1
    fps_f     += 1
    elapsed    = time.time() - fps_t
    if elapsed >= 1.0:
        fps   = fps_f / elapsed
        fps_f = 0
        fps_t = time.time()

    h, w = frame.shape[:2]
    loc  = gps.get_location()
    seg  = road_segment_id(loc)

    ph_count = S["ph_count"]
    wt_count = S["wt_count"]

    # ─────────────────────────────────────────────────────────────────
    # 1. VEHICLE DETECTION + TRACKING + VELOCITY
    # ─────────────────────────────────────────────────────────────────

    current_vehicles = {}   # tid → box
    current_persons  = {}   # tid → (cx, cy)

    if frame_num % VEHICLE_SKIP == 0:

        res = vehicle_model.track(frame, persist=True, tracker="bytetrack.yaml",
                                  verbose=False, imgsz=640, conf=VEHICLE_CONF)
        r   = res[0]

        if r.boxes is not None and r.boxes.id is not None:
            ids    = r.boxes.id.cpu().tolist()
            clses  = r.boxes.cls.cpu().tolist()
            bboxes = r.boxes.xyxy.cpu().tolist()
            counts = {"Car":0,"Motorcycle":0,"Bus":0,"Truck":0}
            total  = 0

            for tid, cls, box in zip(ids, clses, bboxes):
                cid = int(cls); tid = int(tid)
                x1,y1,x2,y2 = [int(v) for v in box]
                cx,cy = (x1+x2)//2, (y1+y2)//2

                if cid in VEHICLE_CLASSES:
                    vtype = VEHICLE_CLASSES[cid]
                    counts[vtype] += 1; total += 1
                    current_vehicles[tid] = [x1,y1,x2,y2]
                    if tid not in v_history: v_history[tid] = deque(maxlen=30)
                    v_history[tid].append((frame_num, cx, cy, [x1,y1,x2,y2]))
                    cv2.rectangle(frame, (x1,y1),(x2,y2), C_GREEN, 2)
                    spd = velocity(v_history[tid])
                    cv2.putText(frame, f"{vtype}#{tid} v={spd:.1f}",
                                (x1, max(y1-6,20)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.40, C_GREEN, 1, cv2.LINE_AA)

            vc      = counts; v_total = total
            density = ("HIGH"   if total >= DENSITY_HIGH
                       else "MEDIUM" if total >= DENSITY_MEDIUM
                       else "LOW")

    # ─────────────────────────────────────────────────────────────────
    # 2. ACCIDENT DETECTION (multi-condition velocity model)
    # ─────────────────────────────────────────────────────────────────

    if frame_num % VEHICLE_SKIP == 0 and len(current_vehicles) >= 2:

        vids   = list(current_vehicles.keys())
        vboxes = list(current_vehicles.values())

        for i in range(len(vids)):
            for j in range(i+1, len(vids)):
                pair   = (min(vids[i],vids[j]), max(vids[i],vids[j]))
                score  = iou_box(vboxes[i], vboxes[j])

                if score >= ACC_IOU_THRESH:
                    overlap_ctr[pair] = overlap_ctr.get(pair, 0) + 1
                else:
                    overlap_ctr[pair] = 0

                if (overlap_ctr.get(pair, 0) >= ACC_MIN_FRAMES
                        and frame_num - last_acc_frame > ACC_COOLDOWN):

                    # VELOCITY CONDITION: both vehicles must have been moving
                    vel_i = velocity(v_history.get(vids[i], deque()))
                    vel_j = velocity(v_history.get(vids[j], deque()))

                    # At least one must have been moving
                    if max(vel_i, vel_j) < ACC_VELOCITY_MIN:
                        overlap_ctr[pair] = 0
                        continue   # pure occlusion — skip

                    accidents          += 1
                    last_acc_frame      = frame_num
                    overlap_ctr[pair]   = 0

                    ev = {
                        "event_id": f"ACCIDENT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{accidents}",
                        "event_type": "ACCIDENT",
                        "bus_id": loc["bus_id"],
                        "latitude": loc["latitude"], "longitude": loc["longitude"],
                        "timestamp": loc["timestamp"],
                        "vehicles_involved": list(pair),
                        "overlap_iou": round(score,3),
                        "vel_v1": round(vel_i,2), "vel_v2": round(vel_j,2),
                        "frame": frame_num
                    }
                    acc_events.append(ev)
                    save_json(os.path.join(EVENT_DIR_ACCIDENT, ev["event_id"]+".json"), ev)
                    update_road_report(seg, loc, "ACCIDENT")
                    write_accident_state()
                    _post("ACCIDENT", loc, confidence=round(score,3), iou=round(score,3))

                    print(f"  🚨 ACCIDENT  frame={frame_num}"
                          f"  #{pair[0]}&#{pair[1]}"
                          f"  IoU={score:.2f}  v=({vel_i:.1f},{vel_j:.1f})")

                    bx1 = min(vboxes[i][0],vboxes[j][0])
                    by1 = min(vboxes[i][1],vboxes[j][1])
                    bx2 = max(vboxes[i][2],vboxes[j][2])
                    by2 = max(vboxes[i][3],vboxes[j][3])
                    cv2.rectangle(frame,(bx1,by1),(bx2,by2),C_MAGENTA,4)
                    cv2.putText(frame,"!! ACCIDENT !!",(bx1,max(by1-12,20)),
                                cv2.FONT_HERSHEY_SIMPLEX,0.75,C_MAGENTA,2,cv2.LINE_AA)

    # ─────────────────────────────────────────────────────────────────
    # 3. OBSTACLE DETECTION (persons, cyclists, animals)
    # ─────────────────────────────────────────────────────────────────

    if frame_num % OBSTACLE_SKIP == 0:

        ob_res = obstacle_model(frame, verbose=False, imgsz=640, conf=OBSTACLE_CONF)
        ob_r   = ob_res[0]
        ob_dets = []

        if ob_r.boxes is not None:
            ob_cls  = ob_r.boxes.cls.cpu().tolist()
            ob_bb   = ob_r.boxes.xyxy.cpu().tolist()
            ob_conf = ob_r.boxes.conf.cpu().tolist()

            for cid, box, conf in zip(ob_cls, ob_bb, ob_conf):
                cid = int(cid)
                if cid not in OBSTACLE_CLASSES: continue
                x1,y1,x2,y2 = [int(v) for v in box]
                cx,cy = (x1+x2)//2, (y1+y2)//2
                label = OBSTACLE_CLASSES[cid]

                # Sign classes handled separately
                if cid in SIGN_CLASSES:
                    if OCR_ENABLED and frame_num % SIGN_SKIP == 0:
                        crop  = frame[max(0,y1):y2, max(0,x1):x2]
                        if crop.size > 0:
                            ocr_results = ocr_reader.readtext(crop)
                            for _, text, oconf in ocr_results:
                                text = text.upper().strip()
                                expected = GIS_SIGNS.get(seg, [])
                                matched  = any(text in e or e in text for e in expected)
                                if not matched and len(text) > 3:
                                    sign_alerts.append({
                                        "frame": frame_num, "text": text,
                                        "segment": seg, "conf": round(float(oconf),2)
                                    })
                                    update_road_report(seg, loc, "SIGN_ISSUE")
                                    print(f"  🪧 SIGN TEXT '{text}' not in GIS for {seg}")
                                cv2.putText(frame, f"OCR: {text}",
                                            (x1, max(y1-22, 20)),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                                            C_PURPLE, 1, cv2.LINE_AA)
                    cv2.rectangle(frame,(x1,y1),(x2,y2),C_PURPLE,2)
                    cv2.putText(frame, label, (x1, max(y1-6,20)),
                                cv2.FONT_HERSHEY_SIMPLEX,0.42,C_PURPLE,1,cv2.LINE_AA)
                    continue

                ob_dets.append({
                    "box": [x1,y1,x2,y2], "conf": float(conf),
                    "center": (cx,cy), "label": label
                })

                # Track persons for hit-and-run
                if cid == 0:
                    if not hasattr(ob_r, "_person_idx"): ob_r._person_idx = 0
                    current_persons[id(box)] = (cx, cy)

        # Match obstacle detections to tracks
        matched = set()
        for det in ob_dets:
            cx, cy = det["center"]
            best_id, best_d = None, float("inf")
            for oid, ot in obstacles.items():
                if oid in matched: continue
                d = cdist((cx,cy), ot["center"])
                if d < best_d: best_d, best_id = d, oid

            if best_id is not None and best_d <= OBSTACLE_MAX_DIST:
                ot = obstacles[best_id]
                ot["center"]     = det["center"]
                ot["box"]        = det["box"]
                ot["conf"]       = max(ot["conf"], det["conf"])
                ot["frames"]    += 1
                ot["last_frame"] = frame_num
                ot["label"]      = det["label"]
                matched.add(best_id)
            else:
                obstacles[S["ob_next"]] = {
                    "center": det["center"], "box": det["box"],
                    "conf": det["conf"], "frames": 1,
                    "last_frame": frame_num, "confirmed": False,
                    "label": det["label"]
                }
                S["ob_next"] += 1

        # Expire stale
        for oid in [o for o,ot in obstacles.items()
                    if frame_num - ot["last_frame"] > 20]:
            del obstacles[oid]

        # Confirm
        for oid, ot in list(obstacles.items()):
            if ot["frames"] >= OBSTACLE_CONFIRM and not ot["confirmed"]:
                ot["confirmed"] = True
                S["ob_count"]  += 1
                ev = {
                    "event_id":    f"OBSTACLE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{oid}",
                    "event_type":  "OBSTACLE",
                    "label":       ot["label"],
                    "bus_id":      loc["bus_id"],
                    "latitude":    loc["latitude"], "longitude": loc["longitude"],
                    "timestamp":   loc["timestamp"],
                    "confidence":  round(ot["conf"],3), "frame": frame_num
                }
                save_json(os.path.join(EVENT_DIR_OBSTACLE, ev["event_id"]+".json"), ev)
                update_road_report(seg, loc, "OBSTACLE")
                _post("OBSTACLE", loc, confidence=round(ot["conf"],3), label=ot["label"])
                print(f"  🚧 OBSTACLE '{ot['label']}'  frame={frame_num}  conf={ot['conf']:.2f}")

        # Draw obstacle boxes
        for oid, ot in obstacles.items():
            x1,y1,x2,y2 = ot["box"]
            col = C_YELLOW if ot["confirmed"] else C_ORANGE
            cv2.rectangle(frame,(x1,y1),(x2,y2),col,2)
            cv2.putText(frame, f"{ot['label']} #{oid}",
                        (x1,max(y1-6,20)), cv2.FONT_HERSHEY_SIMPLEX,
                        0.42,col,1,cv2.LINE_AA)

    # ─────────────────────────────────────────────────────────────────
    # 4. HIT-AND-RUN DETECTION
    # ─────────────────────────────────────────────────────────────────
    # A person was near a fast vehicle → person disappears → vehicle accelerates

    if frame_num % VEHICLE_SKIP == 0:
        for tid, box in current_vehicles.items():
            bx = [(box[0]+box[2])//2, (box[1]+box[3])//2]
            for pid, (px,py) in current_persons.items():
                dist = cdist(bx, [px,py])
                if dist < HTR_PROX_THRESH:
                    htr_candidates[pid] = {
                        "last_frame":      frame_num,
                        "near_vehicle":    tid,
                        "vehicle_vel_then":velocity(v_history.get(tid, deque()))
                    }

        # Check if candidates' persons have disappeared
        expired_candidates = []
        for pid, info in htr_candidates.items():
            frames_since = frame_num - info["last_frame"]
            if frames_since > HTR_DISAPPEAR_WIN:
                # Person gone — check vehicle acceleration
                vtid  = info["near_vehicle"]
                vel_now = velocity(v_history.get(vtid, deque()))
                vel_was = info["vehicle_vel_then"]
                if vel_now - vel_was > HTR_ACCEL_THRESH:
                    htr_count += 1
                    ev = {
                        "event_id":   f"HTR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{htr_count}",
                        "event_type": "HIT_AND_RUN",
                        "bus_id":     loc["bus_id"],
                        "latitude":   loc["latitude"], "longitude": loc["longitude"],
                        "timestamp":  loc["timestamp"],
                        "vehicle_id": vtid, "acceleration": round(vel_now-vel_was,2),
                        "frame":      frame_num
                    }
                    save_json(os.path.join(EVENT_DIR_ACCIDENT, ev["event_id"]+".json"), ev)
                    update_road_report(seg, loc, "HTR")
                    write_accident_state()
                    _post("HTR", loc, confidence=0.85)
                    print(f"  🏃 HIT-AND-RUN  frame={frame_num}  vehicle=#{vtid}"
                          f"  accel={vel_now-vel_was:.1f}")
                expired_candidates.append(pid)

        for pid in expired_candidates:
            htr_candidates.pop(pid, None)

    # ─────────────────────────────────────────────────────────────────
    # 5. POTHOLE DETECTION + GPS REPORT
    # ─────────────────────────────────────────────────────────────────

    if frame_num % POTHOLE_SKIP == 0:
        p_res = pothole_model(frame, verbose=False, imgsz=640, conf=POTHOLE_CONF)
        p_dets = []
        if p_res[0].boxes is not None:
            pb = p_res[0].boxes.xyxy.cpu().tolist()
            pc = p_res[0].boxes.conf.cpu().tolist()
            for box, conf in zip(pb, pc):
                x1,y1,x2,y2 = [int(v) for v in box]
                p_dets.append({
                    "box": [x1,y1,x2,y2], "conf": float(conf),
                    "center": ((x1+x2)//2,(y1+y2)//2)
                })

        matched = set()
        for det in p_dets:
            cx,cy = det["center"]
            best_id, best_d = None, float("inf")
            for pid,ph in potholes.items():
                if pid in matched: continue
                d = cdist((cx,cy), ph["center"])
                if d < best_d: best_d,best_id = d,pid

            if best_id is not None and best_d <= POTHOLE_MAX_DIST:
                ph = potholes[best_id]
                ph["center"] = det["center"]; ph["box"] = det["box"]
                ph["conf"]   = max(ph["conf"], det["conf"])
                ph["frames"] += 1; ph["last_frame"] = frame_num
                matched.add(best_id)
            else:
                potholes[S["ph_next"]] = {
                    "center": det["center"], "box": det["box"],
                    "conf": det["conf"], "frames": 1,
                    "last_frame": frame_num, "confirmed": False
                }
                S["ph_next"] += 1

        for pid in [p for p,ph in potholes.items()
                    if frame_num - ph["last_frame"] > 18]:
            del potholes[pid]

        for pid, ph in list(potholes.items()):
            if ph["frames"] >= POTHOLE_CONFIRM and not ph["confirmed"]:
                ph["confirmed"] = True
                S["ph_count"]  += 1
                eid = f"POTHOLE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{pid}"
                ev  = {
                    "event_id": eid, "event_type": "POTHOLE",
                    "bus_id":   loc["bus_id"],
                    "latitude": loc["latitude"], "longitude": loc["longitude"],
                    "timestamp":loc["timestamp"],
                    "confidence":  round(ph["conf"],3),
                    "confirmation_frames": ph["frames"],
                    "video":    os.path.basename(args.video),
                    "frame":    frame_num,
                    "road_segment": seg
                }
                save_json(os.path.join(EVENT_DIR_POTHOLE, eid+".json"), ev)
                update_road_report(seg, loc, "POTHOLE")
                write_pothole_state()
                _post("POTHOLE", loc, confidence=round(ph["conf"],3), road_segment=seg)
                print(f"  ⚠️  POTHOLE #{pid}  frame={frame_num}"
                      f"  conf={ph['conf']:.2f}  GPS={loc['latitude']:.4f},{loc['longitude']:.4f}"
                      f"  road={seg}")

        ph_count = S["ph_count"]

        for pid,ph in potholes.items():
            x1,y1,x2,y2 = ph["box"]
            col = C_RED if ph["confirmed"] else C_ORANGE
            lw  = 3 if ph["confirmed"] else 2
            conf_pct = int(ph["conf"]*100)
            lbl = (f"POTHOLE {conf_pct}%" if ph["confirmed"]
                   else f"? {ph['frames']}/{POTHOLE_CONFIRM}")
            cv2.rectangle(frame,(x1,y1),(x2,y2),col,lw)
            cv2.putText(frame, lbl, (x1,max(y1-6,20)),
                        cv2.FONT_HERSHEY_SIMPLEX,0.48,col,2,cv2.LINE_AA)

    # ─────────────────────────────────────────────────────────────────
    # 6. WATERLOGGING DETECTION
    # ─────────────────────────────────────────────────────────────────

    if frame_num % WATER_SKIP == 0:
        w_dets  = detect_waterlogging(frame)
        matched_w = set()

        for det in w_dets:
            cx,cy = det["center"]
            best_id, best_d = None, float("inf")
            for wid,wt in waters.items():
                if wid in matched_w: continue
                d = cdist((cx,cy), wt["center"])
                if d < best_d: best_d,best_id = d,wid

            if best_id is not None and best_d <= WATER_MAX_DIST:
                wt = waters[best_id]
                wt["center"] = det["center"]; wt["box"] = det["box"]
                wt["conf"]   = max(wt["conf"], det["conf"])
                wt["frames"] += 1; wt["last_frame"] = frame_num
                matched_w.add(best_id)
            else:
                waters[S["wt_next"]] = {
                    "center": det["center"], "box": det["box"],
                    "conf": det["conf"], "frames": 1,
                    "last_frame": frame_num, "confirmed": False
                }
                S["wt_next"] += 1

        for wid in [w for w,wt in waters.items()
                    if frame_num - wt["last_frame"] > 25]:
            del waters[wid]

        for wid, wt in list(waters.items()):
            if wt["frames"] >= WATER_CONFIRM and not wt["confirmed"]:
                wt["confirmed"] = True
                S["wt_count"]  += 1
                eid = f"WATER-{datetime.now().strftime('%Y%m%d%H%M%S')}-{wid}"
                ev  = {
                    "event_id": eid, "event_type": "WATERLOGGING",
                    "bus_id":   loc["bus_id"],
                    "latitude": loc["latitude"], "longitude": loc["longitude"],
                    "timestamp":loc["timestamp"],
                    "confidence": round(wt["conf"],3),
                    "confirmation_frames": wt["frames"],
                    "video":  os.path.basename(args.video),
                    "frame":  frame_num, "road_segment": seg
                }
                save_json(os.path.join(EVENT_DIR_WATER, eid+".json"), ev)
                update_road_report(seg, loc, "WATERLOGGING")
                write_water_state()
                _post("WATERLOGGING", loc, confidence=round(wt["conf"],3), road_segment=seg)
                print(f"  🌊 WATERLOGGING #{wid}  frame={frame_num}"
                      f"  conf={wt['conf']:.2f}  road={seg}")

        wt_count = S["wt_count"]

        for wid,wt in waters.items():
            x1,y1,x2,y2 = wt["box"]
            lw  = 3 if wt["confirmed"] else 2
            lbl = f"WATERLOG {int(wt['conf']*100)}%" if wt["confirmed"] else f"Water? {wt['frames']}/{WATER_CONFIRM}"
            cv2.rectangle(frame,(x1,y1),(x2,y2),C_BLUE,lw)
            cv2.putText(frame,lbl,(x1,max(y1-6,20)),
                        cv2.FONT_HERSHEY_SIMPLEX,0.45,C_BLUE,2,cv2.LINE_AA)

    # ─────────────────────────────────────────────────────────────────
    # 7. PERIODIC STATE + LIVE WRITES
    # ─────────────────────────────────────────────────────────────────

    if frame_num - state_tick >= STATE_EVERY:
        write_traffic_state()
        write_road_priority_state()
        state_tick = frame_num

    if frame_num - live_tick >= LIVE_EVERY:
        write_live_state()
        live_tick = frame_num

    # ─────────────────────────────────────────────────────────────────
    # 8. HUD + DISPLAY
    # ─────────────────────────────────────────────────────────────────

    draw_hud(frame, h, w, ph_count, wt_count)

    if not args.headless:
        display_frame = cv2.resize(frame, (960, 540))
        cv2.imshow(WIN_NAME, display_frame)
        if cv2.waitKey(30) & 0xFF == ord("q"):
            print("\nStopped by user.")
            break

    if frame_num % 100 == 0:
        print(f"  Frame {frame_num}/{total_frames}"
              f"  | V:{v_total} D:{density}"
              f"  | P:{S['ph_count']} W:{S['wt_count']} Ob:{S['ob_count']}"
              f"  | Acc:{accidents} HTR:{htr_count}"
              f"  | Roads:{len(road_reports)}"
              f"  | FPS:{fps:.1f}")

# ══════════════════════════════════════════════════════════════════════
# CLEANUP
# ══════════════════════════════════════════════════════════════════════

cap.release()
if not args.headless:
    cv2.destroyAllWindows()

print("\nWriting final state files...")
write_traffic_state()
write_pothole_state()
write_water_state()
write_accident_state()
write_road_priority_state()
write_live_state()

# ══════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ══════════════════════════════════════════════════════════════════════

loc = gps.get_location()
print()
print("╔══════════════════════════════════════════════════════════════╗")
print("║           URBANPULSE v3 — ANALYSIS COMPLETE                 ║")
print("╠══════════════════════════════════════════════════════════════╣")
print(f"║  Video    : {os.path.basename(args.video):<50}║")
print(f"║  Frames   : {frame_num:<50}║")
print("╠══════════════════════════════════════════════════════════════╣")
print(f"║  TRAFFIC      Vehicles: {v_total:<5} Density: {density:<21}║")
print(f"║  OBSTACLES    Confirmed: {S['ob_count']:<37}║")
print(f"║  POTHOLES     Confirmed: {S['ph_count']:<37}║")
print(f"║  WATERLOGGING Confirmed: {S['wt_count']:<37}║")
print(f"║  ACCIDENTS    Detected:  {accidents:<37}║")
print(f"║  HIT-AND-RUN  Detected:  {htr_count:<37}║")
print(f"║  SIGN ISSUES  Detected:  {len(sign_alerts):<37}║")
print("╠══════════════════════════════════════════════════════════════╣")
print(f"║  ROAD REPORTS  Total roads tracked: {len(road_reports):<26}║")

# Top 3 priority roads
sorted_roads = sorted(road_reports.values(),
                      key=lambda r: r["priority_score"], reverse=True)
for i, r in enumerate(sorted_roads[:3], 1):
    print(f"║    #{i} {r['segment_id']:<15} Score:{r['priority_score']:<5} {r['priority_level']:<20}║")

print("╚══════════════════════════════════════════════════════════════╝")

issues = []
if S["ph_count"] > 0:  issues.append(f"Pothole x{S['ph_count']}")
if S["wt_count"] > 0:  issues.append(f"Waterlogging x{S['wt_count']}")
if accidents     > 0:  issues.append(f"Accident x{accidents}")
if htr_count     > 0:  issues.append(f"Hit-and-Run x{htr_count}")
if sign_alerts:        issues.append(f"Sign Issues x{len(sign_alerts)}")

if issues:
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         🚨  MAINTENANCE / RESPONSE REQUIRED                 ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    for iss in issues:
        print(f"║  ▸ {iss:<58}║")
    print(f"║  Bus: {loc['bus_id']:<56}║")
    print(f"║  GPS: {loc['latitude']}, {loc['longitude']:<43}║")
    print("╚══════════════════════════════════════════════════════════════╝")

print()
print("State files → UrbanPulse/prototype/state/")
print("Road reports → UrbanPulse/reports/")
print("Dashboard   → streamlit run UrbanPulse/prototype/dashboard.py")
print()
