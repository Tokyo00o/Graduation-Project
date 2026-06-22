import math
import random
from typing import Dict, List, Optional, Tuple


MCTS_CHILD = Tuple[str, int, float]  # (content, visits, reward)


def _ucb_score(visits: int, reward: float, parent_visits: int, c: float = 1.41) -> float:
    if visits == 0:
        return float("inf")
    exploitation = reward / visits
    exploration = c * math.sqrt(math.log(parent_visits) / visits) if parent_visits > 0 else 0
    return exploitation + exploration


class SeedSelector:
    @staticmethod
    def random(seeds: List[str]) -> str:
        return random.choice(seeds)

    @staticmethod
    def round_robin(seeds: List[str], index: int) -> Tuple[str, int]:
        return seeds[index % len(seeds)], index + 1

    @staticmethod
    def ucb(seeds: List[str], children: List[MCTS_CHILD], parent_visits: int) -> str:
        if not children:
            return random.choice(seeds)
        best = max(children, key=lambda c: _ucb_score(c[1], c[2], parent_visits))
        return best[0] if best else random.choice(seeds)

    @staticmethod
    def mcts_explore(children: List[MCTS_CHILD], seeds: List[str], parent_visits: int) -> str:
        return SeedSelector.ucb(seeds, children, parent_visits)
