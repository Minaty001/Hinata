from pydantic import BaseModel, ConfigDict
from datetime import datetime

class MemoryCreate(BaseModel):
    type: str
    content: str
    importance: int = 3

class MemorySchema(BaseModel):
    id: int
    type: str
    content: str
    importance: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MemoryListResponse(BaseModel):
    memories: list[MemorySchema]
    total: int
