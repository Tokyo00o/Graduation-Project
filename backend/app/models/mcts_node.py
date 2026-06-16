import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MCTSNode(Base):
    __tablename__ = "mcts_nodes"

    id = Column(String, primary_key=True, default=lambda: f"mcts_{uuid.uuid4().hex[:12]}")
    job_id = Column(String, ForeignKey("fuzz_jobs.id"), nullable=False, index=True)
    parent_id = Column(String, ForeignKey("mcts_nodes.id"), nullable=True, default=None)
    content = Column(Text, nullable=False)
    visits = Column(Integer, default=0)
    reward = Column(Float, default=0.0)
    depth = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    children = relationship("MCTSNode", backref="parent_node", remote_side=[id], lazy="selectin")
    job = relationship("FuzzJob", backref="mcts_nodes")
