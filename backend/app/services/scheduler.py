import json
import threading
import time
from datetime import datetime, timezone

from croniter import croniter
from structlog import get_logger

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.job import FuzzJob
from app.models.schedule import JobSchedule
from app.services.engine import run_fuzz_job

logger = get_logger(__name__)


class SchedulerService:
    """Background thread that polls for due schedules and creates jobs."""

    def __init__(self, check_interval: int = 30):
        self._check_interval = check_interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("scheduler_started", interval_seconds=self._check_interval)

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("scheduler_stopped")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as e:
                logger.error("scheduler_tick_error", error=str(e))
            self._stop_event.wait(self._check_interval)

    def _tick(self):
        db: Session = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            due = (
                db.query(JobSchedule)
                .filter(JobSchedule.is_active == True)
                .filter(JobSchedule.next_run_at <= now)
                .all()
            )
            for sched in due:
                try:
                    self._execute_schedule(db, sched, now)
                except Exception as e:
                    logger.error("schedule_execution_failed", schedule_id=sched.id, error=str(e))
                    db.rollback()
            self._check_completed_jobs(db)
        finally:
            db.close()

    def _execute_schedule(self, db, sched: JobSchedule, now: datetime):
        seed_ids = json.loads(sched.seed_ids) if sched.seed_ids else []

        job = FuzzJob(
            project_id=sched.project_id,
            strategy=sched.strategy,
            budget=sched.budget,
            judge=sched.judge,
            target_model=sched.target_model,
            status="created",
        )
        db.add(job)
        db.flush()

        sched.last_run_at = now
        sched.last_job_id = job.id
        try:
            sched.next_run_at = croniter(sched.cron_expression, now).get_next(datetime)
        except (ValueError, KeyError):
            sched.is_active = False
            sched.next_run_at = None

        db.commit()

        threading.Thread(target=run_fuzz_job, args=(job.id, seed_ids), daemon=True).start()
        logger.info("scheduled_job_created", job_id=job.id, schedule_id=sched.id, strategy=sched.strategy)

    def _check_completed_jobs(self, db: Session):
        """Check if any scheduled jobs have completed and if ASR threshold is breached."""
        from app.services.notifications import notify_threshold_breach

        schedules = (
            db.query(JobSchedule)
            .filter(JobSchedule.last_job_id.isnot(None))
            .filter(JobSchedule.asr_threshold.isnot(None))
            .all()
        )
        for sched in schedules:
            job = db.query(FuzzJob).filter(FuzzJob.id == sched.last_job_id).first()
            if job and job.status == "completed":
                if job.asr >= sched.asr_threshold:
                    alert = notify_threshold_breach(db, sched, job)
                    if alert.id:
                        db.commit()


scheduler_service = SchedulerService()
