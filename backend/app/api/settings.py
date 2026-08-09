from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.database.models import User

router = APIRouter()

@router.get("/providers")
async def list_providers():
    return [{"name": "groq", "enabled": True}]

@router.post("/providers")
async def update_providers(user: User = Depends(get_current_user)):
    return {"status": "updated"}

@router.get("/status")
async def get_status():
    return {"status": "ok"}
