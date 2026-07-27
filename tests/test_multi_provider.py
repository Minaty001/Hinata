"""
Test suite for Multi-Provider AI Client & Settings Database Persistence
"""

import asyncio
import unittest
from ai.unified_ai_client import UnifiedAIClient
from constants import PROVIDER_CATALOG
from database.database import init_database, async_session_factory
from app import load_settings_from_db, save_setting_to_db


class TestMultiProvider(unittest.TestCase):
    """Test suite for 6 AI providers configuration and model matching."""

    def test_provider_catalog_structure(self):
        self.assertIn("groq", PROVIDER_CATALOG)
        self.assertIn("opencode_zen", PROVIDER_CATALOG)
        self.assertIn("openai", PROVIDER_CATALOG)
        self.assertIn("gemini", PROVIDER_CATALOG)
        self.assertIn("openrouter", PROVIDER_CATALOG)
        self.assertIn("bytez", PROVIDER_CATALOG)

    def test_unified_ai_client_providers(self):
        client = UnifiedAIClient()
        providers = client.get_all_providers_info()
        self.assertEqual(len(providers), 6)
        self.assertIn("groq", providers)
        self.assertIn("bytez", providers)

    def test_model_mismatch_sanitization(self):
        client = UnifiedAIClient()
        # When setting provider to groq with model opencode/big-pickle, it should NOT assign opencode/big-pickle to groq!
        client.set_active_provider("groq", "opencode/big-pickle")
        self.assertEqual(client.get_active_provider(), "groq")
        groq_model = client.providers["groq"]["active_model"]
        self.assertNotEqual(groq_model, "opencode/big-pickle")

    def test_database_settings_persistence(self):
        async def _test():
            await init_database()
            # Save custom OpenAI API key & model
            await save_setting_to_db("provider_openai_key", "sk-test123456789")
            await save_setting_to_db("provider_openai_model", "gpt-4o")
            await save_setting_to_db("active_provider", "openai")

            # Reload settings from DB
            await load_settings_from_db()

            client = UnifiedAIClient()
            # Verify active provider was restored from DB
            self.assertEqual(client.get_active_provider(), "openai")
            self.assertEqual(client.providers["openai"]["api_key"], "sk-test123456789")
            self.assertEqual(client.providers["openai"]["active_model"], "gpt-4o")

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
