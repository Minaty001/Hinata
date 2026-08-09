from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    chain_id: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    source: str = "web"

class ChatResponse(BaseModel):
    reply: str
    chain_id: str
    provider: str
    model: str
    timestamp: datetime

class MessageSchema(BaseModel):
    id: int
    role: str
    message: str
    timestamp: datetime

class ChainSchema(BaseModel):
    chain_id: str
    title: str
    created_at: datetime
    updated_at: datetime

class HistoryResponse(BaseModel):
    chain_id: str
    messages: List[MessageSchema]
