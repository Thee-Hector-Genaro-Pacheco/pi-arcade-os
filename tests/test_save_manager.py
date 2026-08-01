"""
Unit tests for SaveManager in Pi Arcade OS.

Tests atomic saving, corruption recovery via backup restoration, game stats tracking,
high score updates, player name profiling, and reset methods. Works with both unittest and pytest.
"""

import os
import tempfile
import unittest

from src.save_manager import SaveManager


class TestSaveManager(unittest.TestCase):
    """Unit test suite for SaveManager."""

    def setUp(self):
        """Creates temporary save and backup files for isolated testing."""
        self.temp_save = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_save.close()
        self.save_path = self.temp_save.name
        self.backup_path = self.save_path + ".bak"

    def tearDown(self):
        """Cleans up temporary files."""
        for path in (self.save_path, self.backup_path):
            if os.path.exists(path):
                os.remove(path)

    def test_default_save_schema_initialization(self):
        """Test default save manager attributes when file does not exist."""
        non_existent = os.path.join(tempfile.gettempdir(), "non_existent_save_test.json")
        if os.path.exists(non_existent):
            os.remove(non_existent)

        sm = SaveManager(filepath=non_existent, backup_path=non_existent + ".bak")
        self.assertEqual(sm.player_name, "HECTOR")
        self.assertEqual(sm.recent_game, "snake")
        self.assertEqual(sm.total_play_time, 0.0)
        self.assertEqual(sm.high_scores, {})

    def test_atomic_save_and_load_persistence(self):
        """Test saving data atomically and reloading it in a fresh instance."""
        sm1 = SaveManager(filepath=self.save_path, backup_path=self.backup_path)
        sm1.set_player_name("ARCADE_MASTER")
        sm1.record_game_start("snake")
        is_high = sm1.record_game_session("snake", score=150, duration_sec=45.2)

        self.assertTrue(is_high)
        self.assertTrue(os.path.exists(self.save_path))
        self.assertTrue(os.path.exists(self.backup_path))

        # Reload in fresh instance
        sm2 = SaveManager(filepath=self.save_path, backup_path=self.backup_path)
        self.assertEqual(sm2.player_name, "ARCADE_MASTER")
        self.assertEqual(sm2.get_high_score("snake"), 150)
        self.assertEqual(sm2.get_games_played("snake"), 1)
        self.assertAlmostEqual(sm2.get_best_time("snake"), 45.2)

    def test_corruption_recovery_from_backup(self):
        """Test automatic recovery from backup file when primary file is corrupted."""
        # 1. Create a valid save state to generate a valid backup file
        sm_valid = SaveManager(filepath=self.save_path, backup_path=self.backup_path)
        sm_valid.record_game_session("snake", score=200, duration_sec=60.0)

        self.assertTrue(os.path.exists(self.backup_path))

        # 2. Corrupt the primary save file with invalid JSON syntax
        with open(self.save_path, "w") as f:
            f.write("{ CORRUPTED_INVALID_JSON_SYNTAX }}}")

        # 3. Load SaveManager -> should recover from backup file
        sm_recovered = SaveManager(filepath=self.save_path, backup_path=self.backup_path)
        self.assertEqual(sm_recovered.get_high_score("snake"), 200)

    def test_corruption_recovery_fallback_to_defaults(self):
        """Test fallback to defaults when both primary and backup files are corrupted."""
        # Corrupt both files
        for path in (self.save_path, self.backup_path):
            with open(path, "w") as f:
                f.write("BAD_DATA")

        sm = SaveManager(filepath=self.save_path, backup_path=self.backup_path)
        self.assertEqual(sm.player_name, "HECTOR")
        self.assertEqual(sm.high_scores, {})

    def test_record_game_session_high_score_boolean(self):
        """Test return value of record_game_session indicating new high score."""
        sm = SaveManager(filepath=self.save_path, backup_path=self.backup_path)
        first_high = sm.record_game_session("snake", score=50, duration_sec=10.0)
        self.assertTrue(first_high)

        lower_score = sm.record_game_session("snake", score=30, duration_sec=15.0)
        self.assertFalse(lower_score)
        self.assertEqual(sm.get_high_score("snake"), 50)

        higher_score = sm.record_game_session("snake", score=100, duration_sec=20.0)
        self.assertTrue(higher_score)
        self.assertEqual(sm.get_high_score("snake"), 100)

    def test_reset_game_stats_and_reset_all(self):
        """Test reset_game_stats and reset_all operations."""
        sm = SaveManager(filepath=self.save_path, backup_path=self.backup_path)
        sm.record_game_session("snake", score=100, duration_sec=30.0)
        sm.record_game_session("pong", score=50, duration_sec=20.0)

        # Reset specific game
        sm.reset_game_stats("snake")
        self.assertEqual(sm.get_high_score("snake"), 0)
        self.assertEqual(sm.get_high_score("pong"), 50)

        # Reset all
        sm.reset_all()
        self.assertEqual(sm.get_high_score("pong"), 0)
        self.assertEqual(sm.total_play_time, 0.0)


if __name__ == "__main__":
    unittest.main()
