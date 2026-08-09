from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class UserSchema(BaseModel):
    id: int
    username: Optional[str]
    display_name: Optional[str]
    language: str
    timezone: str
    current_personality: str
    current_mood: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    personality: Optional[str] = None
