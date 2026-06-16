from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base


class TargetModel(Base):
    __tablename__ = "target_models"

    id = Column(String, primary_key=True)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    label = Column(String, default="")
    api_key_encrypted = Column(String, default="")
    status = Column(String, default="inactive")
    total_queries = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
