from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _sched_id():
    return "sched_" + uuid.uuid4().hex[:12]


class JobSchedule(Base):
    __tablename__ = "job_schedules"

    id = Column(String, primary_key=True, default=_sched_id)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    name = Column(String(128), nullable=False)
    strategy = Column(String(32), default="random")
    budget = Column(Integer, default=100)
    judge = Column(String(32), default="roberta")
    target_model = Column(String(128), default="")
    seed_ids = Column(Text, default="[]")
    cron_expression = Column(String(64), default="0 0 * * *")
    is_active = Column(Boolean, default=True)
    asr_threshold = Column(Float, nullable=True)
    slack_webhook_url = Column(String(512), nullable=True)
    webhook_url = Column(String(512), nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    last_job_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="schedules")
