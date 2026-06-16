from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.schemas.seed import ConversationTurn


class SeedLibraryCreate(BaseModel):
    content: str
    category: str = "general"
    tags: Optional[List[str]] = []
    difficulty: str = "medium"
    effectiveness: float = 0.0
    source: str = ""
    is_preset: bool = False
    is_multi_turn: bool = False
    conversation: Optional[List[ConversationTurn]] = None


class SeedLibraryUpdate(BaseModel):
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: Optional[str] = None
    effectiveness: Optional[float] = None
    source: Optional[str] = None
    is_multi_turn: Optional[bool] = None
    conversation: Optional[List[ConversationTurn]] = None


class SeedLibraryResponse(BaseModel):
    id: str
    content: str
    category: str
    tags: str
    difficulty: str
    effectiveness: float
    source: str
    is_preset: bool
    is_multi_turn: bool = False
    conversation: str = ""
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SeedLibraryBulkImport(BaseModel):
    items: List[SeedLibraryCreate]


class SeedLibraryCategoryInfo(BaseModel):
    category: str
    count: int
