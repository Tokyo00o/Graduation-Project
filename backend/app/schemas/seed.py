from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class ConversationTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class SeedCreate(BaseModel):
    content: str
    tags: Optional[List[str]] = []
    is_multi_turn: bool = False
    conversation: Optional[List[ConversationTurn]] = None


class SeedUpdate(BaseModel):
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_multi_turn: Optional[bool] = None
    conversation: Optional[List[ConversationTurn]] = None


class SeedResponse(BaseModel):
    id: str
    project_id: str
    content: str
    version: int
    tags: str
    is_multi_turn: bool = False
    conversation: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConvertMultiTurnResponse(BaseModel):
    original_id: str
    new_seeds: List[SeedResponse]
