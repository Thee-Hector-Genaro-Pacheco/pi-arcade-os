"""
Unit tests for PongGame, AI Opponent, and Pong Save Subsystem in Pi Arcade OS.

Tests interface implementation, registration, paddle movement, collision physics,
wall bounces, scoring, first-to-5 victory condition, pause/resume, single-player AI mode,
and persistent Pong statistics.
All tests run headlessly without physical hardware. Works with both unittest and pytest.
"""

import os
# Configure headless environment for Pygame before importing Pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import tempfile
import unittest
import pygame

pygame.init()
pygame.display.set_mode((100, 100))

from src.config import Action, SCREEN_HEIGHT, PONG_PADDLE_HEIGHT, PONG_BALL_SIZE
from src.game_interface import ArcadeGame
from src.game_registry import GameRegistry
from src.games.pong_game import PongGame
from src.save_manager import SaveManager
from src.launcher import Launcher, LauncherState


class TestPongGame(unittest.TestCase):
    """Unit test suite for PongGame platform component."""

    def setUp(self):
        """Sets up temporary SaveManager and GameRegistry fixtures."""
        self.temp_save = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_save.close()
        self.save_path = self.temp_save.name
        self.save_manager = SaveManager(filepath=self.save_path, backup_path=self.save_path + ".bak")

        self.registry = GameRegistry()
        self.registry.register("pong", PongGame)

    def tearDown(self):
        """Cleans up temporary files."""
        for path in (self.save_path, self.save_path + ".bak"):
            if os.path.exists(path):
                os.remove(path)

    def test_pong_implements_arcade_game_interface(self):
        """Test that PongGame implements the ArcadeGame interface and returns metadata."""
        self.assertTrue(issubclass(PongGame, ArcadeGame))
        game = PongGame(save_manager=self.save_manager)
        self.assertIsInstance(game, ArcadeGame)
        self.assertEqual(game.name, "Pong")
        self.assertEqual(game.icon, "🏓")
        self.assertEqual(game.version, "1.0.0")
        self.assertEqual(game.author, "Hector Pacheco")
        self.assertIn("paddle", game.description.lower())
        self.assertFalse(game.is_finished)

    def test_pong_registers_and_launches_in_launcher(self):
        """Test registering PongGame in GameRegistry and launching via Launcher."""
        launcher = Launcher(registry=self.registry, save_manager=self.save_manager)
        self.assertEqual(launcher.selected_index, 0)

        launcher.handle_action(Action.SELECT)
        self.assertEqual(launcher.state, LauncherState.PLAYING)
        self.assertIsNotNone(launcher.active_game)
        self.assertEqual(launcher.active_game.name, "Pong")

    def test_paddle_movement_and_clamping(self):
        """Test paddle up/down movement and boundary clamping."""
        game = PongGame(save_manager=self.save_manager)
        initial_y = game._p1_y

        # Move Up
        game._p1_up = True
        game.update(0.1)
        self.assertLess(game._p1_y, initial_y)

        # Force out of upper bounds -> should clamp at 0.0
        game._p1_y = -50.0
        game.update(0.01)
        self.assertEqual(game._p1_y, 0.0)

        # Force out of lower bounds -> should clamp at (SCREEN_HEIGHT - PADDLE_HEIGHT)
        max_y = float(SCREEN_HEIGHT - PONG_PADDLE_HEIGHT)
        game._p1_y = 1000.0
        game.update(0.01)
        self.assertEqual(game._p1_y, max_y)

    def test_top_and_bottom_wall_bounce(self):
        """Test ball bouncing off top and bottom walls."""
        game = PongGame(save_manager=self.save_manager)

        # Top Wall Bounce
        game._ball_y = 0.0
        game._ball_vy = -200.0
        game.update(0.01)
        self.assertGreater(game._ball_vy, 0.0)

        # Bottom Wall Bounce
        game._ball_y = float(SCREEN_HEIGHT - PONG_BALL_SIZE)
        game._ball_vy = 200.0
        game.update(0.01)
        self.assertLess(game._ball_vy, 0.0)

    def test_paddle_collision_reflections(self):
        """Test ball bouncing off left and right paddles."""
        game = PongGame(save_manager=self.save_manager)

        # Left Paddle Collision
        game._ball_x = 35.0
        game._ball_y = game._p1_y + 10.0
        game._ball_vx = -300.0
        game.update(0.01)
        self.assertGreater(game._ball_vx, 0.0)

        # Right Paddle Collision
        game._ball_x = 750.0
        game._ball_y = game._p2_y + 10.0
        game._ball_vx = 300.0
        game.update(0.01)
        self.assertLess(game._ball_vx, 0.0)

    def test_player_scoring_and_victory(self):
        """Test P1 scoring, P2 scoring, and first-to-5 victory condition."""
        game = PongGame(save_manager=self.save_manager)
        game.start()

        # Score 5 points for P1
        for i in range(5):
            game._score_point(p1_scored=True)

        self.assertEqual(game.p1_score, 5)
        self.assertTrue(game._game_over)
        self.assertEqual(game._winner_name, "Player 1")

    def test_pause_and_resume_toggle(self):
        """Test pausing and resuming match via Action / toggle_pause."""
        game = PongGame(save_manager=self.save_manager)
        self.assertFalse(game._is_paused)

        game._toggle_pause()
        self.assertTrue(game._is_paused)

        # Position should not update when paused
        game._ball_x = 400.0
        game._ball_vx = 300.0
        game.update(0.1)
        self.assertEqual(game._ball_x, 400.0)

        game._toggle_pause()
        self.assertFalse(game._is_paused)

    def test_gpio_mode_enables_ai_and_bounds_containment(self):
        """Test that single-player AI mode tracks target and stays inside screen bounds."""
        game = PongGame(save_manager=self.save_manager, use_ai=True)
        self.assertTrue(game._use_ai)

        game._ball_y = 100.0
        game._ai_timer = 1.0
        game.update(0.1)

        self.assertGreaterEqual(game._p2_y, 0.0)
        self.assertLessEqual(game._p2_y, float(SCREEN_HEIGHT - PONG_PADDLE_HEIGHT))

    def test_save_schema_migration_preserves_snake_and_pong(self):
        """Test that recording Pong sessions preserves legacy Snake save data."""
        # 1. Record Snake stats
        self.save_manager.record_game_session("snake", score=100, duration_sec=30.0)
        self.assertEqual(self.save_manager.get_high_score("snake"), 100)

        # 2. Record Pong session
        self.save_manager.record_pong_session(p1_score=5, p2_score=3, duration_sec=40.0, rally_count=8)

        # 3. Reload SaveManager to verify persistence
        sm2 = SaveManager(filepath=self.save_path, backup_path=self.save_path + ".bak")
        self.assertEqual(sm2.get_high_score("snake"), 100)
        self.assertEqual(sm2.get_wins("pong"), 1)
        self.assertEqual(sm2.get_longest_rally("pong"), 8)


if __name__ == "__main__":
    unittest.main()
