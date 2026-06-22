from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MutationResponse(BaseModel):
    id: str
    iteration_id: str
    parent_seed_id: str
    mutation_type: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
