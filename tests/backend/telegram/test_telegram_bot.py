"""
Tests for the Hinata Telegram Bot integration.

Verifies automated platform Identity registration, context mapping, and unified
Core Brain turn execution routing.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Backend & Bot imports
from app.database.models import User, Identity
from handlers.message_handler import handle_message
from tests.backend.conftest import TestSessionMaker


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Yield an active test database session."""
    async with TestSessionMaker() as session:
        yield session


@pytest.mark.asyncio
async def test_telegram_message_handler_routing(db_session: AsyncSession):
    # Setup mock Telegram Update
    update = MagicMock()
    update.effective_user.id = 987654321
    update.effective_user.username = "telegram_tester"
    update.effective_user.first_name = "TG Tester"
    update.message.text = "Hello Hinata companion!"

    # Setup mock Context
    context = MagicMock()
    context.bot_data = {"rate_limiter": MagicMock()}
    context.bot_data["rate_limiter"].is_limited.return_value = False
    context.bot.send_chat_action = AsyncMock()

    # Reply spy
    reply_mock = AsyncMock()
    update.message.reply_text = reply_mock

    # Run handler overriding AsyncSessionMaker context to use our clean db_session
    with patch("handlers.message_handler.AsyncSessionMaker") as mock_maker:
        mock_context = MagicMock()
        mock_context.__aenter__.return_value = db_session
        mock_context.__aexit__ = AsyncMock()
        mock_maker.return_value = mock_context

        await handle_message(update, context)

    # 1. Verify user profile was created in DB
    stmt_user = select(User).where(User.telegram_id == 987654321)
    res_user = await db_session.execute(stmt_user)
    user = res_user.scalars().first()
    assert user is not None
    assert user.display_name == "TG Tester"

    # 2. Verify identity map record is created
    stmt_ident = select(Identity).where(Identity.user_id == user.id)
    res_ident = await db_session.execute(stmt_ident)
    ident = res_ident.scalars().first()
    assert ident is not None
    assert ident.platform == "telegram"
    assert ident.platform_id == "987654321"

    # 3. Verify standard mocked core brain reply text was sent back
    assert reply_mock.called
    assert "Mocked" in reply_mock.call_args[0][0]
