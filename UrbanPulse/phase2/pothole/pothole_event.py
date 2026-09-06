from ultralytics import YOLO
import cv2
import math
import json
import os
from datetime import datetime

from location_provider import LocationProvider


# ==========================================
# Configuration
# ==========================================

MODEL_PATH = "../../models/pothole/best.pt"
VIDEO_PATH = "../../phase1/videos/traffic2.mp4"

CONFIDENCE_THRESHOLD = 0.60
REQUIRED_FRAMES = 3
MAX_DISTANCE = 100

OUTPUT_DIR = "events"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==========================================
# Load model and GPS provider
# ==========================================

print("Loading pothole model...")

model = YOLO(MODEL_PATH)

gps = LocationProvider()

print("Pothole model loaded")
print("GPS/AVL provider loaded")


# ==========================================
# Open video
# ==========================================

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print("ERROR: Could not open video")
    exit()


# ==========================================
# Pothole tracking state
# ==========================================

potholes = {}

next_id = 1

confirmed_count = 0

frame_number = 0


# ==========================================
# Process video
# ==========================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_number += 1


    # ======================================
    # YOLO detection
    # ======================================

    results = model(
        frame,
        device=0,
        conf=CONFIDENCE_THRESHOLD,
        verbose=False
    )


    detections = []


    if results[0].boxes is not None:

        boxes = results[0].boxes.xyxy.cpu().tolist()

        confidences = results[0].boxes.conf.cpu().tolist()


        for box, confidence in zip(boxes, confidences):

            x1, y1, x2, y2 = box

            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)


            detections.append({

                "box": [
                    int(x1),
                    int(y1),
                    int(x2),
                    int(y2)
                ],

                "confidence": float(confidence),

                "center": (
                    center_x,
                    center_y
                )
            })


    # ======================================
    # Match detections
    # ======================================

    matched_ids = set()


    for detection in detections:

        center = detection["center"]

        best_id = None

        best_distance = float("inf")


        for pothole_id, pothole in potholes.items():

            if pothole_id in matched_ids:
                continue


            previous_center = pothole["center"]


            distance = math.sqrt(

                (center[0] - previous_center[0]) ** 2
                +
                (center[1] - previous_center[1]) ** 2
            )


            if distance < best_distance:

                best_distance = distance
                best_id = pothole_id


        # ==================================
        # Existing pothole
        # ==================================

        if (
            best_id is not None
            and best_distance <= MAX_DISTANCE
        ):

            pothole = potholes[best_id]

            pothole["center"] = center

            pothole["box"] = detection["box"]

            pothole["confidence"] = max(
                pothole["confidence"],
                detection["confidence"]
            )

            pothole["frames"] += 1

            pothole["last_frame"] = frame_number

            matched_ids.add(best_id)


        # ==================================
        # New pothole
        # ==================================

        else:

            potholes[next_id] = {

                "center": center,

                "box": detection["box"],

                "confidence": detection["confidence"],

                "frames": 1,

                "last_frame": frame_number,

                "confirmed": False
            }

            next_id += 1


    # ======================================
    # Remove old detections
    # ======================================

    remove_ids = []


    for pothole_id, pothole in potholes.items():

        if frame_number - pothole["last_frame"] > 10:

            remove_ids.append(pothole_id)


    for pothole_id in remove_ids:

        del potholes[pothole_id]


    # ======================================
    # Confirm potholes
    # ======================================

    for pothole_id, pothole in potholes.items():

        if (
            pothole["frames"] >= REQUIRED_FRAMES
            and not pothole["confirmed"]
        ):

            pothole["confirmed"] = True

            confirmed_count += 1


            # ==================================
            # Get GPS / AVL location
            # ==================================

            location = gps.get_location()


            # ==================================
            # Create event
            # ==================================

            event = {

                "event_id":
                    f"POTHOLE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{pothole_id}",

                "event_type":
                    "POTHOLE",

                "bus_id":
                    location["bus_id"],

                "latitude":
                    location["latitude"],

                "longitude":
                    location["longitude"],

                "timestamp":
                    location["timestamp"],

                "confidence":
                    round(
                        pothole["confidence"],
                        3
                    ),

                "confirmation_frames":
                    pothole["frames"],

                "video":
                    os.path.basename(VIDEO_PATH),

                "frame":
                    frame_number
            }


            # ==================================
            # Save event
            # ==================================

            event_file = os.path.join(

                OUTPUT_DIR,

                event["event_id"] + ".json"
            )


            with open(
                event_file,
                "w"
            ) as f:

                json.dump(
                    event,
                    f,
                    indent=4
                )


            print()
            print("=" * 55)
            print("CONFIRMED POTHOLE EVENT")
            print("=" * 55)

            print(
                json.dumps(
                    event,
                    indent=4
                )
            )

            print("=" * 55)


    # ======================================
    # Draw results
    # ======================================

    annotated_frame = frame.copy()


    for pothole_id, pothole in potholes.items():

        x1, y1, x2, y2 = pothole["box"]


        if pothole["confirmed"]:

            label = (

                f"POTHOLE #{pothole_id} "
                f"CONFIRMED "
                f"{pothole['confidence']:.2f}"
            )

        else:

            label = (

                f"Checking "
                f"{pothole['frames']}/"
                f"{REQUIRED_FRAMES}"
            )


        cv2.rectangle(

            annotated_frame,

            (x1, y1),

            (x2, y2),

            (0, 255, 0),

            3
        )


        cv2.putText(

            annotated_frame,

            label,

            (x1, max(y1 - 10, 20)),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.6,

            (0, 255, 0),

            2
        )


    # ======================================
    # Display information
    # ======================================

    location = gps.get_location()


    cv2.putText(

        annotated_frame,

        f"Bus: {location['bus_id']}",

        (30, 40),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.7,

        (255, 255, 255),

        2
    )


    cv2.putText(

        annotated_frame,

        f"GPS: {location['latitude']:.5f}, "
        f"{location['longitude']:.5f}",

        (30, 75),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2
    )


    cv2.putText(

        annotated_frame,

        f"Confirmed: {confirmed_count}",

        (30, 110),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.7,

        (0, 255, 255),

        2
    )


    cv2.imshow(

        "UrbanPulse - Pothole Intelligence",

        annotated_frame
    )


    # ======================================
    # Quit
    # ======================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# ==========================================
# Cleanup
# ==========================================

cap.release()

cv2.destroyAllWindows()


print()
print("=" * 55)
print("POTHOLE PROCESSING COMPLETE")
print("=" * 55)

print(
    f"Confirmed potholes: {confirmed_count}"
)

print(
    f"Events saved to: {OUTPUT_DIR}"
)
