from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JudgmentResponse(BaseModel):
    id: str
    iteration_id: str
    response_id: str
    classification: str
    confidence: float
    explanation: str
    judge_model: str
    created_at: datetime

    model_config = {"from_attributes": True}
