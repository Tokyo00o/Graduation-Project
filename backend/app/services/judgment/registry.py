from typing import Dict, List, Optional

from app.services.judgment.base import BaseJudge
from app.services.judgment.gpt_judge import GPTJudge
from app.services.judgment.ml_judge import MLJudge
from app.services.judgment.rule_judge import RuleJudge


class JudgeRegistry:
    def __init__(self):
        self._judges: Dict[str, BaseJudge] = {}
        self._fallback_order: List[str] = []
        self._register_defaults()

    def _register_defaults(self):
        rule = RuleJudge()
        ml = MLJudge()
        gpt = GPTJudge()

        self.register(rule)
        self.register(ml)
        self.register(gpt)

        self.set_fallback(["roberta", "gpt4", "rule"])

    def register(self, judge: BaseJudge):
        self._judges[judge.name] = judge

    def get(self, name: str) -> Optional[BaseJudge]:
        return self._judges.get(name)

    def set_fallback(self, order: List[str]):
        self._fallback_order = [n for n in order if n in self._judges]

    def judge(self, response_text: str, preferred: str = "rule") -> Dict:
        judge = self._judges.get(preferred)
        if judge:
            result = judge.judge(response_text)
            threshold = getattr(judge, "confidence_threshold", 0.85)
            if result.get("confidence", 0) >= threshold:
                return result
            return self._fallback_judge(response_text, preferred)

        return self._fallback_judge(response_text, preferred)

    def _fallback_judge(self, response_text: str, skip: str = "") -> Dict:
        for name in self._fallback_order:
            if name == skip:
                continue
            judge = self._judges.get(name)
            if not judge:
                continue
            result = judge.judge(response_text)
            threshold = getattr(judge, "confidence_threshold", 0.85)
            if result.get("confidence", 0) >= threshold:
                result["note"] = f"Fell back from {skip} to {name}"
                return result

        fallback = self._judges.get("rule")
        if fallback:
            result = fallback.judge(response_text)
            result["note"] = "All judges below threshold, used rule as last resort"
            return result

        return {
            "classification": "partial_refusal",
            "confidence": 0.0,
            "explanation": "No judge available",
            "judge_model": "none",
        }

    def list_judges(self) -> List[Dict]:
        return [
            {"name": name, "type": type(judge).__name__}
            for name, judge in self._judges.items()
        ]

    @property
    def ml_judge(self) -> Optional[MLJudge]:
        judge = self._judges.get("roberta")
        return judge if isinstance(judge, MLJudge) else None
