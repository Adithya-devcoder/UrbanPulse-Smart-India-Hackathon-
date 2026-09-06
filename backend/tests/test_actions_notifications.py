def test_action_center_workflow(client):
    # Create action
    payload = {
        "incident_id": 1,
        "title": "Deploy Asphalt Patch Unit",
        "priority": "High",
        "assigned_team": "GCC Road Works",
        "eta_minutes": 45,
        "notes": "Emergency pothole repair"
    }
    response = client.post("/api/v1/actions", json=payload)
    assert response.status_code == 200
    action_data = response.json()["data"]
    assert "ACT-" in action_data["action_code"]
    action_id = action_data["id"]

    # Update action status
    patch_res = client.patch(
        f"/api/v1/actions/{action_id}",
        json={"status": "Resolved", "notes": "Asphalt patch completed."}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["status"] == "Resolved"


def test_notifications_workflow(client):
    res = client.get("/api/v1/notifications")
    assert res.status_code == 200
    notifs = res.json()["data"]
    assert len(notifs) > 0

    notif_id = notifs[0]["id"]
    read_res = client.patch(f"/api/v1/notifications/{notif_id}/read")
    assert read_res.status_code == 200
    assert read_res.json()["data"]["is_read"] is True

    mark_all_res = client.post("/api/v1/notifications/mark-all-read")
    assert mark_all_res.status_code == 200
