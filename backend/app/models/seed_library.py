import json
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.database import Base


class SeedLibraryItem(Base):
    __tablename__ = "seed_library"

    id = Column(String, primary_key=True, default=lambda: f"lib_{uuid.uuid4().hex[:12]}")
    content = Column(Text, nullable=False)
    category = Column(String(64), nullable=False, index=True)
    tags = Column(String, default="")
    difficulty = Column(String(16), default="medium")
    effectiveness = Column(Float, default=0.0)
    source = Column(String, default="")
    is_preset = Column(Boolean, default=False)
    is_multi_turn = Column(Boolean, default=False)
    conversation = Column(Text, default="")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def get_conversation(self) -> List[dict]:
        if self.conversation:
            try:
                return json.loads(self.conversation)
            except (json.JSONDecodeError, TypeError):
                pass
        return []

    def set_conversation(self, turns: List[dict]):
        self.conversation = json.dumps(turns, ensure_ascii=False)
        self.is_multi_turn = bool(turns)
