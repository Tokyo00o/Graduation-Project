import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class FuzzJob(Base):
    __tablename__ = "fuzz_jobs"

    id = Column(String, primary_key=True, default=lambda: f"job_{uuid.uuid4().hex[:12]}")
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    strategy = Column(String, nullable=False, default="random")
    status = Column(String, default="pending")
    budget = Column(Integer, default=1000)
    queries_used = Column(Integer, default=0)
    asr = Column(Float, default=0.0)
    target_model = Column(String, default="")
    judge = Column(String, default="roberta")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    project = relationship("Project", back_populates="jobs")
    iterations = relationship("JobIteration", back_populates="job", cascade="all, delete-orphan")
