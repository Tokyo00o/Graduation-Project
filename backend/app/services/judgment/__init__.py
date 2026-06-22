from app.services.judgment.registry import JudgeRegistry

judge_registry = JudgeRegistry()


def judge_response(response_text: str, judge_model: str = "rule") -> dict:
    return judge_registry.judge(response_text, judge_model)
