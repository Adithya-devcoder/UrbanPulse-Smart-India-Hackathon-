def test_list_incidents(client):
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] >= 2
    assert len(data["data"]["items"]) > 0


def test_get_demo_incident_2048(client):
    response = client.get("/api/v1/incidents/INC-2048")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["incident_code"] == "INC-2048"
    assert data["incident_type"] == "Possible Hit-and-Run"
    assert data["severity"] == "Critical"
    assert data["confidence"] == 0.87
    assert data["status"] == "Under Review"
    assert len(data["vehicles"]) == 2
    assert len(data["evidence_frames"]) >= 5
    assert len(data["timeline_events"]) >= 5


def test_update_incident_status(client):
    response = client.patch(
        "/api/v1/incidents/INC-2048/status",
        json={"status": "Verified", "notes": "Traffic inspector verified ANPR footage"}
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "Verified"


def test_get_incident_evidence(client):
    response = client.get("/api/v1/incidents/INC-2048/evidence")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "evidence_frames" in data
    assert "timeline_events" in data
