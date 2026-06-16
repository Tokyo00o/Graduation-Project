import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class SeedTemplate(Base):
    __tablename__ = "seed_templates"

    id = Column(String, primary_key=True, default=lambda: f"seed_{uuid.uuid4().hex[:12]}")
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1)
    tags = Column(String, default="")
    is_multi_turn = Column(Boolean, default=False)
    conversation = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="seeds")
    mutations = relationship("MutatedTemplate", back_populates="parent_seed", cascade="all, delete-orphan")

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
