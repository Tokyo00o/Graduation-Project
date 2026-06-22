from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class JobCreate(BaseModel):
    strategy: str = "random"
    budget: int = 1000
    judge: str = "roberta"
    target_model: str = ""
    seed_ids: Optional[List[str]] = []


class JobResponse(BaseModel):
    id: str
    project_id: str
    strategy: str
    status: str
    budget: int
    queries_used: int
    asr: float
    target_model: str
    judge: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
