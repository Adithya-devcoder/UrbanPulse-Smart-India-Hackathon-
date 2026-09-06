import cv2

from detection.vehicle_detector import VehicleDetector
from tracking.vehicle_tracker import VehicleTracker
from counting.vehicle_counter import VehicleCounter
from counting.traffic_density import TrafficDensity

# ==========================================
# Configuration
# ==========================================

VIDEO_PATHS = [
    "UrbanPulse/phase1/videos/traffic1.mp4",
    "UrbanPulse/phase1/videos/traffic2.mp4"
]


# ==========================================
# Initialize modules
# ==========================================

print("Initializing UrbanPulse...")

detector = VehicleDetector()
tracker = VehicleTracker()
counter = VehicleCounter(line_position=0.60)
density = TrafficDensity()

print("Vehicle detection initialized")
print("Vehicle tracking initialized")
print("Vehicle counting initialized")
print("Traffic density initialized")


# ==========================================
# Open video
# ==========================================

video_index = 0

cap = cv2.VideoCapture(VIDEO_PATHS[video_index])

if not cap.isOpened():
    print("ERROR: Could not open video:")
    print(VIDEO_PATHS[video_index])
    exit()
# ==========================================
# Process video
# ==========================================

while True:

    ret, frame = cap.read()

    if not ret:

        cap.release()

        video_index += 1

        if video_index >= len(VIDEO_PATHS):
            break

        print(f"Switching to video {video_index + 1}: {VIDEO_PATHS[video_index]}")

        cap = cv2.VideoCapture(VIDEO_PATHS[video_index])

        if not cap.isOpened():
            print("ERROR: Could not open:")
            print(VIDEO_PATHS[video_index])
            break

        continue

    # --------------------------------------
    # YOLO + ByteTrack
    # --------------------------------------

    result = tracker.track(frame)


    # --------------------------------------
    # Get tracking information
    # --------------------------------------

    if result.boxes.id is not None:

        boxes = result.boxes.xyxy.cpu().tolist()

        track_ids = (
            result.boxes.id
            .int()
            .cpu()
            .tolist()
        )

        class_ids = (
            result.boxes.cls
            .int()
            .cpu()
            .tolist()
        )

    else:

        boxes = []
        track_ids = []
        class_ids = []


    # --------------------------------------
    # Vehicle counting
    # --------------------------------------

    total_count, type_counts, line_y = counter.update(
        frame_height=frame.shape[0],
        boxes=boxes,
        track_ids=track_ids,
        class_ids=class_ids,
        vehicle_classes=detector.vehicle_classes
    )
    current_vehicles, average_vehicles, density_counts = density.calculate(
        boxes=boxes,
        track_ids=track_ids,
        class_ids=class_ids,
        vehicle_classes=detector.vehicle_classes
    )

    density_level = density.get_density_level(
        average_vehicles
    )
    # --------------------------------------
    # Draw YOLO + tracking results
    # --------------------------------------

    annotated_frame = result.plot()


    # --------------------------------------
    # Draw counting line
    # --------------------------------------

    cv2.line(
        annotated_frame,
        (0, line_y),
        (frame.shape[1], line_y),
        (0, 255, 255),
        3
    )


    # --------------------------------------
    # Display traffic statistics
    # --------------------------------------

    cv2.putText(
        annotated_frame,
        f"Vehicles Passed: {total_count}",
        (30, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),
        3
    )

    cv2.putText(
        annotated_frame,
        f"Current Vehicles: {current_vehicles}",
        (30, 230),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Traffic Density: {density_level}",
        (30, 270),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        3
    )
    cv2.putText(
        annotated_frame,
        f"Average Vehicles: {average_vehicles:.1f}",
        (30, 310),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 255),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Cars: {type_counts['Car']}",
        (30, 85),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Motorcycles: {type_counts['Motorcycle']}",
        (30, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Buses: {type_counts['Bus']}",
        (30, 155),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.putText(
        annotated_frame,
        f"Trucks: {type_counts['Truck']}",
        (30, 190),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )


    # --------------------------------------
    # Display
    # --------------------------------------

    cv2.imshow(
        "UrbanPulse - Traffic Intelligence",
        annotated_frame
    )


    # Q = quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ==========================================
# Cleanup
# ==========================================

cap.release()
cv2.destroyAllWindows()


# ==========================================
# Final report
# ==========================================

print()
print("=" * 45)
print("       URBANPULSE TRAFFIC REPORT")
print("=" * 45)

print(f"Total vehicles passed: {total_count}")

print(f"Cars:         {type_counts['Car']}")
print(f"Motorcycles:  {type_counts['Motorcycle']}")
print(f"Buses:        {type_counts['Bus']}")
print(f"Trucks:       {type_counts['Truck']}")

print("=" * 45)
