import time
from datetime import datetime


class LocationProvider:

    def __init__(self):
        # Prototype GPS position.
        # In production this will come from the
        # authorized MTC GPS/AVL interface.
        self.latitude = 13.0827
        self.longitude = 80.2707

        self.bus_id = "MTC-DEMO-001"

    def get_location(self):

        return {
            "bus_id": self.bus_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":

    gps = LocationProvider()

    location = gps.get_location()

    print("GPS/AVL Location")
    print("----------------")
    print("Bus ID:", location["bus_id"])
    print("Latitude:", location["latitude"])
    print("Longitude:", location["longitude"])
    print("Timestamp:", location["timestamp"])
