class VehicleCounter:

    def __init__(self, line_position=0.60):
        """
        line_position:
        Position of the counting line as a percentage
        of the frame height.

        0.60 = 60% down the frame.
        """

        self.line_position = line_position

        # Remember the previous Y position of each vehicle
        self.previous_positions = {}

        # Vehicles that have already been counted
        self.counted_ids = set()

        # Total count
        self.total_count = 0

        # Count by vehicle type
        self.type_counts = {
            "Car": 0,
            "Motorcycle": 0,
            "Bus": 0,
            "Truck": 0
        }

    def update(self, frame_height, boxes, track_ids, class_ids, vehicle_classes):
        """
        Update vehicle positions and detect line crossings.

        boxes      -> bounding boxes
        track_ids  -> ByteTrack IDs
        class_ids  -> YOLO class IDs
        vehicle_classes -> dictionary mapping class IDs to names

        Returns:
            total_count
            type_counts
            line_y
        """

        line_y = int(frame_height * self.line_position)

        for box, track_id, class_id in zip(
            boxes,
            track_ids,
            class_ids
        ):

            # Ignore non-vehicle classes
            if class_id not in vehicle_classes:
                continue

            x1, y1, x2, y2 = box

            # Calculate center of vehicle
            center_y = int((y1 + y2) / 2)

            # Check whether this vehicle existed in the previous frame
            if track_id in self.previous_positions:

                previous_y = self.previous_positions[track_id]

                # Vehicle crossed the line downward
                crossed_line = (
                    previous_y < line_y
                    and center_y >= line_y
                )

                # Count only once
                if crossed_line and track_id not in self.counted_ids:

                    self.total_count += 1

                    self.counted_ids.add(track_id)

                    vehicle_type = vehicle_classes[class_id]

                    self.type_counts[vehicle_type] += 1

                    print(
                        f"[COUNT] "
                        f"ID={track_id} | "
                        f"Type={vehicle_type} | "
                        f"Total={self.total_count}"
                    )

            # Store current position
            self.previous_positions[track_id] = center_y

        return (
            self.total_count,
            self.type_counts,
            line_y
        )
