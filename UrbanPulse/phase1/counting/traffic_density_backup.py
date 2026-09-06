class TrafficDensity:

    def __init__(self):
        self.current_counts = {
            "Car": 0,
            "Motorcycle": 0,
            "Bus": 0,
            "Truck": 0
        }

    def calculate(self, class_ids, vehicle_classes):
        """
        Calculate the number of vehicles currently
        visible in the camera frame.
        """

        # Reset counts for the current frame
        self.current_counts = {
            "Car": 0,
            "Motorcycle": 0,
            "Bus": 0,
            "Truck": 0
        }

        for class_id in class_ids:

            if class_id in vehicle_classes:

                vehicle_type = vehicle_classes[class_id]

                self.current_counts[vehicle_type] += 1

        total_vehicles = sum(self.current_counts.values())

        return total_vehicles, self.current_counts

    def get_density_level(self, total_vehicles):
        """
        Convert vehicle count into a simple
        traffic density category.

        These thresholds are prototype values.
        We will calibrate them later using
        real road data.
        """

        if total_vehicles <= 10:
            return "LOW"

        elif total_vehicles <= 25:
            return "MEDIUM"

        else:
            return "HIGH"
