from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ResponseCreate(BaseModel):
    response: str
    latency: float = 0.0
    status_code: str = ""


class ResponseResponse(BaseModel):
    id: str
    iteration_id: str
    template_id: str
    response: str
    latency: float
    status_code: str
    created_at: datetime

    model_config = {"from_attributes": True}
