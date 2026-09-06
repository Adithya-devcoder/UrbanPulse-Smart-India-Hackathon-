from ultralytics import YOLO


class VehicleTracker:

    def __init__(self):
        # Load YOLO model
        self.model = YOLO(
            "UrbanPulse/models/vehicle/yolo11n.pt"
        )

    def track(self, frame):
        """
        Detect and track vehicles using ByteTrack.

        persist=True tells YOLO to maintain
        tracking IDs between consecutive frames.
        """

        results = self.model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            device=0,
            verbose=False
        )

        return results[0]
