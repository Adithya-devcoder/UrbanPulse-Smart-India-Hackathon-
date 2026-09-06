import io
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.evidence import EvidenceFrame
from app.models.evidence_timeline import EvidenceTimelineEvent
from app.models.vehicle import VehicleObservation
from app.models.action import ActionItem
from app.core.errors import NotFoundException


class PDFReportService:
    @staticmethod
    def generate_incident_pdf(db: Session, identifier: str) -> io.BytesIO:
        # 1. Fetch incident & related entities
        if identifier.isdigit():
            incident = db.query(Incident).filter(Incident.id == int(identifier)).first()
        else:
            incident = db.query(Incident).filter(Incident.incident_code == identifier).first()
            if not incident:
                incident = db.query(Incident).filter(Incident.incident_code == f"INC-{identifier}").first()

        if not incident:
            raise NotFoundException(resource="Incident", identifier=identifier)

        evidence_frames = db.query(EvidenceFrame).filter(EvidenceFrame.incident_id == incident.id).all()
        timeline_events = db.query(EvidenceTimelineEvent).filter(EvidenceTimelineEvent.incident_id == incident.id).order_by(EvidenceTimelineEvent.timestamp).all()
        vehicles = db.query(VehicleObservation).filter(VehicleObservation.incident_id == incident.id).all()
        actions = db.query(ActionItem).filter(ActionItem.incident_id == incident.id).all()

        # 2. Setup Document buffer & styles
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        primary_color = colors.HexColor("#0f172a")     # Slate 900
        brand_blue = colors.HexColor("#2563eb")        # Blue 600
        accent_red = colors.HexColor("#dc2626")        # Red 600
        bg_light = colors.HexColor("#f8fafc")          # Slate 50
        border_color = colors.HexColor("#e2e8f0")      # Slate 200

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=primary_color
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=brand_blue
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=primary_color,
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155")
        )
        body_bold = ParagraphStyle(
            "BodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )
        disclaimer_style = ParagraphStyle(
            "Disclaimer",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b")
        )

        story = []

        # Header Table: Title & Metadata
        header_data = [
            [
                Paragraph("<b>URBANPULSE</b><br/><font size=8 color='#2563eb'>AI-POWERED URBAN ROAD INTELLIGENCE</font>", title_style),
                Paragraph(f"<b>INCIDENT DOSSIER</b><br/><b>Ref:</b> {incident.incident_code}<br/><b>Generated:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", body_style)
            ]
        ]
        header_table = Table(header_data, colWidths=[340, 200])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5, color=brand_blue, spaceBefore=2, spaceAfter=8))

        # AI Assessment Notice Banner
        ai_banner_data = [[
            Paragraph("<b>⚠️ NOTICE — AI-GENERATED ASSESSMENT:</b> This report contains automated multi-camera computer vision detections and probabilistic sensor fusion analytics. It serves as actionable intelligence for municipal traffic authorities and does not represent legally binding court determinations.", disclaimer_style)
        ]]
        ai_banner_table = Table(ai_banner_data, colWidths=[540])
        ai_banner_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#f59e0b")),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(ai_banner_table)
        story.append(Spacer(1, 10))

        # Core Incident Summary Table
        story.append(Paragraph("1. INCIDENT OVERVIEW", h2_style))
        sev_color = accent_red if incident.severity in ["High", "Critical"] else colors.HexColor("#d97706")
        
        summary_rows = [
            [
                Paragraph("<b>Incident ID:</b>", body_style), Paragraph(incident.incident_code, body_bold),
                Paragraph("<b>Module:</b>", body_style), Paragraph(incident.module.replace("_", " ").title(), body_style)
            ],
            [
                Paragraph("<b>Incident Type:</b>", body_style), Paragraph(incident.incident_type, body_bold),
                Paragraph("<b>Current Status:</b>", body_style), Paragraph(f"<b>{incident.status}</b>", body_bold)
            ],
            [
                Paragraph("<b>Severity:</b>", body_style), Paragraph(f"<font color='{sev_color.hexval()}'><b>{incident.severity}</b></font>", body_style),
                Paragraph("<b>AI Confidence:</b>", body_style), Paragraph(f"<b>{int(incident.confidence * 100)}%</b>", body_bold)
            ],
            [
                Paragraph("<b>Location:</b>", body_style), Paragraph(incident.location_name, body_style),
                Paragraph("<b>Coordinates:</b>", body_style), Paragraph(f"{incident.latitude:.5f}, {incident.longitude:.5f}", body_style)
            ],
            [
                Paragraph("<b>Detected At:</b>", body_style), Paragraph(incident.detected_time.strftime("%Y-%m-%d %I:%M:%S %p"), body_style),
                Paragraph("<b>Waterlogged Prob:</b>", body_style), Paragraph(f"{int(incident.waterlogged_pothole_probability * 100)}%" if incident.waterlogged_pothole_probability else "N/A", body_style)
            ]
        ]
        summary_table = Table(summary_rows, colWidths=[95, 175, 110, 160])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_light),
            ('BOX', (0,0), (-1,-1), 1, border_color),
            ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 10))

        # AI Event Reconstruction Narrative
        if incident.assessment_text:
            story.append(Paragraph("2. AI EVENT RECONSTRUCTION", h2_style))
            narrative_data = [[
                Paragraph(f"<b>Synthesized Narrative:</b><br/>{incident.assessment_text}", body_style)
            ]]
            narrative_table = Table(narrative_data, colWidths=[540])
            narrative_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#eff6ff")),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#bfdbfe")),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ]))
            story.append(narrative_table)
            story.append(Spacer(1, 10))

        # Vehicles Involved & OCR Recognition
        if vehicles:
            story.append(Paragraph("3. VEHICLE INTELLIGENCE & OCR EXTRACTION", h2_style))
            veh_headers = [
                Paragraph("<b>Vehicle ID</b>", body_bold),
                Paragraph("<b>Type & Color</b>", body_bold),
                Paragraph("<b>License Plate (OCR)</b>", body_bold),
                Paragraph("<b>Plate Conf.</b>", body_bold),
                Paragraph("<b>Speed / Direction</b>", body_bold)
            ]
            veh_table_data = [veh_headers]
            for v in vehicles:
                veh_table_data.append([
                    Paragraph(v.vehicle_track_id, body_style),
                    Paragraph(f"{(v.vehicle_type or 'Car').title()} ({v.color or 'N/A'})", body_style),
                    Paragraph(f"<b>{v.license_plate or 'Not legible'}</b>", body_style),
                    Paragraph(f"{int((v.plate_confidence or 0.85)*100)}%" if v.license_plate else "-", body_style),
                    Paragraph(f"{v.speed_kmh or 0:.0f} km/h • {v.direction or 'N/A'}", body_style),
                ])
            veh_table = Table(veh_table_data, colWidths=[90, 110, 140, 75, 125])
            veh_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
                ('BOX', (0,0), (-1,-1), 1, border_color),
                ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(veh_table)
            story.append(Spacer(1, 10))

        # Evidence Timeline
        if timeline_events:
            story.append(Paragraph("4. CHRONOLOGICAL EVIDENCE TIMELINE", h2_style))
            tl_headers = [
                Paragraph("<b>Time</b>", body_bold),
                Paragraph("<b>Event Type</b>", body_bold),
                Paragraph("<b>Description / Observations</b>", body_bold),
                Paragraph("<b>Source</b>", body_bold)
            ]
            tl_rows = [tl_headers]
            for ev in timeline_events:
                tl_rows.append([
                    Paragraph(ev.timestamp_str, body_style),
                    Paragraph(f"<b>{ev.event_type}</b>", body_style),
                    Paragraph(ev.description, body_style),
                    Paragraph("AI Engine" if ev.is_ai_generated else "Officer", body_style)
                ])
            tl_table = Table(tl_rows, colWidths=[75, 115, 275, 75])
            tl_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
                ('BOX', (0,0), (-1,-1), 1, border_color),
                ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(tl_table)
            story.append(Spacer(1, 10))

        # Action / Response Center Status
        if actions:
            story.append(Paragraph("5. ACTION DISPATCH & RESPONSE", h2_style))
            act_headers = [
                Paragraph("<b>Action Code</b>", body_bold),
                Paragraph("<b>Assigned Unit</b>", body_bold),
                Paragraph("<b>Priority</b>", body_bold),
                Paragraph("<b>Status</b>", body_bold),
                Paragraph("<b>ETA</b>", body_bold)
            ]
            act_rows = [act_headers]
            for a in actions:
                act_rows.append([
                    Paragraph(a.action_code, body_style),
                    Paragraph(a.assigned_team, body_style),
                    Paragraph(a.priority, body_style),
                    Paragraph(f"<b>{a.status}</b>", body_bold),
                    Paragraph(f"{a.eta_minutes} mins" if a.eta_minutes else "-", body_style)
                ])
            act_table = Table(act_rows, colWidths=[90, 160, 90, 110, 90])
            act_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
                ('BOX', (0,0), (-1,-1), 1, border_color),
                ('INNERGRID', (0,0), (-1,-1), 0.5, border_color),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(act_table)
            story.append(Spacer(1, 10))

        # Embedded Evidence Frame snapshot if available
        if evidence_frames:
            first_frame = evidence_frames[0]
            img_path = Path(first_frame.file_path)
            if img_path.exists() and img_path.is_file():
                try:
                    story.append(KeepTogether([
                        Paragraph("6. KEY EVIDENCE VISUAL FRAME", h2_style),
                        RLImage(str(img_path), width=320, height=180),
                        Paragraph(f"<i>Evidence Snapshot: {first_frame.caption or 'Frame #1'} (Camera: {first_frame.camera_id})</i>", disclaimer_style),
                        Spacer(1, 6)
                    ]))
                except Exception:
                    pass

        # Build document
        doc.build(story)
        buffer.seek(0)
        return buffer


pdf_report_service = PDFReportService()
