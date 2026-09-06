from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.incident import Incident
from app.models.road import Road
from app.models.vehicle import VehicleObservation
from app.models.camera import Camera
from app.schemas.search import SearchResultItem, UnifiedSearchResponse


class SearchService:
    @staticmethod
    def search_all(db: Session, query_str: str) -> UnifiedSearchResponse:
        if not query_str or not query_str.strip():
            return UnifiedSearchResponse(query=query_str, total_results=0, results=[])

        term = f"%{query_str.strip()}%"
        results: List[SearchResultItem] = []

        # 1. Incidents
        incidents = db.query(Incident).filter(
            or_(
                Incident.incident_code.ilike(term),
                Incident.incident_type.ilike(term),
                Incident.location_name.ilike(term),
                Incident.module.ilike(term)
            )
        ).limit(10).all()

        for inc in incidents:
            results.append(SearchResultItem(
                category="incident",
                id=inc.id,
                title=f"{inc.incident_code}: {inc.incident_type}",
                subtitle=f"{inc.location_name} • Severity: {inc.severity} • Status: {inc.status}",
                url_target=f"/incidents/{inc.incident_code}",
                metadata={"module": inc.module, "confidence": inc.confidence}
            ))

        # 2. Roads
        roads = db.query(Road).filter(
            or_(
                Road.code.ilike(term),
                Road.name.ilike(term),
                Road.zone.ilike(term)
            )
        ).limit(5).all()

        for r in roads:
            results.append(SearchResultItem(
                category="road",
                id=r.id,
                title=f"{r.name} ({r.code})",
                subtitle=f"Risk Score: {r.risk_score} • Status: {r.status} • Accidents: {r.accident_count}",
                url_target=f"/roads/{r.id}",
                metadata={"risk_score": r.risk_score, "traffic_index": r.traffic_index}
            ))

        # 3. Vehicles
        vehicles = db.query(VehicleObservation).filter(
            or_(
                VehicleObservation.vehicle_track_id.ilike(term),
                VehicleObservation.license_plate.ilike(term),
                VehicleObservation.color.ilike(term)
            )
        ).limit(5).all()

        for v in vehicles:
            results.append(SearchResultItem(
                category="vehicle",
                id=v.id,
                title=f"Vehicle {v.vehicle_track_id} ({v.vehicle_type.title()})",
                subtitle=f"Plate: {v.license_plate or 'Not Detected'} • Color: {v.color or 'N/A'}",
                url_target=f"/vehicles/{v.id}",
                metadata={"license_plate": v.license_plate}
            ))

        # 4. Cameras
        cameras = db.query(Camera).filter(
            or_(
                Camera.camera_code.ilike(term),
                Camera.location_name.ilike(term)
            )
        ).limit(5).all()

        for c in cameras:
            results.append(SearchResultItem(
                category="camera",
                id=c.id,
                title=f"Camera {c.camera_code}",
                subtitle=f"Location: {c.location_name} • Position: {c.camera_position} • Status: {c.status}",
                url_target=f"/cameras/{c.id}",
                metadata={"status": c.status}
            ))

        return UnifiedSearchResponse(
            query=query_str,
            total_results=len(results),
            results=results
        )


search_service = SearchService()
