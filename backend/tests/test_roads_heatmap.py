def test_list_roads(client):
    response = client.get("/api/v1/roads")
    assert response.status_code == 200
    data = response.json()["data"]
    assert len(data) >= 5
    codes = [r["code"] for r in data]
    assert "RD-ANNASALAI" in codes
    assert "RD-OMR" in codes


def test_get_road_detail(client):
    response = client.get("/api/v1/roads/1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "name" in data
    assert "risk_score" in data


def test_recalculate_road_risk(client):
    response = client.post("/api/v1/roads/1/recalculate-risk")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["risk_score"] > 0
    assert data["status"] in ["High Risk", "Moderate", "Safe"]


def test_heatmap_endpoints(client):
    # Test all risk types
    response = client.get("/api/v1/heatmap?time_range=7_days&risk_type=all")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_points"] > 0
    assert len(data["points"]) > 0

    # Test specific filter
    res_potholes = client.get("/api/v1/heatmap?time_range=30_days&risk_type=potholes")
    assert res_potholes.status_code == 200
