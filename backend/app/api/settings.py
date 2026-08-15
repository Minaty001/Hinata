from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.user import get_current_user
from app.database.engine import get_session
from app.database.models import User, Setting
from app.core.brain import brain

router = APIRouter()


class ProviderUpdate(BaseModel):
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    base_url: str | None = None


def _serialize_providers() -> dict:
    """Return providers info in the shape the web UI expects."""
    info = brain.unified_client.get_all_providers_info()
    return {
        "active_provider": brain.unified_client.get_active_provider(),
        "providers": info,
    }


@router.get("/providers")
async def list_providers(user: User = Depends(get_current_user)):
    return _serialize_providers()


@router.post("/providers")
async def update_providers(
    req: ProviderUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    client = brain.unified_client
    try:
        if req.provider:
            client.set_active_provider(req.provider, req.model)
        target = req.provider or client.get_active_provider()
        if req.api_key is not None or req.base_url is not None or req.model is not None:
            client.set_provider_config(
                target,
                api_key=req.api_key,
                base_url=req.base_url,
                model=req.model,
            )
    except Exception as exc:  # noqa: BLE001 - surface provider config errors to UI
        raise HTTPException(status_code=400, detail=str(exc))

    # Persist across restarts so the config survives a server reboot.
    try:
        await _persist_settings(session, client)
    except Exception:  # noqa: BLE001 - persistence is best-effort
        pass

    return _serialize_providers()


async def _persist_settings(session: AsyncSession, client) -> None:
    """Store active provider + per-provider config as Setting rows."""
    rows = {
        "active_provider": client.get_active_provider(),
    }
    for key, cfg in client.providers.items():
        if cfg.get("api_key"):
            rows[f"provider_{key}_key"] = cfg["api_key"]
        if cfg.get("base_url"):
            rows[f"provider_{key}_url"] = cfg["base_url"]
        if cfg.get("active_model"):
            rows[f"provider_{key}_model"] = cfg["active_model"]

    for k, v in rows.items():
        res = await session.execute(select(Setting).where(Setting.key == k))
        setting = res.scalars().first()
        if setting:
            setting.value = v
        else:
            session.add(Setting(key=k, value=v))
    await session.commit()


@router.get("/status")
async def get_status():
    return {"status": "ok"}
