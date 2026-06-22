import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class TargetResponse(Base):
    __tablename__ = "target_responses"

    id = Column(String, primary_key=True, default=lambda: f"resp_{uuid.uuid4().hex[:12]}")
    iteration_id = Column(String, ForeignKey("job_iterations.id"), nullable=False)
    template_id = Column(String, ForeignKey("mutated_templates.id"), nullable=False)
    response = Column(Text, default="")
    latency = Column(Float, default=0.0)
    status_code = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    iteration = relationship("JobIteration", back_populates="target_response")
