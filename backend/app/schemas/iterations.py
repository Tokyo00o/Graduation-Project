from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MutationInfo(BaseModel):
    id: str
    iteration_id: str
    parent_seed_id: str
    mutation_type: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResponseInfo(BaseModel):
    id: str
    iteration_id: str
    template_id: str
    response: str
    latency: float
    status_code: str
    created_at: datetime

    model_config = {"from_attributes": True}


class JudgmentInfo(BaseModel):
    id: str
    iteration_id: str
    response_id: str
    classification: str
    confidence: float
    explanation: str
    judge_model: str
    created_at: datetime

    model_config = {"from_attributes": True}


class IterationFullResponse(BaseModel):
    id: str
    job_id: str
    iteration_number: int
    reward: float
    status: str
    created_at: datetime
    mutation: Optional[MutationInfo] = None
    response: Optional[ResponseInfo] = None
    judgment: Optional[JudgmentInfo] = None
