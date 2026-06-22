import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class JudgmentResult(Base):
    __tablename__ = "judgment_results"

    id = Column(String, primary_key=True, default=lambda: f"judge_{uuid.uuid4().hex[:12]}")
    iteration_id = Column(String, ForeignKey("job_iterations.id"), nullable=False)
    response_id = Column(String, ForeignKey("target_responses.id"), nullable=False)
    classification = Column(String, nullable=False)
    confidence = Column(Float, default=0.0)
    explanation = Column(Text, default="")
    judge_model = Column(String, default="roberta")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    iteration = relationship("JobIteration", back_populates="judgment")
