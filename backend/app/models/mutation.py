import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MutatedTemplate(Base):
    __tablename__ = "mutated_templates"

    id = Column(String, primary_key=True, default=lambda: f"mut_{uuid.uuid4().hex[:12]}")
    iteration_id = Column(String, ForeignKey("job_iterations.id"), nullable=False)
    parent_seed_id = Column(String, ForeignKey("seed_templates.id"), nullable=False)
    mutation_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    conversation = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    iteration = relationship("JobIteration", back_populates="mutation")
    parent_seed = relationship("SeedTemplate", back_populates="mutations")
