from collections import defaultdict


class TrafficDensity:

    def __init__(self, history_size=30):
        """
        history_size:
        Number of recent frames used to calculate
        traffic statistics.
        """

        self.history_size = history_size

        # Recent vehicle counts
        self.vehicle_history = []

        # Recent vehicle-type counts
        self.type_history = []

        # Track how long vehicles remain visible
        self.track_history = defaultdict(list)

    def calculate(
        self,
        boxes,
        track_ids,
        class_ids,
        vehicle_classes
    ):
        """
        Calculate traffic statistics from
        YOLO + ByteTrack results.
        """

        current_counts = {
            "Car": 0,
            "Motorcycle": 0,
            "Bus": 0,
            "Truck": 0
        }

        # Process currently tracked vehicles
        for box, track_id, class_id in zip(
            boxes,
            track_ids,
            class_ids
        ):

            if class_id not in vehicle_classes:
                continue

            vehicle_type = vehicle_classes[class_id]

            current_counts[vehicle_type] += 1

            # Save vehicle center position
            x1, y1, x2, y2 = box

            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)

            self.track_history[track_id].append(
                (center_x, center_y)
            )

            # Keep only recent positions
            if len(self.track_history[track_id]) > self.history_size:
                self.track_history[track_id].pop(0)

        # Total vehicles currently visible
        total_vehicles = sum(current_counts.values())

        # Save history
        self.vehicle_history.append(total_vehicles)
        self.type_history.append(current_counts.copy())

        if len(self.vehicle_history) > self.history_size:
            self.vehicle_history.pop(0)

        if len(self.type_history) > self.history_size:
            self.type_history.pop(0)

        # Calculate average vehicles over recent frames
        average_vehicles = (
            sum(self.vehicle_history)
            / len(self.vehicle_history)
        )

        return (
            total_vehicles,
            average_vehicles,
            current_counts
        )

    def get_density_level(self, average_vehicles):
        """
        Estimate traffic density from recent
        vehicle occupancy.

        These are prototype thresholds and will
        later be calibrated using real road data.
        """

        if average_vehicles < 8:
            return "LOW"

        elif average_vehicles < 18:
            return "MEDIUM"

        elif average_vehicles < 30:
            return "HIGH"

        else:
            return "SEVERE"

    def get_vehicle_history(self):
        """
        Return recent vehicle-count history.
        """

        return self.vehicle_history
