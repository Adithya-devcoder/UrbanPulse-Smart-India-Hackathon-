from ultralytics import YOLO
import cv2
import glob
import os

# ==========================================
# Configuration
# ==========================================

MODEL_PATH = "UrbanPulse/models/pothole/best.pt"
VIDEO_FOLDER = "UrbanPulse/phase1/videos"

CONFIDENCE = 0.40

# ==========================================
# Load pothole model
# ==========================================

print("Loading pothole model...")

model = YOLO(MODEL_PATH)

print("Pothole model loaded successfully")
print("Classes:", model.names)

# ==========================================
# Find all videos
# ==========================================

video_files = []

for extension in ("*.mp4", "*.avi", "*.mov", "*.mkv"):
    video_files.extend(
        glob.glob(
            os.path.join(VIDEO_FOLDER, extension)
        )
    )

video_files.sort()

if not video_files:
    print("ERROR: No videos found in:")
    print(VIDEO_FOLDER)
    exit()

print()
print("Videos found:")

for video in video_files:
    print(" -", os.path.basename(video))

print()
print("Total videos:", len(video_files))

# ==========================================
# Process videos continuously
# ==========================================

for video_number, video_path in enumerate(video_files, start=1):

    print()
    print("=" * 50)
    print(f"Processing video {video_number}/{len(video_files)}")
    print(os.path.basename(video_path))
    print("=" * 50)

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("ERROR: Could not open:")
        print(video_path)
        continue

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        # ==================================
        # YOLO pothole detection
        # ==================================

        results = model(
            frame,
            device=0,
            conf=CONFIDENCE,
            verbose=False
        )

        # ==================================
        # Draw detections
        # ==================================

        annotated_frame = results[0].plot()

        # ==================================
        # Display current video
        # ==================================

        cv2.putText(
            annotated_frame,
            f"Video {video_number}/{len(video_files)}",
            (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2
        )

        cv2.putText(
            annotated_frame,
            os.path.basename(video_path),
            (30, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.imshow(
            "UrbanPulse - Pothole Detection",
            annotated_frame
        )

        # Q = quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            cap.release()
            cv2.destroyAllWindows()
            print("Stopped by user.")
            exit()

    cap.release()

    print("Finished:", os.path.basename(video_path))


# ==========================================
# Cleanup
# ==========================================

cv2.destroyAllWindows()

print()
print("=" * 50)
print("ALL VIDEOS PROCESSED")
print("=" * 50)
