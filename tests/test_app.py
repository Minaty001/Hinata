"""
Unit Tests for Hinata Hyuga Web Application & Backend Modules
"""

import unittest
from utils.validators import sanitise_input, is_owner
from config import settings


class TestUtilsAndValidators(unittest.TestCase):
    """Test suite for input validators and config."""

    def test_sanitise_input(self):
        raw = "  Hello \x00 World \n\n\n\n\n Test  "
        sanitised = sanitise_input(raw)
        self.assertNotIn("\x00", sanitised)
        self.assertNotIn("\n\n\n\n", sanitised)
        self.assertTrue(sanitised.startswith("Hello"))

    def test_is_owner(self):
        self.assertTrue(is_owner(12345, 12345))
        self.assertFalse(is_owner(12345, 67890))

    def test_config_settings(self):
        self.assertIsNotNone(settings.WEB_PORT)
        self.assertIsNotNone(settings.WEB_HOST)


if __name__ == "__main__":
    unittest.main()
