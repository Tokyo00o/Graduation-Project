import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class JobIteration(Base):
    __tablename__ = "job_iterations"

    id = Column(String, primary_key=True, default=lambda: f"iter_{uuid.uuid4().hex[:12]}")
    job_id = Column(String, ForeignKey("fuzz_jobs.id"), nullable=False)
    iteration_number = Column(Integer, nullable=False)
    reward = Column(Float, default=0.0)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    job = relationship("FuzzJob", back_populates="iterations")
    mutation = relationship("MutatedTemplate", uselist=False, back_populates="iteration", cascade="all, delete-orphan")
    target_response = relationship("TargetResponse", uselist=False, back_populates="iteration", cascade="all, delete-orphan")
    judgment = relationship("JudgmentResult", uselist=False, back_populates="iteration", cascade="all, delete-orphan")
