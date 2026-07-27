"""
Test suite for Hinata Stored Data & Chain Conversations (Greenlet-Free)
"""

import asyncio
import unittest
from database.database import Base, init_database, async_session_factory
from database.models import User, Conversation, Chain, Memory
from services.user_service import get_or_create_web_user
from services.chat_service import (
    save_message,
    get_conversation_history,
    get_user_chains,
    get_or_create_chain,
    delete_chain,
)
from memory.memory_manager import save_memory, get_memories_list, get_memories_summary


class TestStorageAndChains(unittest.TestCase):
    """Integration test suite for database storage and chain conversations."""

    def test_database_persistence_and_chains(self):
        async def _test():
            await init_database()

            async with async_session_factory() as session:
                # 1. Create Web User
                user = await get_or_create_web_user(session)
                self.assertIsNotNone(user.id)
                self.assertEqual(user.username, "web_user")

                # 2. Get/Create Chain
                chain1 = await get_or_create_chain(session, user.id, title="Topic 1: Anime")
                self.assertIsNotNone(chain1.chain_id)

                chain2 = await get_or_create_chain(session, user.id, title="Topic 2: Coding")
                self.assertIsNotNone(chain2.chain_id)

                # 3. List chains
                chains = await get_user_chains(session, user.id)
                self.assertGreaterEqual(len(chains), 2)

                # 4. Save messages to specific chains
                await save_message(session, user.id, "user", "Who is Hinata Hyuga?", chain_id=chain1.chain_id)
                await save_message(session, user.id, "assistant", "She is a sweet ninja girl! 🌸", chain_id=chain1.chain_id)

                await save_message(session, user.id, "user", "How do I use Python async?", chain_id=chain2.chain_id)

                # 5. Fetch history per chain
                history1 = await get_conversation_history(session, user.id, chain_id=chain1.chain_id)
                self.assertGreaterEqual(len(history1), 2)

                history2 = await get_conversation_history(session, user.id, chain_id=chain2.chain_id)
                self.assertGreaterEqual(len(history2), 1)

                # 6. Save & Fetch Memories
                mem1 = await save_memory(session, user.id, "fact", "User loves Python coding.", importance=5)
                self.assertIsNotNone(mem1.id)

                memories_list = await get_memories_list(session, user.id)
                self.assertGreaterEqual(len(memories_list), 1)

                mem_summary = await get_memories_summary(session, user.id)
                self.assertIn("User loves Python coding", mem_summary)

                # 7. Delete Chain
                del_success = await delete_chain(session, user.id, chain1.chain_id)
                self.assertTrue(del_success)

                history1_after = await get_conversation_history(session, user.id, chain_id=chain1.chain_id)
                self.assertEqual(len(history1_after), 0)

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
