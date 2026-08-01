"""
Unit test suite for AchievementManager in Pi Arcade OS.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
from src.save_manager import SaveManager
from src.notification_manager import NotificationManager
from src.achievement_manager import AchievementManager


class TestAchievementManager(unittest.TestCase):
    """Unit tests for achievement unlock logic, triggers, and JSON persistence."""

    def setUp(self):
        self.save_manager = SaveManager(filepath="test_ach_save.json", backup_path="test_ach_save.json.bak")
        self.save_manager.reset_all()
        self.notif_manager = NotificationManager()
        self.ach_manager = AchievementManager(
            save_manager=self.save_manager,
            notification_manager=self.notif_manager,
        )

    def tearDown(self):
        for path in ["test_ach_save.json", "test_ach_save.json.bak"]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def test_first_launch_unlocked_on_startup(self):
        self.assertTrue(self.ach_manager.is_unlocked("first_launch"))
        self.assertIn("first_launch", self.save_manager.achievements)

    def test_first_snake_game_unlock(self):
        self.ach_manager.check_achievements("game_start", {"game_id": "snake"})
        self.assertTrue(self.ach_manager.is_unlocked("first_snake"))

    def test_score_100_in_snake_unlock(self):
        self.save_manager.record_game_session("snake", 100, 45.0)
        self.ach_manager.check_achievements("game_end")
        self.assertTrue(self.ach_manager.is_unlocked("score_100_snake"))

    def test_first_pong_win_unlock(self):
        self.save_manager.record_pong_session(5, 2, 60.0, 10)
        self.ach_manager.check_achievements("game_end")
        self.assertTrue(self.ach_manager.is_unlocked("first_pong_win"))

    def test_first_tetris_line_unlock(self):
        self.save_manager.record_tetris_session(300, 2, 1, 0, 40.0)
        self.ach_manager.check_achievements("game_end")
        self.assertTrue(self.ach_manager.is_unlocked("first_tetris_line"))

    def test_play_10_games_unlock(self):
        for i in range(10):
            self.save_manager.record_game_start("snake")
        self.ach_manager.check_achievements("game_end")
        self.assertTrue(self.ach_manager.is_unlocked("play_10_games"))

    def test_duplicate_unlock_returns_false(self):
        res1 = self.ach_manager.unlock("first_snake")
        res2 = self.ach_manager.unlock("first_snake")
        self.assertTrue(res1)
        self.assertFalse(res2)

    def test_get_all_achievements_list(self):
        all_achs = self.ach_manager.get_all_achievements()
        self.assertGreaterEqual(len(all_achs), 8)
        ids = [a["id"] for a in all_achs]
        self.assertIn("arcade_veteran", ids)


if __name__ == "__main__":
    unittest.main()
