import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: f"proj_{uuid.uuid4().hex[:12]}")
    name = Column(String, nullable=False)
    description = Column(String, default="")
    owner_id = Column(String, nullable=False, default="default")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    seeds = relationship("SeedTemplate", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("FuzzJob", back_populates="project", cascade="all, delete-orphan")
    schedules = relationship("JobSchedule", back_populates="project", cascade="all, delete-orphan")
