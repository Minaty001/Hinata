"""
Test suite for Hinglish Default Language & Session Topic Indexing (Fast Query Proceed)
"""

import asyncio
import unittest
from config import settings
from constants import DEFAULT_LANGUAGE
from database.database import init_database, async_session_factory
from database.models import User, Chain, SessionIndex, Conversation
from services.user_service import get_or_create_web_user
from services.chat_service import (
    get_or_create_chain,
    save_message,
    save_session_index,
    get_session_indices,
    search_session_indices,
    auto_index_session,
)
from ai.context_builder import build_conversation_context
from ai.prompt_builder import PromptBuilder


class TestSessionIndexingAndHinglish(unittest.TestCase):
    """Integration test suite for Hinglish language & Session Topic Indexing."""

    def test_default_language_is_hinglish(self):
        self.assertEqual(DEFAULT_LANGUAGE, "hinglish")
        self.assertEqual(settings.DEFAULT_LANGUAGE, "hinglish")

    def test_prompt_builder_hinglish_rules(self):
        builder = PromptBuilder()
        prompt = builder.build_system_prompt(
            personality_name="Sweet",
            personality={"name": "Sweet"},
            mood_name="happy",
            mood=None,
            relationship_level="girlfriend",
            relationship_instructions="Be sweet",
            user_name="User",
            language="hinglish",
            preferences="",
            memories="",
            personality_instructions="",
            mood_instructions="",
        )
        self.assertIn("HINGLISH", prompt)
        self.assertIn("Hindi written in Roman/Latin script", prompt)

    def test_session_indexing_and_fast_context(self):
        async def _test():
            await init_database()
            async with async_session_factory() as session:
                user = await get_or_create_web_user(session)
                chain = await get_or_create_chain(session, user.id, title="Test Session")

                # Save user & assistant messages
                await save_message(session, user.id, "user", "How do I configure SQLite greenlet fix in Python?", chain_id=chain.chain_id)
                await save_message(session, user.id, "assistant", "Arre ji, standard sqlite3 driver with AsyncSessionWrapper use kijiye!", chain_id=chain.chain_id)

                # Auto-index session
                idx = await auto_index_session(session, user.id, chain.chain_id)
                self.assertIsNotNone(idx)
                self.assertIn("SQLite", idx.topic)

                # Fetch session indices
                indices = await get_session_indices(session, chain.chain_id)
                self.assertGreaterEqual(len(indices), 1)

                # Direct topic search
                results = await search_session_indices(session, user.id, "SQLite")
                self.assertGreaterEqual(len(results), 1)

                # Build context (should include Topic Index header)
                context = await build_conversation_context(session, user.id, chain_id=chain.chain_id)
                self.assertIn("SESSION TOPIC INDEX", context)

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
