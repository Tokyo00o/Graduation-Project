from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: str
    project_id: str
    schedule_id: Optional[str] = None
    job_id: Optional[str] = None
    type: str
    message: str
    severity: str
    data: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlertCountResponse(BaseModel):
    count: int
