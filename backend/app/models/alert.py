from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _alert_id():
    return "alert_" + uuid.uuid4().hex[:12]


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=_alert_id)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    schedule_id = Column(String, ForeignKey("job_schedules.id"), nullable=True)
    job_id = Column(String, ForeignKey("fuzz_jobs.id"), nullable=True)
    type = Column(String(32), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(16), default="warning")
    data = Column(Text, default="{}")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
