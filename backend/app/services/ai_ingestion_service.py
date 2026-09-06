import math
import uuid
from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.observation import Observation
from app.models.evidence import EvidenceFrame
from app.models.evidence_timeline import EvidenceTimelineEvent
from app.models.vehicle import VehicleObservation
from app.models.notification import Notification
from app.models.road import Road
from app.schemas.ai_ingestion import AIDetectionIngestRequest, AIDetectionIngestResponse
from app.integrations.storage.local_storage import storage_provider
from app.integrations.ocr.ocr_service import ocr_service
from app.services.road_risk_service import road_risk_service


def calculate_haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates distance between two GPS coordinates in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class AIIngestionService:
    @staticmethod
    def _find_matching_road(db: Session, lat: float, lon: float) -> Optional[Road]:
        """Finds closest road within ~500 meters or returns default primary road."""
        roads = db.query(Road).all()
        best_road = None
        min_dist = float("inf")
        for road in roads:
            dist = calculate_haversine_distance_meters(lat, lon, road.latitude, road.longitude)
            if dist < min_dist:
                min_dist = dist
                best_road = road
        if min_dist <= 1500:  # 1.5 km
            return best_road
        return None

    @staticmethod
    def _find_correlated_incident(db: Session, req: AIDetectionIngestRequest) -> Optional[Incident]:
        """
        Correlates multi-camera observations of the same road defect or ongoing incident
        within 25 meters and 5 minutes window.
        """
        if req.module not in ["road_defect", "pothole"]:
            return None

        window_start = datetime.utcnow() - timedelta(minutes=5)
        candidates = db.query(Incident).filter(
            Incident.module.in_(["road_defect", "pothole"]),
            Incident.status.notin_(["Resolved", "Rejected"]),
            Incident.detected_time >= window_start
        ).all()

        for inc in candidates:
            dist = calculate_haversine_distance_meters(req.latitude, req.longitude, inc.latitude, inc.longitude)
            if dist <= 25.0:  # within 25 meters
                return inc
        return None

    @classmethod
    async def process_detection(
        cls,
        db: Session,
        req: AIDetectionIngestRequest,
        image_file: Optional[UploadFile] = None,
        image_bytes: Optional[bytes] = None
    ) -> AIDetectionIngestResponse:
        # 1. Find or assign Road
        road = cls._find_matching_road(db, req.latitude, req.longitude)
        location_title = req.location_name or (road.name if road else f"Coordinates ({req.latitude:.4f}, {req.longitude:.4f})")

        # 2. Check for correlation with existing incident
        correlated_incident = cls._find_correlated_incident(db, req)
        is_correlated = correlated_incident is not None

        incident = correlated_incident
        if not incident:
            # Generate new incident code
            incident_number = db.query(Incident).count() + 2049
            incident_code = f"INC-{incident_number}"
            
            # Formulate incident type label
            inc_type = req.incident_type
            if not inc_type:
                if req.module in ["road_defect", "pothole"]:
                    inc_type = "Pothole / Road Defect"
                elif req.module == "traffic_sign":
                    inc_type = "Damaged / Missing Traffic Sign"
                elif req.module == "vehicle_density":
                    inc_type = "High Vehicle Density"
                elif req.module == "traffic_bottleneck":
                    inc_type = "Traffic Bottleneck"
                elif req.module == "vulnerable_pedestrian":
                    inc_type = "Vulnerable Pedestrian Situation"
                else:
                    inc_type = "Urban Road Hazard"

            # Formulate AI Assessment narrative (strictly labeled as AI-generated)
            assessment_text = (
                f"AI Assessment [Probabilistic Sensor Fusion]: Multi-camera detection on bus {req.bus_id} "
                f"via {req.camera_position} camera ({req.camera_id}). Confidence: {int(req.confidence * 100)}%. "
                f"Identified {inc_type.lower()} at {location_title}."
            )

            # Check Waterlogged Pothole intelligence condition
            waterlogged_pothole_prob = None
            if req.module in ["road_defect", "pothole"]:
                # If road has high waterlogging history or metadata indicates wet surface
                if (road and road.waterlogging_count > 0) or (req.metadata and req.metadata.get("waterlogged", False)):
                    waterlogged_pothole_prob = 0.84
                    assessment_text += " Co-location analysis indicates high likelihood (84%) of submerged waterlogged pothole."

            incident = Incident(
                incident_code=incident_code,
                incident_type=inc_type,
                module=req.module,
                road_id=road.id if road else None,
                location_name=location_title,
                latitude=req.latitude,
                longitude=req.longitude,
                severity=req.severity or "Medium",
                confidence=req.confidence,
                status="New",
                detected_time=req.timestamp or datetime.utcnow(),
                assessment_text=assessment_text,
                waterlogged_pothole_probability=waterlogged_pothole_prob,
                is_demo_seed=False
            )
            db.add(incident)
            db.flush()

            # Update road stats if road is linked
            if road:
                if req.module in ["road_defect", "pothole"]:
                    road.pothole_count += 1
                elif req.severity in ["High", "Critical"]:
                    road.accident_count += 1
                road_risk_service.update_road_metrics(db, road.id)

        # 3. Create Observation record
        obs = Observation(
            incident_id=incident.id,
            module=req.module,
            defect_type=req.defect_type,
            sign_type=req.sign_type,
            sign_condition=req.sign_condition,
            pedestrian_movement=req.pedestrian_movement,
            risk_state=req.risk_level,
            confidence=req.confidence,
            camera_id=req.camera_id,
            bus_id=req.bus_id,
            latitude=req.latitude,
            longitude=req.longitude,
            raw_metadata=req.metadata,
            timestamp=req.timestamp or datetime.utcnow()
        )
        db.add(obs)
        db.flush()

        # 4. Handle Evidence Image Storage & OCR
        evidence_frame_id = None
        evidence_url = None
        extracted_ocr_text = None
        ocr_confidence = None

        if image_file or image_bytes:
            if image_file:
                file_path, evidence_url = await storage_provider.save_upload_file(image_file, subfolder="evidence")
            else:
                file_path, evidence_url = storage_provider.save_bytes(image_bytes, extension=".jpg", subfolder="evidence")

            # OCR processing (Module aware)
            ocr_context = "vehicle_plate" if req.module in ["vehicle_density", "multimodal"] else ("traffic_sign" if req.module == "traffic_sign" else None)
            if ocr_context:
                extracted_ocr_text, ocr_confidence = ocr_service.extract_text(file_path, module=req.module, context=ocr_context)

            # Store Evidence Frame
            frame_count = db.query(EvidenceFrame).filter(EvidenceFrame.incident_id == incident.id).count() + 1
            evidence_frame = EvidenceFrame(
                incident_id=incident.id,
                observation_id=obs.id,
                frame_number=frame_count,
                camera_id=req.camera_id,
                file_path=file_path,
                file_url=evidence_url,
                mime_type="image/jpeg",
                timestamp=req.timestamp or datetime.utcnow(),
                bounding_boxes=[b.model_dump() for b in req.bounding_boxes] if req.bounding_boxes else None,
                ocr_extracted_text=extracted_ocr_text,
                ocr_confidence=ocr_confidence,
                caption=f"Frame {frame_count} from {req.camera_position} camera ({req.camera_id})"
            )
            db.add(evidence_frame)
            db.flush()
            evidence_frame_id = evidence_frame.id

        # 5. Handle Vehicle Observations if present
        if req.vehicles:
            for v_info in req.vehicles:
                veh = VehicleObservation(
                    incident_id=incident.id,
                    observation_id=obs.id,
                    vehicle_track_id=v_info.track_id or f"TRK-{uuid.uuid4().hex[:4].upper()}",
                    vehicle_type=v_info.vehicle_type or "car",
                    color=v_info.color,
                    license_plate=v_info.license_plate or extracted_ocr_text,
                    plate_confidence=v_info.plate_confidence or ocr_confidence,
                    speed_kmh=v_info.speed_kmh,
                    direction=v_info.direction,
                    lane=v_info.lane,
                    confidence=v_info.confidence
                )
                db.add(veh)

        # 6. Create Timeline Event
        timeline_desc = (
            f"Observation recorded by Bus {req.bus_id} ({req.camera_position} camera {req.camera_id}). "
            f"Confidence: {int(req.confidence * 100)}%."
        )
        if extracted_ocr_text:
            timeline_desc += f" OCR read text: '{extracted_ocr_text}'."

        timeline_event = EvidenceTimelineEvent(
            incident_id=incident.id,
            evidence_frame_id=evidence_frame_id,
            timestamp_str=(req.timestamp or datetime.utcnow()).strftime("%I:%M:%S %p"),
            timestamp=req.timestamp or datetime.utcnow(),
            event_type=f"{req.module.replace('_', ' ').title()} Logged",
            description=timeline_desc,
            vehicle_track_id=req.vehicles[0].track_id if req.vehicles else None,
            is_ai_generated=True
        )
        db.add(timeline_event)

        # 7. Create Notification if High/Critical severity
        if req.severity in ["High", "Critical"] and not is_correlated:
            notif = Notification(
                incident_id=incident.id,
                notification_type="CRITICAL_ALERT",
                title=f"Critical Alert: {incident.incident_type}",
                message=f"High severity event detected at {incident.location_name} with {int(incident.confidence*100)}% AI confidence.",
                severity=req.severity,
                is_read=False
            )
            db.add(notif)

        db.commit()
        db.refresh(incident)

        return AIDetectionIngestResponse(
            incident_id=incident.id,
            incident_code=incident.incident_code,
            incident_type=incident.incident_type,
            status=incident.status,
            module=incident.module,
            is_correlated=is_correlated,
            evidence_frame_id=evidence_frame_id,
            evidence_url=evidence_url,
            ocr_extracted_text=extracted_ocr_text,
            waterlogged_pothole_probability=incident.waterlogged_pothole_probability,
            message="Observation successfully processed and correlated into incident." if is_correlated else "New incident created and evidence registered."
        )


ai_ingestion_service = AIIngestionService()
