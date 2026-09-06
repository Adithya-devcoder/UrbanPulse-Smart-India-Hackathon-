from ultralytics import YOLO
import cv2

# -----------------------------
# Configuration
# -----------------------------

model = YOLO("../yolo11n.pt")

video_path = "UrbanPulse/phase1/videos/traffic.mp4"

# Vehicle classes from COCO
vehicle_classes = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

# -----------------------------
# Open video
# -----------------------------

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("ERROR: Could not open video")
    exit()

# -----------------------------
# Tracking variables
# -----------------------------

previous_positions = {}

counted_ids = set()

total_count = 0

# We'll place the virtual line
# at 60% of the video height

frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

count_line_y = int(frame_height * 0.60)

# -----------------------------
# Process video
# -----------------------------

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # YOLO + ByteTrack
    results = model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        device=0,
        verbose=False
    )

    result = results[0]

    # Draw counting line
    cv2.line(
        frame,
        (0, count_line_y),
        (frame_width, count_line_y),
        (0, 255, 255),
        3
    )

    # Check if tracking IDs exist
    if result.boxes.id is not None:

        boxes = result.boxes.xyxy.cpu().tolist()
        track_ids = result.boxes.id.int().cpu().tolist()
        class_ids = result.boxes.cls.int().cpu().tolist()

        for box, track_id, class_id in zip(
            boxes,
            track_ids,
            class_ids
        ):

            # Only count vehicles
            if class_id not in vehicle_classes:
                continue

            x1, y1, x2, y2 = box

            # Center of vehicle
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            # Check previous position
            if track_id in previous_positions:

                previous_y = previous_positions[track_id]

                # Vehicle crossed the line downward
                if (
                    previous_y < count_line_y
                    and center_y >= count_line_y
                    and track_id not in counted_ids
                ):

                    total_count += 1

                    counted_ids.add(track_id)

                    print(
                        f"Vehicle {track_id} crossed the line | "
                        f"Type: {vehicle_classes[class_id]} | "
                        f"Total: {total_count}"
                    )

            # Save current position
            previous_positions[track_id] = center_y

            # Draw center point
            cv2.circle(
                frame,
                (center_x, center_y),
                5,
                (0, 0, 255),
                -1
            )

    # Draw YOLO + tracking annotations
    annotated_frame = result.plot()

    # Draw counting line again
    cv2.line(
        annotated_frame,
        (0, count_line_y),
        (frame_width, count_line_y),
        (0, 255, 255),
        3
    )

    # Display total count
    cv2.putText(
        annotated_frame,
        f"Vehicles Passed: {total_count}",
        (30, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (0, 255, 0),
        3
    )

    # Show video
    cv2.imshow(
        "UrbanPulse - Vehicle Counting",
        annotated_frame
    )

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()

cv2.destroyAllWindows()

print("\n==============================")
print("UrbanPulse Traffic Summary")
print("==============================")
print(f"Total vehicles passed: {total_count}")
