def test_dashboard_kpis(client):
    response = client.get("/api/v1/dashboard/kpis")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "active_incidents" in data
    assert "high_risk_roads" in data
    assert "potholes_detected" in data
    assert "waterlogging_zones" in data


def test_analytics_overview(client):
    response = client.get("/api/v1/analytics/overview?time_range=7_days")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "trends" in data
    assert "distribution" in data
    assert "response_performance" in data
    assert "ai_performance" in data


def test_global_search(client):
    # Search by road name
    res1 = client.get("/api/v1/search?q=Anna")
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert data1["total_results"] > 0

    # Search by incident code
    res2 = client.get("/api/v1/search?q=INC-2048")
    assert res2.status_code == 200
    assert res2.json()["data"]["total_results"] > 0
