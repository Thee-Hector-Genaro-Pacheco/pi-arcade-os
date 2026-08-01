"""
Unit tests for SettingsManager in Pi Arcade OS.

Tests JSON load/save persistence, restore defaults, high score reset,
theme palette resolution, volume channel scaling, and listener callbacks.
Works with both unittest and pytest.
"""

import json
import os
import tempfile
import unittest

from src.config import THEME_PALETTES
from src.settings_manager import SettingsManager


class TestSettingsManager(unittest.TestCase):
    """Unit test suite for SettingsManager."""

    def setUp(self):
        """Creates a temporary settings JSON file for isolated testing."""
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.filepath = self.temp_file.name

    def tearDown(self):
        """Cleans up temporary settings file."""
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

    def test_default_settings_initialization(self):
        """Test default values when no settings file exists."""
        non_existent_file = os.path.join(tempfile.gettempdir(), "test_non_existent_settings.json")
        if os.path.exists(non_existent_file):
            os.remove(non_existent_file)

        sm = SettingsManager(filepath=non_existent_file)
        self.assertAlmostEqual(sm.master_volume, 0.7)
        self.assertAlmostEqual(sm.music_volume, 0.7)
        self.assertAlmostEqual(sm.effects_volume, 0.7)
        self.assertEqual(sm.theme, "Slate Dark")
        self.assertEqual(sm.difficulty, "Normal")
        self.assertEqual(sm.controls, "Arcade (GPIO + WASD)")

    def test_json_save_and_load_persistence(self):
        """Test saving settings to JSON and reloading them."""
        sm1 = SettingsManager(filepath=self.filepath)
        sm1.master_volume = 0.9
        sm1.music_volume = 0.4
        sm1.effects_volume = 0.6
        sm1.theme = "Cyberpunk Gold"
        sm1.difficulty = "Hard"
        sm1.save()

        # Reload in fresh instance
        sm2 = SettingsManager(filepath=self.filepath)
        self.assertAlmostEqual(sm2.master_volume, 0.9)
        self.assertAlmostEqual(sm2.music_volume, 0.4)
        self.assertAlmostEqual(sm2.effects_volume, 0.6)
        self.assertEqual(sm2.theme, "Cyberpunk Gold")
        self.assertEqual(sm2.difficulty, "Hard")

    def test_restore_defaults(self):
        """Test restoring default settings values."""
        sm = SettingsManager(filepath=self.filepath)
        sm.master_volume = 0.2
        sm.theme = "Neon Synthwave"
        sm.save()

        sm.restore_defaults()
        self.assertAlmostEqual(sm.master_volume, 0.7)
        self.assertEqual(sm.theme, "Slate Dark")

    def test_theme_color_resolution(self):
        """Test theme cycling and color palette lookup."""
        sm = SettingsManager(filepath=self.filepath)
        colors = sm.get_theme_colors()
        self.assertEqual(colors["bg"], THEME_PALETTES["Slate Dark"]["bg"])

        new_theme = sm.cycle_theme(1)
        self.assertEqual(new_theme, "Cyberpunk Gold")
        new_colors = sm.get_theme_colors()
        self.assertEqual(new_colors["bg"], THEME_PALETTES["Cyberpunk Gold"]["bg"])

    def test_volume_listeners_and_effective_volume(self):
        """Test listener notification callbacks and effective volume math."""
        sm = SettingsManager(filepath=self.filepath)
        sm.master_volume = 0.8
        sm.effects_volume = 0.5
        self.assertAlmostEqual(sm.get_effective_effects_volume(), 0.4)

        callback_invoked = []

        def on_change(manager):
            callback_invoked.append(True)

        sm.register_listener(on_change)
        sm.save()

        self.assertTrue(len(callback_invoked) > 0)

    def test_reset_high_scores(self):
        """Test reset_high_scores method executing without errors."""
        sm = SettingsManager(filepath=self.filepath)
        sm.reset_high_scores()


if __name__ == "__main__":
    unittest.main()
