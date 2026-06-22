from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IterationResponse(BaseModel):
    id: str
    job_id: str
    iteration_number: int
    reward: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
