from ultralytics import YOLO


class VehicleDetector:

    def __init__(self):
        # Load pretrained YOLO model
        self.model = YOLO(
            "UrbanPulse/models/vehicle/yolo11n.pt"
        )

        # COCO vehicle classes
        self.vehicle_classes = {
            2: "Car",
            3: "Motorcycle",
            5: "Bus",
            7: "Truck"
        }

    def detect(self, frame):
        """
        Detect vehicles in a single frame.

        Returns YOLO detection results.
        """

        results = self.model(
            frame,
            device=0,
            verbose=False
        )

        return results
