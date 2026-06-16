import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: f"usr_{uuid.uuid4().hex[:12]}")
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, default="")
    role = Column(String(16), default="viewer")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
