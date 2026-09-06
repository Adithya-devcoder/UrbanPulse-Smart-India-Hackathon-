import io
import json
from PIL import Image


def test_ai_ingestion_road_defect_json(client):
    payload = {
        "module": "road_defect",
        "bus_id": "BUS-104",
        "camera_id": "CAM-042",
        "camera_position": "front",
        "latitude": 13.0650,
        "longitude": 80.2520,
        "location_name": "Anna Salai North",
        "confidence": 0.88,
        "severity": "Medium",
        "defect_type": "deep_pothole",
        "defect_size_cm": 35.0
    }
    response = client.post("/api/v1/ai/detections", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "INC-" in data["data"]["incident_code"]
    assert data["data"]["module"] == "road_defect"


def test_ai_ingestion_multipart_with_image(client):
    # Create simple in-memory JPEG
    img_byte_arr = io.BytesIO()
    img = Image.new("RGB", (100, 100), color="blue")
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)

    metadata = {
        "module": "traffic_sign",
        "bus_id": "BUS-108",
        "camera_id": "CAM-051",
        "camera_position": "front",
        "latitude": 12.9180,
        "longitude": 80.2310,
        "location_name": "OMR Sholinganallur",
        "confidence": 0.92,
        "sign_type": "SPEED_LIMIT_40",
        "sign_condition": "damaged"
    }

    response = client.post(
        "/api/v1/ai/detections",
        data={"data": json.dumps(metadata)},
        files={"image": ("camera_frame.jpg", img_byte_arr, "image/jpeg")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["evidence_url"] is not None


def test_multi_camera_pothole_correlation(client):
    # Front camera detection
    payload_front = {
        "module": "road_defect",
        "bus_id": "BUS-104",
        "camera_id": "CAM-042",
        "camera_position": "front",
        "latitude": 13.0610,
        "longitude": 80.2490,
        "confidence": 0.85,
        "defect_type": "pothole"
    }
    res1 = client.post("/api/v1/ai/detections", json=payload_front)
    inc_code_1 = res1.json()["data"]["incident_code"]

    # Rear camera detection within 5 meters
    payload_rear = {
        "module": "road_defect",
        "bus_id": "BUS-104",
        "camera_id": "CAM-043",
        "camera_position": "rear",
        "latitude": 13.06102,
        "longitude": 80.24902,
        "confidence": 0.82,
        "defect_type": "pothole"
    }
    res2 = client.post("/api/v1/ai/detections", json=payload_rear)
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert data2["is_correlated"] is True
    assert data2["incident_code"] == inc_code_1


def test_vehicle_density_and_ocr_ingestion(client):
    payload = {
        "module": "vehicle_density",
        "bus_id": "BUS-104",
        "camera_id": "CAM-042",
        "latitude": 13.0600,
        "longitude": 80.2480,
        "confidence": 0.95,
        "vehicles": [
            {
                "track_id": "TRK-9901",
                "vehicle_type": "car",
                "color": "White",
                "license_plate": "TN 02 AX 1122",
                "speed_kmh": 45.0,
                "confidence": 0.92
            }
        ]
    }
    response = client.post("/api/v1/ai/detections", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_vulnerable_pedestrian_ingestion(client):
    payload = {
        "module": "vulnerable_pedestrian",
        "bus_id": "BUS-104",
        "camera_id": "CAM-042",
        "latitude": 13.0630,
        "longitude": 80.2505,
        "confidence": 0.88,
        "pedestrian_movement": "crossing_jaywalk",
        "risk_level": "HIGH",
        "severity": "High"
    }
    response = client.post("/api/v1/ai/detections", json=payload)
    assert response.status_code == 200
    assert response.json()["data"]["incident_type"] == "Vulnerable Pedestrian Situation"
