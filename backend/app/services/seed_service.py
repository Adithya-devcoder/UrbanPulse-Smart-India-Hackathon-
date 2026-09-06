import os
from datetime import datetime, timedelta
from typing import Tuple
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session

from app.models.road import Road, RoadSegment
from app.models.camera import Bus, Camera
from app.models.incident import Incident
from app.models.observation import Observation
from app.models.evidence import EvidenceFrame
from app.models.evidence_timeline import EvidenceTimelineEvent
from app.models.vehicle import VehicleObservation
from app.models.action import ActionItem
from app.models.notification import Notification
from app.core.config import settings
from app.services.road_risk_service import road_risk_service


def generate_synthetic_evidence_image(filename: str, caption: str, color: tuple = (30, 41, 59)) -> Tuple[str, str]:
    """Generates a clean synthetic evidence frame JPEG image with timestamp and camera watermarks."""
    target_path = settings.EVIDENCE_DIR / filename
    img = Image.new("RGB", (640, 360), color=color)
    draw = ImageDraw.Draw(img)

    # Grid lines / simulated road layout
    draw.line([(0, 240), (640, 240)], fill=(71, 85, 105), width=2)
    draw.line([(200, 360), (280, 240)], fill=(234, 179, 8), width=3)
    draw.line([(440, 360), (360, 240)], fill=(234, 179, 8), width=3)

    # Watermark text
    draw.rectangle([(10, 10), (630, 50)], fill=(15, 23, 42, 200))
    draw.text((20, 18), f"URBANPULSE AI SENSING | {caption.upper()}", fill=(248, 250, 252))
    
    timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    draw.rectangle([(10, 315), (630, 350)], fill=(15, 23, 42, 200))
    draw.text((20, 325), f"TIMESTAMP: {timestamp_str} | SENSOR: CAM-042 (FRONT-HD)", fill=(148, 163, 184))

    # Save
    img.save(target_path, "JPEG", quality=85)
    relative_url = f"/api/v1/static/evidence/{filename}"
    return str(target_path), relative_url


class SeedService:
    @staticmethod
    def seed_demo_data(db: Session, force: bool = False):
        existing = db.query(Incident).filter(Incident.incident_code == "INC-2048").first()
        if existing and not force:
            return  # Already seeded

        # Ensure evidence folder exists
        settings.EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Seed Roads
        roads_data = [
            {
                "code": "RD-ANNASALAI",
                "name": "Anna Salai",
                "zone": "Central Zone",
                "road_type": "Arterial",
                "latitude": 13.0604,
                "longitude": 80.2496,
                "length_km": 14.5,
                "accident_count": 4,
                "pothole_count": 6,
                "waterlogging_count": 2,
                "traffic_index": 82.0,
                "average_response_time_min": 24.0,
            },
            {
                "code": "RD-OMR",
                "name": "Old Mahabalipuram Road (OMR)",
                "zone": "South Zone",
                "road_type": "IT Expressway",
                "latitude": 12.9150,
                "longitude": 80.2280,
                "length_km": 21.0,
                "accident_count": 2,
                "pothole_count": 8,
                "waterlogging_count": 4,
                "traffic_index": 78.0,
                "average_response_time_min": 19.5,
            },
            {
                "code": "RD-GST",
                "name": "Grand Southern Trunk (GST) Road",
                "zone": "South West Zone",
                "road_type": "National Highway",
                "latitude": 12.9815,
                "longitude": 80.1636,
                "length_km": 28.0,
                "accident_count": 5,
                "pothole_count": 4,
                "waterlogging_count": 1,
                "traffic_index": 88.0,
                "average_response_time_min": 28.0,
            },
            {
                "code": "RD-PHROAD",
                "name": "Poonamallee High Road",
                "zone": "West Zone",
                "road_type": "Arterial",
                "latitude": 13.0827,
                "longitude": 80.2185,
                "length_km": 16.0,
                "accident_count": 1,
                "pothole_count": 5,
                "waterlogging_count": 1,
                "traffic_index": 65.0,
                "average_response_time_min": 21.0,
            },
            {
                "code": "RD-ECR",
                "name": "East Coast Road (ECR)",
                "zone": "Coastal South",
                "road_type": "State Highway",
                "latitude": 12.8700,
                "longitude": 80.2500,
                "length_km": 35.0,
                "accident_count": 1,
                "pothole_count": 1,
                "waterlogging_count": 0,
                "traffic_index": 35.0,
                "average_response_time_min": 15.0,
            }
        ]

        created_roads = {}
        for r_dict in roads_data:
            road = db.query(Road).filter(Road.code == r_dict["code"]).first()
            if not road:
                road = Road(**r_dict)
                db.add(road)
                db.flush()
                road_risk_service.update_road_metrics(db, road.id)
            created_roads[road.code] = road

        # 2. Seed Buses & Cameras
        bus_1 = db.query(Bus).filter(Bus.bus_number == "TN-01-N-9842").first()
        if not bus_1:
            bus_1 = Bus(
                bus_number="TN-01-N-9842",
                route_number="21G",
                status="Active",
                last_latitude=13.0604,
                last_longitude=80.2496,
                last_ping_at=datetime.utcnow()
            )
            db.add(bus_1)
            db.flush()

            cameras = [
                Camera(camera_code="CAM-042", bus_id=bus_1.id, camera_position="front", location_name="Anna Salai", latitude=13.0604, longitude=80.2496, status="Online", last_frame_at=datetime.utcnow()),
                Camera(camera_code="CAM-043", bus_id=bus_1.id, camera_position="rear", location_name="Anna Salai", latitude=13.0604, longitude=80.2496, status="Online", last_frame_at=datetime.utcnow()),
                Camera(camera_code="CAM-044", bus_id=bus_1.id, camera_position="left_side", location_name="Anna Salai", latitude=13.0604, longitude=80.2496, status="Online", last_frame_at=datetime.utcnow()),
            ]
            db.add_all(cameras)

        bus_2 = db.query(Bus).filter(Bus.bus_number == "TN-09-B-3104").first()
        if not bus_2:
            bus_2 = Bus(
                bus_number="TN-09-B-3104",
                route_number="570",
                status="Active",
                last_latitude=12.9150,
                last_longitude=80.2280,
                last_ping_at=datetime.utcnow()
            )
            db.add(bus_2)
            db.flush()

            cameras_2 = [
                Camera(camera_code="CAM-051", bus_id=bus_2.id, camera_position="front", location_name="OMR IT Corridor", latitude=12.9150, longitude=80.2280, status="Online", last_frame_at=datetime.utcnow()),
                Camera(camera_code="CAM-052", bus_id=bus_2.id, camera_position="right_side", location_name="OMR IT Corridor", latitude=12.9150, longitude=80.2280, status="Online", last_frame_at=datetime.utcnow()),
            ]
            db.add_all(cameras_2)

        # 3. Create Highlight Demo Incident: INC-2048 (Hit-and-Run on Anna Salai)
        anna_salai = created_roads.get("RD-ANNASALAI")
        detected_time = datetime.utcnow().replace(hour=10, minute=42, second=18)
        
        inc_2048 = Incident(
            incident_code="INC-2048",
            incident_type="Possible Hit-and-Run",
            module="multimodal",
            road_id=anna_salai.id if anna_salai else None,
            location_name="Anna Salai, near Thousand Lights",
            latitude=13.0604,
            longitude=80.2496,
            severity="Critical",
            confidence=0.87,
            status="Under Review",
            detected_time=detected_time,
            assessment_text=(
                "AI Assessment [Probabilistic Sensor Fusion]: Vehicle A (Silver Sedan, Plate: TN 09 BX 4412) "
                "approached Vehicle B (Black SUV) at 10:42:21. Sudden lateral trajectory shift and proximity "
                "threshold violation detected at 10:42:23. Vehicle B came to a complete halt while Vehicle A "
                "accelerated and exited camera field of view at 10:42:31 without stopping. "
                "High probability of non-stop collision (Hit-and-Run pattern flagged)."
            ),
            is_demo_seed=True
        )
        db.add(inc_2048)
        db.flush()

        # 4. Vehicles for INC-2048 (2 vehicles)
        veh_a = VehicleObservation(
            incident_id=inc_2048.id,
            vehicle_track_id="Vehicle A",
            vehicle_type="car",
            color="Silver",
            license_plate="TN 09 BX 4412",
            plate_confidence=0.91,
            speed_kmh=48.0,
            direction="Northbound",
            lane="Lane 2",
            confidence=0.94
        )
        veh_b = VehicleObservation(
            incident_id=inc_2048.id,
            vehicle_track_id="Vehicle B",
            vehicle_type="suv",
            color="Black",
            license_plate="TN 07 CP 8821",
            plate_confidence=0.88,
            speed_kmh=0.0,
            direction="Northbound",
            lane="Lane 1",
            confidence=0.92
        )
        db.add_all([veh_a, veh_b])

        # 5. 6 Evidence Frames for INC-2048
        frames_meta = [
            ("frame_2048_1.jpg", "Vehicle A enters frame (Anna Salai, Northbound)", "CAM-042", detected_time),
            ("frame_2048_2.jpg", "Vehicle B approaches intersection", "CAM-042", detected_time + timedelta(seconds=3)),
            ("frame_2048_3.jpg", "Critical proximity & impact angle detected", "CAM-042", detected_time + timedelta(seconds=5)),
            ("frame_2048_4.jpg", "Vehicle B stops abruptly with hazard lights", "CAM-042", detected_time + timedelta(seconds=7)),
            ("frame_2048_5.jpg", "Vehicle A accelerating away from scene", "CAM-042", detected_time + timedelta(seconds=13)),
            ("frame_2048_6.jpg", "Rear camera confirmation of vehicle departure", "CAM-043", detected_time + timedelta(seconds=14)),
        ]
        created_frames = []
        for i, (fn, cap, cam, t) in enumerate(frames_meta, 1):
            f_path, f_url = generate_synthetic_evidence_image(fn, cap)
            frame = EvidenceFrame(
                incident_id=inc_2048.id,
                frame_number=i,
                camera_id=cam,
                file_path=f_path,
                file_url=f_url,
                mime_type="image/jpeg",
                timestamp=t,
                ocr_extracted_text="TN 09 BX 4412" if i in [1, 5] else None,
                ocr_confidence=0.91 if i in [1, 5] else None,
                caption=cap
            )
            db.add(frame)
            db.flush()
            created_frames.append(frame)

        # 6. 5 Evidence Timeline Events for INC-2048
        timeline_events = [
            EvidenceTimelineEvent(
                incident_id=inc_2048.id,
                evidence_frame_id=created_frames[0].id,
                timestamp_str="10:42:18 AM",
                timestamp=detected_time,
                event_type="Vehicle Enters Frame",
                description="Vehicle A (Silver Sedan, TN 09 BX 4412) enters camera frame traveling at 48 km/h.",
                vehicle_track_id="Vehicle A",
                is_ai_generated=True
            ),
            EvidenceTimelineEvent(
                incident_id=inc_2048.id,
                evidence_frame_id=created_frames[1].id,
                timestamp_str="10:42:21 AM",
                timestamp=detected_time + timedelta(seconds=3),
                event_type="Proximity Alert",
                description="Vehicle B (Black SUV) approaches adjacent lane. Separation distance decreases rapidly.",
                vehicle_track_id="Vehicle B",
                is_ai_generated=True
            ),
            EvidenceTimelineEvent(
                incident_id=inc_2048.id,
                evidence_frame_id=created_frames[2].id,
                timestamp_str="10:42:23 AM",
                timestamp=detected_time + timedelta(seconds=5),
                event_type="Collision Detected",
                description="Possible collision detected between Vehicle A and Vehicle B. Angular anomaly flagged.",
                vehicle_track_id="Vehicle A",
                is_ai_generated=True
            ),
            EvidenceTimelineEvent(
                incident_id=inc_2048.id,
                evidence_frame_id=created_frames[3].id,
                timestamp_str="10:42:25 AM",
                timestamp=detected_time + timedelta(seconds=7),
                event_type="Vehicle Stops",
                description="Vehicle B comes to complete stop in Lane 1.",
                vehicle_track_id="Vehicle B",
                is_ai_generated=True
            ),
            EvidenceTimelineEvent(
                incident_id=inc_2048.id,
                evidence_frame_id=created_frames[4].id,
                timestamp_str="10:42:31 AM",
                timestamp=detected_time + timedelta(seconds=13),
                event_type="Vehicle Leaves Scene",
                description="Vehicle A departs scene rapidly at 54 km/h without stopping. Hit-and-run intelligence flagged.",
                vehicle_track_id="Vehicle A",
                is_ai_generated=True
            ),
        ]
        db.add_all(timeline_events)

        # 7. Action item & Notification for INC-2048
        action_2048 = ActionItem(
            action_code="ACT-2048",
            incident_id=inc_2048.id,
            title="Dispatch Traffic Interceptor Unit to Anna Salai",
            priority="Critical",
            assigned_team="Chennai Traffic Police Interceptor Unit 4",
            status="In Progress",
            eta_minutes=12,
            notes="Reviewing ANPR camera feed for Silver Sedan TN 09 BX 4412 heading towards Gemini Flyover."
        )
        db.add(action_2048)

        notif_2048 = Notification(
            incident_id=inc_2048.id,
            notification_type="CRITICAL_ALERT",
            title="CRITICAL: Possible Hit-and-Run on Anna Salai",
            message="Vehicle A fled scene after collision with Vehicle B. AI Confidence 87%. ANPR plate TN 09 BX 4412.",
            severity="Critical",
            is_read=False
        )
        db.add(notif_2048)

        # 8. Seed Second Scenario: Waterlogged Pothole on OMR
        omr = created_roads.get("RD-OMR")
        pothole_time = datetime.utcnow() - timedelta(minutes=45)
        inc_pothole = Incident(
            incident_code="INC-2049",
            incident_type="Waterlogged Pothole",
            module="road_defect",
            road_id=omr.id if omr else None,
            location_name="OMR IT Corridor, near Thoraipakkam Junction",
            latitude=12.9150,
            longitude=80.2280,
            severity="High",
            confidence=0.89,
            status="Verified",
            detected_time=pothole_time,
            assessment_text=(
                "AI Assessment [Sensor Fusion]: Correlated road surface depression with historical pothole repository "
                "and standing water radar signature. Probability of severe submerged waterlogged pothole: 84%."
            ),
            waterlogged_pothole_probability=0.84,
            is_demo_seed=True
        )
        db.add(inc_pothole)
        db.flush()

        pothole_img_path, pothole_img_url = generate_synthetic_evidence_image("frame_pothole_omr.jpg", "Submerged Pothole on OMR", color=(40, 50, 60))
        pothole_frame = EvidenceFrame(
            incident_id=inc_pothole.id,
            frame_number=1,
            camera_id="CAM-051",
            file_path=pothole_img_path,
            file_url=pothole_img_url,
            mime_type="image/jpeg",
            timestamp=pothole_time,
            caption="Front camera frame indicating road depression submerged in rainwater"
        )
        db.add(pothole_frame)

        pothole_tl = EvidenceTimelineEvent(
            incident_id=inc_pothole.id,
            timestamp_str=pothole_time.strftime("%I:%M:%S %p"),
            timestamp=pothole_time,
            event_type="Waterlogged Pothole Flagged",
            description="Deep depression co-located with waterlogging recorded by Bus BUS-108 (CAM-051).",
            is_ai_generated=True
        )
        db.add(pothole_tl)

        # 9. Additional diverse seed incidents (Sign, Pedestrian, Bottleneck)
        gst = created_roads.get("RD-GST")
        inc_sign = Incident(
            incident_code="INC-2050",
            incident_type="Damaged / Missing Traffic Sign",
            module="traffic_sign",
            road_id=gst.id if gst else None,
            location_name="GST Road, near Airport Flyover",
            latitude=12.9815,
            longitude=80.1636,
            severity="Medium",
            confidence=0.93,
            status="Assigned",
            detected_time=datetime.utcnow() - timedelta(hours=3),
            assessment_text="AI Assessment: Overhead Speed Limit sign structure severely damaged and bent into roadway.",
            is_demo_seed=True
        )
        db.add(inc_sign)

        inc_pedestrian = Incident(
            incident_code="INC-2051",
            incident_type="Vulnerable Pedestrian Situation",
            module="vulnerable_pedestrian",
            road_id=anna_salai.id if anna_salai else None,
            location_name="Anna Salai, Spencer Plaza Junction",
            latitude=13.0620,
            longitude=80.2510,
            severity="High",
            confidence=0.86,
            status="Monitoring",
            detected_time=datetime.utcnow() - timedelta(hours=1),
            assessment_text="AI Assessment: Pedestrian crossing high-speed arterial carriageway outside designated crosswalk.",
            is_demo_seed=True
        )
        db.add(inc_pedestrian)

        db.commit()


seed_service = SeedService()
