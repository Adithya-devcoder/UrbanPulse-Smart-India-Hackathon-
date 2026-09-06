def test_export_incident_pdf(client):
    response = client.get("/api/v1/incidents/INC-2048/export")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers.get("content-disposition", "")
    # Check PDF magic bytes (%PDF)
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 1000  # Non-empty PDF
