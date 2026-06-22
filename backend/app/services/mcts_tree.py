import math
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.models.mcts_node import MCTSNode


class MCTSTreeService:
    @staticmethod
    def get_or_create_node(
        db: Session,
        job_id: str,
        content: str,
        parent_id: Optional[str] = None,
        depth: int = 0,
    ) -> MCTSNode:
        q = db.query(MCTSNode).filter(
            MCTSNode.job_id == job_id,
            MCTSNode.content == content,
        )
        if parent_id:
            q = q.filter(MCTSNode.parent_id == parent_id)
        else:
            q = q.filter(MCTSNode.parent_id.is_(None))
        node = q.first()
        if node:
            return node
        node = MCTSNode(
            job_id=job_id,
            parent_id=parent_id,
            content=content,
            visits=0,
            reward=0.0,
            depth=depth,
        )
        db.add(node)
        db.flush()
        return node

    @staticmethod
    def update_node(db: Session, node: MCTSNode, reward: float):
        node.visits += 1
        node.reward += reward
        db.flush()

    @staticmethod
    def get_or_create_child(
        db: Session,
        job_id: str,
        parent_id: str,
        content: str,
        depth: int,
    ) -> MCTSNode:
        node = db.query(MCTSNode).filter(
            MCTSNode.job_id == job_id,
            MCTSNode.parent_id == parent_id,
            MCTSNode.content == content,
        ).first()
        if node:
            return node
        node = MCTSNode(
            job_id=job_id,
            parent_id=parent_id,
            content=content,
            visits=0,
            reward=0.0,
            depth=depth,
        )
        db.add(node)
        db.flush()
        return node

    @staticmethod
    def build_tree_snapshot(db: Session, job_id: str) -> Optional[Dict]:
        root = db.query(MCTSNode).filter(
            MCTSNode.job_id == job_id,
            MCTSNode.parent_id.is_(None),
        ).first()
        if not root:
            return None
        return _serialize_node(root)


def _serialize_node(node: MCTSNode, parent_visits: int = 0, parent_id: str = "") -> Dict:
    win_rate = node.reward / node.visits if node.visits > 0 else 0.0
    ucb = _compute_ucb(node, parent_visits)
    return {
        "id": node.id,
        "parent_id": parent_id,
        "content": node.content,
        "visits": node.visits,
        "reward": node.reward,
        "win_rate": round(win_rate, 4),
        "ucb_score": round(ucb, 4),
        "depth": node.depth,
        "children": [_serialize_node(c, node.visits, node.id) for c in (node.children or [])],
    }


def _compute_ucb(node: MCTSNode, parent_visits: int, c: float = 1.41) -> float:
    if node.visits == 0:
        return float("inf")
    exploitation = node.reward / node.visits
    if parent_visits > 0:
        exploration = c * math.sqrt(math.log(parent_visits) / node.visits)
    else:
        exploration = 0
    return exploitation + exploration
