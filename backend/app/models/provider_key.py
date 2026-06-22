from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String

from app.database import Base


class ProviderKey(Base):
    __tablename__ = "provider_keys"

    provider = Column(String, primary_key=True)
    api_key_encrypted = Column(String, default="")
    label = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
