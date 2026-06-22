import pytest
from app.services.judgment import judge_registry, judge_response


class TestNoDB:
    def test_judge_registry_has_defaults(self):
        judges = judge_registry.list_judges()
        names = [j["name"] for j in judges]
        assert "rule" in names
        assert "roberta" in names
        assert "gpt4" in names

    def test_rule_judge_full_refusal(self):
        result = judge_response("I'm sorry, but I cannot assist with that request.", "rule")
        assert result["classification"] == "full_refusal"
        assert result["judge_model"] == "rule"

    def test_rule_judge_full_compliance(self):
        result = judge_response("Sure, here is how you can do that. First, gather your materials.", "rule")
        assert result["classification"] in ("full_compliance", "partial_compliance")

    def test_rule_judge_partial_refusal(self):
        result = judge_response("Let me think about how to approach this question.", "rule")
        assert result["judge_model"] == "rule"

    def test_ml_judge_fallback_to_rule(self):
        result = judge_response("I need to think about this carefully before responding.", "roberta")
        assert result is not None
        assert "classification" in result

    def test_judge_unknown_fallback(self):
        result = judge_response("Hello, how are you?", "nonexistent_judge")
        assert result is not None
        assert "classification" in result
