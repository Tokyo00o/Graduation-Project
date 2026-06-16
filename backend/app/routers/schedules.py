from datetime import datetime, timezone
from typing import List

from croniter import croniter
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.project import Project
from app.models.schedule import JobSchedule
from app.routers.jobs import _get_project
from app.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleUpdate
from app.schemas.common import StatusResponse
from app.services.auth import get_current_user
from app.services.engine import run_fuzz_job
from app.services.notifications import send_slack_alert, send_webhook_alert

router = APIRouter(prefix="/api/v1", tags=["Schedules"], dependencies=[Depends(get_current_user)])


def _next_run(cron_expr: str) -> datetime:
    try:
        base = datetime.now(timezone.utc)
        cron = croniter(cron_expr, base)
        return cron.get_next(datetime)
    except (ValueError, KeyError):
        raise HTTPException(400, f"Invalid cron expression: {cron_expr}")


@router.get("/projects/{project_id}/schedules", response_model=List[ScheduleResponse])
def list_schedules(project_id: str, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    return db.query(JobSchedule).filter(JobSchedule.project_id == project_id).all()


@router.post("/projects/{project_id}/schedules", response_model=ScheduleResponse, status_code=201)
def create_schedule(project_id: str, payload: ScheduleCreate, db: Session = Depends(get_db)):
    _get_project(project_id, db)
    next_run = _next_run(payload.cron_expression) if payload.is_active else None
    schedule = JobSchedule(
        project_id=project_id,
        name=payload.name,
        strategy=payload.strategy,
        budget=payload.budget,
        judge=payload.judge,
        target_model=payload.target_model,
        seed_ids=str(payload.seed_ids),
        cron_expression=payload.cron_expression,
        is_active=payload.is_active,
        asr_threshold=payload.asr_threshold,
        slack_webhook_url=payload.slack_webhook_url,
        webhook_url=payload.webhook_url,
        next_run_at=next_run,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("/schedules/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    schedule = db.query(JobSchedule).filter(JobSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    return schedule


@router.put("/schedules/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(schedule_id: str, payload: ScheduleUpdate, db: Session = Depends(get_db)):
    schedule = db.query(JobSchedule).filter(JobSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(schedule, field, value)
    if payload.cron_expression is not None or payload.is_active is not None:
        schedule.next_run_at = _next_run(schedule.cron_expression) if schedule.is_active else None
    schedule.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/schedules/{schedule_id}", response_model=StatusResponse)
def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    schedule = db.query(JobSchedule).filter(JobSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    db.delete(schedule)
    db.commit()
    return StatusResponse(status="deleted")


@router.post("/schedules/{schedule_id}/toggle", response_model=ScheduleResponse)
def toggle_schedule(schedule_id: str, db: Session = Depends(get_db)):
    schedule = db.query(JobSchedule).filter(JobSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    schedule.is_active = not schedule.is_active
    schedule.next_run_at = _next_run(schedule.cron_expression) if schedule.is_active else None
    schedule.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.post("/schedules/{schedule_id}/run-now", response_model=StatusResponse)
def run_schedule_now(schedule_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    schedule = db.query(JobSchedule).filter(JobSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    from app.models.job import FuzzJob
    import json
    job = FuzzJob(
        project_id=schedule.project_id,
        strategy=schedule.strategy,
        budget=schedule.budget,
        judge=schedule.judge,
        target_model=schedule.target_model,
        status="created",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    seed_ids = json.loads(schedule.seed_ids) if schedule.seed_ids else []
    background_tasks.add_task(run_fuzz_job, job.id, seed_ids)
    schedule.last_run_at = datetime.now(timezone.utc)
    schedule.last_job_id = job.id
    db.commit()
    return StatusResponse(status="ok", data={"job_id": job.id})


@router.post("/schedules/{schedule_id}/test-notification", response_model=StatusResponse)
def test_schedule_notification(schedule_id: str, db: Session = Depends(get_db)):
    schedule = db.query(JobSchedule).filter(JobSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(404, "Schedule not found")
    from datetime import datetime, timezone
    data = {
        "job_id": "test_job_000000000000",
        "schedule_id": schedule.id,
        "project_id": schedule.project_id,
        "asr": 0.75,
        "threshold": schedule.asr_threshold or 0.5,
        "severity": "warning",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    message = f"[TEST] Schedule '{schedule.name}' — simulated ASR threshold breach"
    results = {"slack": False, "webhook": False}
    if schedule.slack_webhook_url:
        results["slack"] = send_slack_alert(schedule.slack_webhook_url, message, data)
    if schedule.webhook_url:
        results["webhook"] = send_webhook_alert(schedule.webhook_url, message, data)
    if not schedule.slack_webhook_url and not schedule.webhook_url:
        return StatusResponse(status="skipped", message="No notification channels configured")
    ok = results.get("slack", False) or results.get("webhook", False)
    return StatusResponse(status="ok" if ok else "failed", data=results)
