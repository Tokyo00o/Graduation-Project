import csv
import io
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.iteration import JobIteration
from app.models.job import FuzzJob
from app.models.judgment import JudgmentResult
from app.models.mutation import MutatedTemplate
from app.models.project import Project
from app.models.response import TargetResponse
from app.services.judgment.metrics import ASRMetrics
from app.services.compliance import FRAMEWORKS, build_compliance_report, analyze_iteration
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"], dependencies=[Depends(get_current_user)])


class IterationExport(BaseModel):
    iteration_number: int
    mutation_type: str
    mutated_content: str
    parent_seed_content: str
    response: str
    latency: float
    classification: str
    confidence: float
    explanation: str
    judge_model: str
    reward: float


class ReportSummary(BaseModel):
    job_id: str
    project_id: str
    project_name: str
    strategy: str
    status: str
    budget: int
    queries_used: int
    asr: float
    target_model: str
    judge: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ReportFull(BaseModel):
    summary: ReportSummary
    metrics: dict
    top_jailbreaks: List[IterationExport]
    worst_performers: List[IterationExport]
    iterations: List[IterationExport]


def _load_iterations(job_id: str, db: Session) -> List[IterationExport]:
    iterations = (
        db.query(JobIteration)
        .filter(JobIteration.job_id == job_id)
        .order_by(JobIteration.iteration_number.asc())
        .all()
    )
    result = []
    for it in iterations:
        mutation = (
            db.query(MutatedTemplate)
            .filter(MutatedTemplate.iteration_id == it.id)
            .first()
        )
        resp = (
            db.query(TargetResponse)
            .filter(TargetResponse.iteration_id == it.id)
            .first()
        )
        judgment = (
            db.query(JudgmentResult)
            .filter(JudgmentResult.iteration_id == it.id)
            .first()
        )
        parent_content = ""
        if mutation and mutation.parent_seed_id:
            from app.models.seed import SeedTemplate
            seed = db.query(SeedTemplate).filter(SeedTemplate.id == mutation.parent_seed_id).first()
            if seed:
                parent_content = seed.content
        result.append(IterationExport(
            iteration_number=it.iteration_number,
            mutation_type=mutation.mutation_type if mutation else "unknown",
            mutated_content=mutation.content if mutation else "",
            parent_seed_content=parent_content,
            response=resp.response if resp else "",
            latency=resp.latency if resp else 0.0,
            classification=judgment.classification if judgment else "unknown",
            confidence=judgment.confidence if judgment else 0.0,
            explanation=judgment.explanation if judgment else "",
            judge_model=judgment.judge_model if judgment else "",
            reward=it.reward,
        ))
    return result


def _get_job_with_project(job_id: str, db: Session):
    job = db.query(FuzzJob).filter(FuzzJob.id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")
    project = db.query(Project).filter(Project.id == job.project_id).first()
    return job, project


@router.get("/frameworks")
def list_frameworks():
    return {
        key: {"name": fw["name"], "version": fw["version"], "url": fw["url"]}
        for key, fw in FRAMEWORKS.items()
    }


@router.get("/{job_id}")
def get_report(job_id: str, db: Session = Depends(get_db)):
    job, project = _get_job_with_project(job_id, db)
    iterations = _load_iterations(job_id, db)
    metrics = ASRMetrics(db, job_id).full_report()

    by_class = {"full_compliance": [], "partial_compliance": [], "partial_refusal": [], "full_refusal": []}
    for it in iterations:
        by_class.setdefault(it.classification, []).append(it)
        if it.classification in by_class:
            by_class[it.classification].append(it)

    top_jailbreaks = sorted(by_class.get("full_compliance", []), key=lambda x: x.confidence, reverse=True)[:10]
    worst_performers = sorted(iterations, key=lambda x: x.reward)[:5]

    summary = ReportSummary(
        job_id=job.id,
        project_id=job.project_id,
        project_name=project.name if project else "",
        strategy=job.strategy,
        status=job.status,
        budget=job.budget,
        queries_used=job.queries_used,
        asr=job.asr,
        target_model=job.target_model,
        judge=job.judge,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
    )
    return ReportFull(
        summary=summary,
        metrics=metrics,
        top_jailbreaks=top_jailbreaks,
        worst_performers=worst_performers,
        iterations=iterations,
    )


@router.get("/{job_id}/export/json")
def export_json(job_id: str, db: Session = Depends(get_db)):
    job, project = _get_job_with_project(job_id, db)
    iterations = _load_iterations(job_id, db)
    metrics = ASRMetrics(db, job_id).full_report()

    data = {
        "report_generated": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "job_id": job.id,
            "project": project.name if project else "",
            "strategy": job.strategy,
            "status": job.status,
            "budget": job.budget,
            "queries_used": job.queries_used,
            "asr": job.asr,
            "target_model": job.target_model,
            "judge": job.judge,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        },
        "metrics": metrics,
        "iterations": [it.model_dump() for it in iterations],
    }
    import json
    return PlainTextResponse(
        json.dumps(data, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="report_{job_id}.json"'},
    )


@router.get("/{job_id}/export/csv")
def export_csv(job_id: str, db: Session = Depends(get_db)):
    job, _ = _get_job_with_project(job_id, db)
    iterations = _load_iterations(job_id, db)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "iteration", "mutation_type", "mutated_content", "parent_seed",
        "response", "latency", "classification", "confidence",
        "explanation", "judge_model", "reward",
    ])
    for it in iterations:
        writer.writerow([
            it.iteration_number, it.mutation_type, it.mutated_content,
            it.parent_seed_content, it.response, it.latency,
            it.classification, it.confidence, it.explanation,
            it.judge_model, it.reward,
        ])

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="report_{job_id}.csv"'},
    )


@router.get("/{job_id}/export/html")
def export_html(job_id: str, db: Session = Depends(get_db)):
    job, project = _get_job_with_project(job_id, db)
    iterations = _load_iterations(job_id, db)
    metrics = ASRMetrics(db, job_id).full_report()

    rows_html = ""
    for it in iterations:
        rows_html += f"""<tr>
          <td>{it.iteration_number}</td>
          <td>{it.mutation_type}</td>
          <td class="pre">{it.mutated_content[:120]}</td>
          <td class="pre">{it.response[:120]}</td>
          <td>{it.classification}</td>
          <td>{it.confidence}</td>
          <td>{it.reward}</td>
        </tr>"""

    top_jb = ""
    for it in sorted(iterations, key=lambda x: x.confidence, reverse=True)[:5]:
        if it.classification == "full_compliance":
            top_jb += f"<li><strong>Mutated:</strong> {it.mutated_content[:100]}<br><strong>Response:</strong> {it.response[:100]}<br><strong>Confidence:</strong> {it.confidence}</li>"

    classifications = metrics.get("by_classification", {})
    class_rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>"
        for k, v in sorted(classifications.items())
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>FuzzGuard Report — {job_id}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; color: #222; background: #fff; }}
  h1, h2, h3 {{ color: #111; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th, td {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #ddd; font-size: 13px; }}
  th {{ background: #f5f5f5; font-weight: 600; }}
  .pre {{ font-family: 'SFMono-Regular', Consolas, monospace; font-size: 12px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .summary {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; margin: 1rem 0; }}
  .stat {{ background: #f9f9f9; border-radius: 8px; padding: 1rem; text-align: center; }}
  .stat-value {{ font-size: 1.5rem; font-weight: 700; color: #2563eb; }}
  .stat-label {{ font-size: 0.75rem; color: #666; text-transform: uppercase; }}
  .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 11px; }}
  .badge-green {{ background: #d1fae5; color: #065f46; }}
  .badge-red {{ background: #fee2e2; color: #991b1b; }}
  .badge-yellow {{ background: #fef3c7; color: #92400e; }}
  .footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #eee; font-size: 12px; color: #888; text-align: center; }}
</style>
</head>
<body>
  <h1>FuzzGuard Report</h1>
  <p style="color:#666;">Job <code>{job_id}</code> — Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>

  <h2>Summary</h2>
  <div class="summary">
    <div class="stat"><div class="stat-value">{metrics.get('asr_top1', 0)*100:.1f}%</div><div class="stat-label">ASR (Top-1)</div></div>
    <div class="stat"><div class="stat-value">{metrics.get('asr_top5', 0)*100:.1f}%</div><div class="stat-label">ASR (Top-5)</div></div>
    <div class="stat"><div class="stat-value">{metrics.get('mean_asr', 0)*100:.1f}%</div><div class="stat-label">Mean ASR</div></div>
    <div class="stat"><div class="stat-value">{metrics.get('total_iterations', 0)}</div><div class="stat-label">Iterations</div></div>
  </div>

  <table>
    <tr><th>Property</th><th>Value</th></tr>
    <tr><td>Project</td><td>{project.name if project else '—'}</td></tr>
    <tr><td>Strategy</td><td>{job.strategy}</td></tr>
    <tr><td>Status</td><td><span class="badge badge-{'green' if job.status == 'completed' else 'red' if job.status == 'failed' else 'yellow'}">{job.status}</span></td></tr>
    <tr><td>Target Model</td><td>{job.target_model}</td></tr>
    <tr><td>Judge</td><td>{job.judge}</td></tr>
    <tr><td>Budget / Used</td><td>{job.budget} / {job.queries_used}</td></tr>
  </table>

  <h2>Classification Breakdown</h2>
  <table><tr><th>Classification</th><th>Count</th></tr>{class_rows}</table>

  <h2>Top Jailbreaks</h2>
  {"<ol>" + top_jb + "</ol>" if top_jb else "<p>No jailbreaks found.</p>"}

  <h2>All Iterations</h2>
  <table>
    <thead><tr><th>#</th><th>Mutation</th><th>Mutated</th><th>Response</th><th>Class</th><th>Conf</th><th>Reward</th></tr></thead>
    <tbody>{rows_html}</tbody>
  </table>

  <div class="footer">Generated by FuzzGuard</div>
</body>
</html>"""
    return PlainTextResponse(
        html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="report_{job_id}.html"'},
    )


@router.get("/summary/all")
def get_summary(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
):
    jobs = (
        db.query(FuzzJob)
        .order_by(FuzzJob.created_at.desc())
        .limit(limit)
        .all()
    )
    projects = {p.id: p for p in db.query(Project).all()}
    results = []
    for job in jobs:
        metrics = ASRMetrics(db, job.id).full_report() if job.status == "completed" else {}
        results.append({
            "job_id": job.id,
            "project_id": job.project_id,
            "project_name": getattr(projects.get(job.project_id), "name", ""),
            "strategy": job.strategy,
            "status": job.status,
            "budget": job.budget,
            "queries_used": job.queries_used,
            "asr": job.asr,
            "target_model": job.target_model,
            "judge": job.judge,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "metrics": metrics,
        })
    return results


@router.get("/{job_id}/compliance")
def get_compliance_report(job_id: str, db: Session = Depends(get_db)):
    job, project = _get_job_with_project(job_id, db)
    iterations_raw = (
        db.query(JobIteration)
        .filter(JobIteration.job_id == job_id)
        .order_by(JobIteration.iteration_number.asc())
        .all()
    )
    iterations = _load_iterations(job_id, db)
    metrics = ASRMetrics(db, job_id).full_report()
    compliance = build_compliance_report(
        {"job_id": job.id, "project": project.name if project else ""},
        metrics,
        iterations,
    )
    return compliance


@router.get("/{job_id}/export/pdf")
def export_pdf(job_id: str, db: Session = Depends(get_db)):
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    job, project = _get_job_with_project(job_id, db)
    iterations = _load_iterations(job_id, db)
    metrics = ASRMetrics(db, job_id).full_report()
    compliance = build_compliance_report(
        {"job_id": job.id, "project": project.name if project else ""},
        metrics,
        iterations,
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            topMargin=0.5*inch, bottomMargin=0.5*inch,
                            leftMargin=0.6*inch, rightMargin=0.6*inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("SectionHead", parent=styles["Heading2"], spaceBefore=16, spaceAfter=6, textColor=HexColor("#1e293b")))
    styles.add(ParagraphStyle("SmallText", parent=styles["Normal"], fontSize=8, textColor=HexColor("#64748b")))
    styles.add(ParagraphStyle("MonoText", parent=styles["Normal"], fontName="Courier", fontSize=7.5))
    styles.add(ParagraphStyle("CenterHead", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle("ScoreStyle", parent=styles["Normal"], fontSize=28, alignment=TA_CENTER, textColor=HexColor("#2563eb")))

    elements = []

    elements.append(Paragraph("FuzzGuard", styles["CenterHead"]))
    elements.append(Paragraph(f"Red-Teaming Report — {job_id}", styles["CenterHead"]))
    elements.append(Paragraph(f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["SmallText"]))
    elements.append(Spacer(1, 12))

    elements.append(HRFlowable(width="100%", color=HexColor("#e2e8f0")))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("Summary", styles["SectionHead"]))
    summary_data = [
        ["Property", "Value"],
        ["Project", project.name if project else "—"],
        ["Strategy", job.strategy],
        ["Status", job.status],
        ["Target Model", job.target_model],
        ["Judge", job.judge],
        ["Budget", str(job.budget)],
        ["Queries Used", str(job.queries_used)],
    ]
    summary_table = Table(summary_data, colWidths=[2*inch, 3.5*inch])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#1e293b")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Attack Success Rate", styles["SectionHead"]))
    asr_data = [
        ["Metric", "Value"],
        ["ASR (Top-1)", f"{metrics.get('asr_top1', 0)*100:.1f}%"],
        ["ASR (Top-5)", f"{metrics.get('asr_top5', 0)*100:.1f}%"],
        ["Mean ASR", f"{metrics.get('mean_asr', 0)*100:.1f}%"],
        ["Total Iterations", str(metrics.get("total_iterations", 0))],
    ]
    asr_table = Table(asr_data, colWidths=[2*inch, 2*inch])
    asr_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#1e293b")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(asr_table)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Classification Breakdown", styles["SectionHead"]))
    class_counts = metrics.get("by_classification", {})
    class_data = [["Classification", "Count"]]
    for cls, cnt in sorted(class_counts.items()):
        class_data.append([cls.replace("_", " ").title(), str(cnt)])
    if len(class_data) == 1:
        class_data.append(["No data", "0"])
    class_table = Table(class_data, colWidths=[3*inch, 1*inch])
    class_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(class_table)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Compliance Mapping", styles["SectionHead"]))
    score = compliance.get("overall_compliance_score", 100)
    elements.append(Paragraph(f"Overall Score: {score}%", ParagraphStyle("ScoreLine", parent=styles["Normal"], fontSize=14, textColor=HexColor("#2563eb"), alignment=TA_CENTER)))
    elements.append(Spacer(1, 8))

    for fw_key, fw_info in compliance.get("frameworks", {}).items():
        elements.append(Paragraph(f"<b>{fw_info['name']}</b> (v{fw_info['version']}) — Score: {fw_info['compliance_score']}%", styles["SectionHead"]))
        fw_data = [["Category", "Findings", "Max Severity"]]
        for cat_id, cat_info in fw_info.get("categories", {}).items():
            fw_data.append([f"{cat_id}: {cat_info['title']}", str(cat_info["finding_count"]), cat_info["max_severity"].title()])
        if len(fw_data) > 1:
            fw_table = Table(fw_data, colWidths=[2.8*inch, 0.7*inch, 1*inch])
            fw_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(fw_table)
        else:
            elements.append(Paragraph("No findings for this framework.", styles["SmallText"]))
        elements.append(Spacer(1, 8))

    elements.append(PageBreak())
    elements.append(Paragraph("Top Jailbreaks", styles["SectionHead"]))
    jailbreaks = [it for it in iterations if it.classification == "full_compliance"]
    if jailbreaks:
        jb_data = [["#", "Mutation", "Confidence", "Response (truncated)"]]
        for i, jb in enumerate(jailbreaks[:10], 1):
            jb_data.append([
                str(i),
                jb.mutation_type,
                f"{jb.confidence:.2f}",
                jb.response[:80] + ("..." if len(jb.response) > 80 else ""),
            ])
        jb_table = Table(jb_data, colWidths=[0.3*inch, 1*inch, 0.7*inch, 3.5*inch])
        jb_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#fee2e2")),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(jb_table)
    else:
        elements.append(Paragraph("No jailbreaks detected.", styles["Normal"]))

    elements.append(Spacer(1, 16))
    elements.append(Paragraph("All Iterations (first 50)", styles["SectionHead"]))
    iter_data = [["#", "Type", "Class", "Conf", "Reward"]]
    for it in iterations[:50]:
        iter_data.append([
            str(it.iteration_number),
            it.mutation_type,
            it.classification.replace("_", " ").title(),
            f"{it.confidence:.2f}",
            f"{it.reward:.2f}",
        ])
    iter_table = Table(iter_data, colWidths=[0.3*inch, 0.8*inch, 1.2*inch, 0.5*inch, 0.5*inch])
    iter_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(iter_table)

    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", color=HexColor("#e2e8f0")))
    elements.append(Paragraph(f"Generated by FuzzGuard — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", styles["SmallText"]))

    doc.build(elements)
    pdf_bytes = buf.getvalue()
    buf.close()

    return PlainTextResponse(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="report_{job_id}.pdf"'},
    )
