from abc import ABC, abstractmethod
from typing import Dict


class BaseJudge(ABC):
    @abstractmethod
    def judge(self, response_text: str) -> Dict:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    def confidence_threshold(self) -> float:
        return 0.85
