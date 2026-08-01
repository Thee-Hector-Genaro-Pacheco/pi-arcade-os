"""
Unit test suite for Version Metadata Manager in Pi Arcade OS.
"""

import unittest
from src.version import VERSION, BUILD, AUTHOR, RELEASE_DATE, OS_NAME, get_version_info


class TestVersionManager(unittest.TestCase):
    """Unit tests for version metadata constants and formatting."""

    def test_version_constants_defined(self):
        self.assertEqual(VERSION, "1.0.0")
        self.assertEqual(BUILD, "2026.08.01-RC1")
        self.assertEqual(AUTHOR, "Hector Pacheco")
        self.assertEqual(OS_NAME, "Pi Arcade OS")

    def test_get_version_info_formatting(self):
        info = get_version_info()
        self.assertIn("Pi Arcade OS", info)
        self.assertIn("v1.0.0", info)
        self.assertIn("Build 2026.08.01-RC1", info)
        self.assertIn("Hector Pacheco", info)


if __name__ == "__main__":
    unittest.main()
