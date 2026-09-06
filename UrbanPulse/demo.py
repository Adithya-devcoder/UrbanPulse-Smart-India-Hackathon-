import cv2
import os
import sys
import json
import math
import glob
from datetime import datetime
from ultralytics import YOLO

# Make phase2 imports available
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "phase2", "pothole"))
from location_provider import LocationProvider

BASE = "UrbanPulse"

VIDEO_DIR = f"{BASE}/phase1/videos"
VEHICLE_MODEL = f"{BASE}/models/vehicle/yolo11n.pt"
POTHOLE_MODEL = f"{BASE}/models/pothole/best.pt"

VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

print("=" * 50)
print("          URBANPULSE DEMO")
print("=" * 50)

print("Loading models...")

vehicle_model = YOLO(VEHICLE_MODEL)
pothole_model = YOLO(POTHOLE_MODEL)

print("Models loaded successfully.")


# ==================================================
# PHASE 1 - TRAFFIC
# ==================================================

video1 = f"{VIDEO_DIR}/traffic1.mp4"

print()
print("=" * 50)
print("PHASE 1 - TRAFFIC INTELLIGENCE")
print("=" * 50)

cap = cv2.VideoCapture(video1)

if not cap.isOpened():
    print("ERROR: Cannot open traffic1.mp4")
    exit()

max_vehicles = 0

final_counts = {
    "Car": 0,
    "Motorcycle": 0,
    "Bus": 0,
    "Truck": 0
}

frame_number = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    # Process every 2nd frame for speed
    if frame_number % 2 != 0:
        continue

    results = vehicle_model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False,
        imgsz=640
    )

    result = results[0]

    vehicle_count = 0

    current_counts = {
        "Car": 0,
        "Motorcycle": 0,
        "Bus": 0,
        "Truck": 0
    }

    if result.boxes is not None:

        for cls in result.boxes.cls:

            class_id = int(cls.item())

            if class_id in VEHICLE_CLASSES:

                vehicle_type = VEHICLE_CLASSES[class_id]

                vehicle_count += 1

                current_counts[vehicle_type] += 1

    if vehicle_count > max_vehicles:

        max_vehicles = vehicle_count
        final_counts = current_counts.copy()

    if vehicle_count >= 15:
        density = "HIGH"
    elif vehicle_count >= 7:
        density = "MEDIUM"
    else:
        density = "LOW"

    annotated = result.plot()

    cv2.putText(
        annotated,
        "URBANPULSE - PHASE 1",
        (30, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.putText(
        annotated,
        f"Vehicles: {vehicle_count}",
        (30, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.putText(
        annotated,
        f"Traffic Density: {density}",
        (30, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.imshow(
        "UrbanPulse - Phase 1",
        annotated
    )

    # Q only stops the complete demo
    if cv2.waitKey(1) & 0xFF == ord("q"):
        cap.release()
        cv2.destroyAllWindows()
        exit()


cap.release()
cv2.destroyAllWindows()

print("PHASE 1 COMPLETE")
print("Maximum vehicles:", max_vehicles)
print("Final vehicle breakdown:", final_counts)


# ==================================================
# SAVE TRAFFIC DATA FOR DASHBOARD
# ==================================================

state_dir = f"{BASE}/prototype/state"

os.makedirs(state_dir, exist_ok=True)

traffic_state = {
    "vehicles": max_vehicles,
    "density": density,
    "cars": final_counts["Car"],
    "motorcycles": final_counts["Motorcycle"],
    "buses": final_counts["Bus"],
    "trucks": final_counts["Truck"]
}

with open(
    f"{state_dir}/traffic_state.json",
    "w"
) as f:

    json.dump(
        traffic_state,
        f,
        indent=4
    )

print("Traffic state saved to dashboard.")


# ==================================================
# PHASE 2 - POTHOLES
# ==================================================

video2 = f"{VIDEO_DIR}/traffic2.mp4"

print()
print("=" * 50)
print("PHASE 2 - POTHOLE INTELLIGENCE")
print("=" * 50)

cap = cv2.VideoCapture(video2)

if not cap.isOpened():
    print("ERROR: Cannot open traffic2.mp4")
    exit()

# Location / GPS provider
gps = LocationProvider()

# Event output directory
event_dir = f"{BASE}/phase2/pothole/events"
os.makedirs(event_dir, exist_ok=True)

# Pothole tracking state
potholes = {}        # pothole_id -> tracking dict
next_id = 1
confirmed = 0
frame_number = 0

MAX_DISTANCE   = 100   # pixels — same pothole if center moves less than this
REQUIRED_FRAMES = 3    # frames needed to confirm

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1

    # Process every 2nd frame for speed
    if frame_number % 2 != 0:
        continue

    results = pothole_model(
        frame,
        verbose=False,
        imgsz=640
    )

    result = results[0]

    # ----------------------------------------
    # Extract detections this frame
    # ----------------------------------------
    detections = []

    if result.boxes is not None:

        boxes       = result.boxes.xyxy.cpu().tolist()
        confidences = result.boxes.conf.cpu().tolist()

        for box, conf in zip(boxes, confidences):

            if conf < 0.50:
                continue

            x1, y1, x2, y2 = box
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            detections.append({
                "box":        [int(x1), int(y1), int(x2), int(y2)],
                "confidence": float(conf),
                "center":     (cx, cy)
            })

    # ----------------------------------------
    # Match detections → existing potholes
    # ----------------------------------------
    matched_ids = set()

    for det in detections:

        cx, cy = det["center"]
        best_id   = None
        best_dist = float("inf")

        for pid, ph in potholes.items():

            if pid in matched_ids:
                continue

            px, py = ph["center"]
            dist = math.sqrt((cx - px) ** 2 + (cy - py) ** 2)

            if dist < best_dist:
                best_dist = dist
                best_id   = pid

        if best_id is not None and best_dist <= MAX_DISTANCE:

            ph = potholes[best_id]
            ph["center"]     = (cx, cy)
            ph["box"]        = det["box"]
            ph["confidence"] = max(ph["confidence"], det["confidence"])
            ph["frames"]    += 1
            ph["last_frame"] = frame_number
            matched_ids.add(best_id)

        else:

            potholes[next_id] = {
                "center":     (cx, cy),
                "box":        det["box"],
                "confidence": det["confidence"],
                "frames":     1,
                "last_frame": frame_number,
                "confirmed":  False
            }
            next_id += 1

    # ----------------------------------------
    # Remove stale tracks
    # ----------------------------------------
    stale = [pid for pid, ph in potholes.items()
             if frame_number - ph["last_frame"] > 10]
    for pid in stale:
        del potholes[pid]

    # ----------------------------------------
    # Confirm potholes + save events
    # ----------------------------------------
    for pid, ph in potholes.items():

        if ph["frames"] >= REQUIRED_FRAMES and not ph["confirmed"]:

            ph["confirmed"] = True
            confirmed      += 1

            location = gps.get_location()

            event_id = (
                f"POTHOLE-"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}-"
                f"{pid}"
            )

            event = {
                "event_id":           event_id,
                "event_type":         "POTHOLE",
                "bus_id":             location["bus_id"],
                "latitude":           location["latitude"],
                "longitude":          location["longitude"],
                "timestamp":          location["timestamp"],
                "confidence":         round(ph["confidence"], 3),
                "confirmation_frames": ph["frames"],
                "video":              os.path.basename(video2),
                "frame":              frame_number
            }

            event_file = os.path.join(event_dir, event_id + ".json")

            with open(event_file, "w") as f:
                json.dump(event, f, indent=4)

            print(
                f"CONFIRMED POTHOLE #{pid} "
                f"at frame {frame_number} "
                f"(confidence: {ph['confidence']:.2f}) "
                f"→ event saved"
            )

            # ---- Update pothole_state.json live so dashboard refreshes ---
            all_events = []
            for ef in glob.glob(os.path.join(event_dir, "POTHOLE-*.json")):
                try:
                    with open(ef) as ef_f:
                        all_events.append(json.load(ef_f))
                except Exception:
                    pass

            # Sort by timestamp, newest last
            all_events.sort(key=lambda e: e.get("timestamp", ""))

            latest = all_events[-1] if all_events else event

            pothole_state = {
                "potholes":    len(all_events),
                "status":      "POTHOLES DETECTED",
                "bus_id":      latest["bus_id"],
                "latitude":    latest["latitude"],
                "longitude":   latest["longitude"],
                "timestamp":   latest["timestamp"],
                "confidence":  latest["confidence"],
                "video":       latest["video"],
                "frame":       latest["frame"],
                "event_id":    latest["event_id"],
                "all_locations": [
                    {
                        "lat": e["latitude"],
                        "lon": e["longitude"],
                        "confidence": e["confidence"]
                    }
                    for e in all_events
                ]
            }

            with open(f"{state_dir}/pothole_state.json", "w") as f:
                json.dump(pothole_state, f, indent=4)

    # ----------------------------------------
    # Draw results on frame
    # ----------------------------------------
    annotated = result.plot()

    cv2.putText(
        annotated,
        "URBANPULSE - PHASE 2",
        (30, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2
    )

    cv2.putText(
        annotated,
        f"Confirmed Potholes: {confirmed}",
        (30, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )

    cv2.imshow(
        "UrbanPulse - Phase 2",
        annotated
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()


# ==================================================
# WRITE FINAL POTHOLE STATE (in case none confirmed
# during loop, or to ensure file always exists)
# ==================================================

all_events = []
for ef in glob.glob(os.path.join(event_dir, "POTHOLE-*.json")):
    try:
        with open(ef) as ef_f:
            all_events.append(json.load(ef_f))
    except Exception:
        pass

all_events.sort(key=lambda e: e.get("timestamp", ""))

if all_events:
    latest = all_events[-1]
    pothole_state = {
        "potholes":    len(all_events),
        "status":      "POTHOLES DETECTED",
        "bus_id":      latest["bus_id"],
        "latitude":    latest["latitude"],
        "longitude":   latest["longitude"],
        "timestamp":   latest["timestamp"],
        "confidence":  latest["confidence"],
        "video":       latest["video"],
        "frame":       latest["frame"],
        "event_id":    latest["event_id"],
        "all_locations": [
            {
                "lat": e["latitude"],
                "lon": e["longitude"],
                "confidence": e["confidence"]
            }
            for e in all_events
        ]
    }
else:
    pothole_state = {
        "potholes":    0,
        "status":      "NO POTHOLES DETECTED",
        "bus_id":      gps.get_location()["bus_id"],
        "latitude":    gps.get_location()["latitude"],
        "longitude":   gps.get_location()["longitude"],
        "timestamp":   gps.get_location()["timestamp"],
        "confidence":  0,
        "video":       os.path.basename(video2),
        "frame":       frame_number,
        "event_id":    "",
        "all_locations": []
    }

with open(f"{state_dir}/pothole_state.json", "w") as f:
    json.dump(pothole_state, f, indent=4)

print("Pothole state saved to dashboard.")


# ==================================================
# MAINTENANCE ALERT
# ==================================================

if pothole_state["potholes"] > 0:
    print()
    print("=" * 50)
    print("  🚨  ROAD MAINTENANCE REQUIRED")
    print("=" * 50)
    print(f"  Issue:      Pothole")
    print(f"  Count:      {pothole_state['potholes']} confirmed")
    print(f"  Bus:        {pothole_state['bus_id']}")
    print(f"  Confidence: {pothole_state['confidence'] * 100:.0f}%")
    print(f"  Location:   {pothole_state['latitude']}, {pothole_state['longitude']}")
    print("=" * 50)


# ==================================================
# FINAL REPORT
# ==================================================

print()
print("=" * 50)
print("       URBANPULSE DEMO COMPLETE")
print("=" * 50)

print()
print("TRAFFIC")
print("--------------------------------")
print("Maximum vehicles:", max_vehicles)
print("Density:", density)
print("Cars:", final_counts["Car"])
print("Motorcycles:", final_counts["Motorcycle"])
print("Buses:", final_counts["Bus"])
print("Trucks:", final_counts["Truck"])

print()
print("ROAD CONDITION")
print("--------------------------------")
print("Confirmed potholes:", pothole_state["potholes"])
print("Dashboard state: UrbanPulse/prototype/state/pothole_state.json")

print()
print("LOCATION")
print("--------------------------------")
print("Bus ID:   ", pothole_state["bus_id"])
print("Latitude: ", pothole_state["latitude"])
print("Longitude:", pothole_state["longitude"])

print()
print("=" * 50)
