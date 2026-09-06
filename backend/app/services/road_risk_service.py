from typing import Optional
from sqlalchemy.orm import Session
from app.models.road import Road, RoadSegment


class RoadRiskService:
    @staticmethod
    def calculate_risk_score(
        accident_count: int,
        pothole_count: int,
        waterlogging_count: int,
        traffic_index: float,
        avg_response_time_min: float
    ) -> float:
        """
        Multi-factor risk score calculation (0 - 100).
        Accidents (weight 12), Potholes (weight 4), Waterlogging (weight 8),
        Traffic index (weight 0.25), Response time penalty.
        """
        score = (
            (accident_count * 12.0) +
            (pothole_count * 4.0) +
            (waterlogging_count * 8.0) +
            (traffic_index * 0.25) +
            (max(0.0, avg_response_time_min - 15.0) * 0.5)
        )
        return min(100.0, round(score, 1))

    @staticmethod
    def determine_status(risk_score: float) -> str:
        if risk_score >= 70.0:
            return "High Risk"
        elif risk_score >= 40.0:
            return "Moderate"
        return "Safe"

    @classmethod
    def update_road_metrics(cls, db: Session, road_id: int) -> Optional[Road]:
        road = db.query(Road).filter(Road.id == road_id).first()
        if not road:
            return None

        # Recalculate dynamic risk
        road.risk_score = cls.calculate_risk_score(
            accident_count=road.accident_count,
            pothole_count=road.pothole_count,
            waterlogging_count=road.waterlogging_count,
            traffic_index=road.traffic_index,
            avg_response_time_min=road.average_response_time_min
        )
        road.status = cls.determine_status(road.risk_score)
        
        # Historical trend determination
        if road.risk_score > 75:
            road.historical_trend = "worsening"
        elif road.risk_score < 35:
            road.historical_trend = "improving"
        else:
            road.historical_trend = "stable"

        db.commit()
        db.refresh(road)
        return road


road_risk_service = RoadRiskService()
