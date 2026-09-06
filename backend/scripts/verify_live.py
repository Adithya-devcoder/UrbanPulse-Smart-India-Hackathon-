import urllib.request
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("========================================")
    print("URBANPULSE LIVE BACKEND VERIFICATION")
    print("========================================")

    # 1. Health Check
    res = urllib.request.urlopen(f"{BASE_URL}/health")
    health = json.loads(res.read())
    print("[1] Health:", health)

    # 2. Dashboard KPIs
    res = urllib.request.urlopen(f"{BASE_URL}/api/v1/dashboard/kpis")
    kpis = json.loads(res.read())["data"]
    print("[2] Dashboard KPIs:", kpis)

    # 3. Highlight Incident INC-2048
    res = urllib.request.urlopen(f"{BASE_URL}/api/v1/incidents/INC-2048")
    inc = json.loads(res.read())["data"]
    print(f"[3] Incident INC-2048: {inc['incident_type']} | Severity: {inc['severity']} | Confidence: {inc['confidence']*100}% | Frames: {len(inc['evidence_frames'])} | Timeline: {len(inc['timeline_events'])} | Vehicles: {len(inc['vehicles'])}")

    # 4. Waterlogged Pothole INC-2049
    res = urllib.request.urlopen(f"{BASE_URL}/api/v1/incidents/INC-2049")
    pothole = json.loads(res.read())["data"]
    print(f"[4] Incident INC-2049: {pothole['incident_type']} | Waterlogged Pothole Probability: {pothole['waterlogged_pothole_probability']*100}%")

    # 5. Roads & Multi-factor Risk Scores
    res = urllib.request.urlopen(f"{BASE_URL}/api/v1/roads")
    roads = json.loads(res.read())["data"]
    print(f"[5] Major Roads Tracked ({len(roads)}):")
    for r in roads:
        print(f"    - {r['name']} ({r['code']}): Risk Score = {r['risk_score']} [{r['status']}] | Accidents = {r['accident_count']} | Potholes = {r['pothole_count']}")

    # 6. Heatmap Points
    res = urllib.request.urlopen(f"{BASE_URL}/api/v1/heatmap?time_range=7_days&risk_type=all")
    heatmap = json.loads(res.read())["data"]
    print(f"[6] Heatmap Points: {heatmap['total_points']} geographic risk nodes")

    # 7. AI Ingestion API
    ai_payload = json.dumps({
        "module": "road_defect",
        "bus_id": "BUS-104",
        "camera_id": "CAM-042",
        "camera_position": "front",
        "latitude": 13.0615,
        "longitude": 80.2498,
        "location_name": "Anna Salai Crossroad",
        "confidence": 0.91,
        "severity": "Medium",
        "defect_type": "deep_pothole"
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/ai/detections",
        data=ai_payload,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    ai_resp = json.loads(res.read())["data"]
    print(f"[7] AI Ingestion Result: Incident {ai_resp['incident_code']} created | Correlated: {ai_resp['is_correlated']}")

    # 8. Export Incident PDF
    res = urllib.request.urlopen(f"{BASE_URL}/api/v1/incidents/INC-2048/export")
    pdf_data = res.read()
    output_pdf = Path("storage/UrbanPulse_Incident_INC-2048_Dossier.pdf")
    output_pdf.write_bytes(pdf_data)
    print(f"[8] PDF Dossier Export: Saved {len(pdf_data)} bytes to {output_pdf} (Magic: {pdf_data[:4].decode('latin-1')})")

    # 9. Unified Global Search
    res = urllib.request.urlopen(f"{BASE_URL}/api/v1/search?q=Anna")
    search_res = json.loads(res.read())["data"]
    print(f"[9] Global Search for 'Anna': {search_res['total_results']} matching items across Incidents, Roads, and Cameras")

    print("========================================")
    print("ALL ACCEPTANCE CHECKS VERIFIED SUCCESSFULLY!")
    print("========================================")


if __name__ == "__main__":
    main()
