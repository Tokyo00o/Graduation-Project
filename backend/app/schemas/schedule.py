from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ScheduleCreate(BaseModel):
    name: str
    strategy: str = "random"
    budget: int = 100
    judge: str = "roberta"
    target_model: str = ""
    seed_ids: List[str] = []
    cron_expression: str = "0 0 * * *"
    is_active: bool = True
    asr_threshold: Optional[float] = None
    slack_webhook_url: Optional[str] = None
    webhook_url: Optional[str] = None


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    strategy: Optional[str] = None
    budget: Optional[int] = None
    judge: Optional[str] = None
    target_model: Optional[str] = None
    seed_ids: Optional[List[str]] = None
    cron_expression: Optional[str] = None
    is_active: Optional[bool] = None
    asr_threshold: Optional[float] = None
    slack_webhook_url: Optional[str] = None
    webhook_url: Optional[str] = None


class ScheduleResponse(BaseModel):
    id: str
    project_id: str
    name: str
    strategy: str
    budget: int
    judge: str
    target_model: str
    seed_ids: str
    cron_expression: str
    is_active: bool
    asr_threshold: Optional[float] = None
    slack_webhook_url: Optional[str] = None
    webhook_url: Optional[str] = None
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    last_job_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
