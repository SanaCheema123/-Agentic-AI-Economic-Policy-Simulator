from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from backend.app.db.database import get_db
from backend.app.db.models import ScenarioRun, GeneratedReport

router = APIRouter(prefix="/api/reports", tags=["Downloadable Reports"])

def _build_pdf(row: ScenarioRun):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Economic Policy Scenario Report")
    styles = getSampleStyleSheet()
    story = [Paragraph("Economic Policy Scenario Report", styles["Title"]), Spacer(1, 12)]
    story.append(Paragraph(f"Country: {row.country} &nbsp;&nbsp; Policy: {row.policy_variable} &nbsp;&nbsp; Change: {row.change_percent:+.2f}% &nbsp;&nbsp; Horizon: {row.horizon} years", styles["BodyText"]))
    story.append(Spacer(1, 12))
    result = row.result or {}
    story.append(Paragraph(result.get("interpretation", "Model-based scenario analysis."), styles["BodyText"]))
    story.append(Spacer(1, 12))
    for key, target in result.get("targets", {}).items():
        story.append(Paragraph(target.get("target_name", key), styles["Heading2"]))
        data = [["Year", "Baseline", "Scenario", "Estimated impact"]]
        for item in target.get("results", []):
            data.append([item.get("year"), item.get("baseline_target"), item.get("scenario_target"), item.get("estimated_impact")])
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.lightgrey), ("GRID", (0,0), (-1,-1), 0.25, colors.grey), ("FONTSIZE", (0,0), (-1,-1), 8)]))
        story.extend([table, Spacer(1, 10)])
    story.append(Paragraph("Methodological note", styles["Heading2"]))
    story.append(Paragraph(result.get("disclaimer", "These are model-based estimates and not policy recommendations."), styles["BodyText"]))
    doc.build(story)
    buf.seek(0)
    return buf

@router.get("/{scenario_id}.pdf")
def download_report(scenario_id: int, db: Session = Depends(get_db)):
    row = db.get(ScenarioRun, scenario_id)
    if not row:
        raise HTTPException(404, "Scenario not found")
    report = GeneratedReport(scenario_id=row.id, title=f"Policy Scenario {row.id}", language="en", format="pdf", metadata_json={"country": row.country})
    db.add(report); db.commit()
    pdf = _build_pdf(row)
    return StreamingResponse(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="policy_scenario_{scenario_id}.pdf"'})
