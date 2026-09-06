from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.road import Road
from app.schemas.heatmap import HeatmapPoint, HeatmapResponse


class HeatmapService:
    @staticmethod
    def get_heatmap_points(
        db: Session,
        time_range: str = "7_days",
        risk_type: str = "all"
    ) -> HeatmapResponse:
        now = datetime.utcnow()
        if time_range == "today":
            start_date = now - timedelta(days=1)
        elif time_range == "30_days":
            start_date = now - timedelta(days=30)
        elif time_range == "3_months":
            start_date = now - timedelta(days=90)
        else:  # default 7_days
            start_date = now - timedelta(days=7)

        # Base query
        query = db.query(Incident).filter(Incident.detected_time >= start_date)

        # Module / risk type mapping
        if risk_type == "accidents":
            query = query.filter(Incident.incident_type.ilike("%hit-and-run%") | Incident.incident_type.ilike("%collision%") | Incident.incident_type.ilike("%accident%"))
        elif risk_type == "potholes":
            query = query.filter(Incident.module.in_(["road_defect", "pothole"]))
        elif risk_type == "waterlogging":
            query = query.filter(Incident.waterlogged_pothole_probability.isnot(None) | Incident.incident_type.ilike("%waterlog%"))
        elif risk_type == "traffic":
            query = query.filter(Incident.module.in_(["vehicle_density", "traffic_bottleneck"]))
        elif risk_type == "infrastructure":
            query = query.filter(Incident.module == "traffic_sign")

        incidents = query.all()
        points: List[HeatmapPoint] = []

        severity_weights = {
            "Critical": 1.0,
            "High": 0.8,
            "Medium": 0.5,
            "Low": 0.3
        }

        for inc in incidents:
            w = severity_weights.get(inc.severity, 0.5)
            # Map module to risk category
            cat = "accidents"
            if inc.module in ["road_defect", "pothole"]:
                cat = "waterlogging" if inc.waterlogged_pothole_probability else "potholes"
            elif inc.module in ["vehicle_density", "traffic_bottleneck"]:
                cat = "traffic"
            elif inc.module == "traffic_sign":
                cat = "infrastructure"

            points.append(
                HeatmapPoint(
                    latitude=inc.latitude,
                    longitude=inc.longitude,
                    weight=w,
                    risk_type=cat,
                    incident_code=inc.incident_code,
                    severity=inc.severity,
                    location_name=inc.location_name
                )
            )

        # Include Road hotspots if risk_type is all or traffic
        if risk_type in ["all", "traffic"]:
            roads = db.query(Road).filter(Road.risk_score >= 50.0).all()
            for r in roads:
                points.append(
                    HeatmapPoint(
                        latitude=r.latitude,
                        longitude=r.longitude,
                        weight=min(1.0, r.risk_score / 100.0),
                        risk_type="traffic" if r.traffic_index > 70 else "accidents",
                        incident_code=r.code,
                        severity="High" if r.risk_score >= 70 else "Medium",
                        location_name=r.name
                    )
                )

        return HeatmapResponse(
            time_range=time_range,
            risk_type=risk_type,
            total_points=len(points),
            points=points
        )


heatmap_service = HeatmapService()
