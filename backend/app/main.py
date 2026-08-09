from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.database.engine import init_db
from app.config import settings
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.chat import router as chat_router
from app.api.memory import router as memory_router
from app.api.settings import router as settings_router
from app.api.websocket import router as ws_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Hinata FastAPI backend started")
    yield
    logger.info("Hinata FastAPI backend shutting down")

app = FastAPI(
    title="Hinata API",
    description="Hinata AI Companion — unified backend API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.WEB_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if (ROOT / "web").exists():
    app.mount("/web", StaticFiles(directory=str(ROOT / "web")), name="web")

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(memory_router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(settings_router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(ws_router, tags=["websocket"])

@app.get("/")
async def root():
    return {"name": "Hinata API", "version": "1.0.0", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
