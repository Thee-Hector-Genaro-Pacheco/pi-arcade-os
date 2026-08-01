"""
Unit test suite for BootSequence, System Diagnostics, and Statistics view in Pi Arcade OS.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame

pygame.init()
pygame.display.set_mode((100, 100))

from src.config import Action
from src.boot_sequence import BootSequence, BootState
from src.game_registry import GameRegistry, GameMetadata
from src.games.snake_game import SnakeGame
from src.games.pong_game import PongGame
from src.games.tetris_game import TetrisGame
from src.launcher import Launcher, LauncherState
from src.save_manager import SaveManager


class TestBootAndStats(unittest.TestCase):
    """Unit tests for animated boot sequence transitions, diagnostics logging, and Statistics screen."""

    def setUp(self):
        self.save_manager = SaveManager(filepath="test_boot_save.json", backup_path="test_boot_save.json.bak")
        self.save_manager.reset_all()

        self.registry = GameRegistry()
        self.registry.register("snake", SnakeGame)
        self.registry.register("pong", PongGame)
        self.registry.register("tetris", TetrisGame)
        self.registry.register_coming_soon(
            GameMetadata(id="breakout", name="Breakout", description="Brick buster", is_coming_soon=True)
        )

    def tearDown(self):
        for path in ["test_boot_save.json", "test_boot_save.json.bak"]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def test_boot_sequence_fast_mode_transitions_to_finished(self):
        boot = BootSequence(fast_mode=True)
        self.assertFalse(boot.is_finished)

        # Step update loop
        for _ in range(50):
            boot.update(0.05)

        self.assertTrue(boot.is_finished)

    def test_boot_sequence_headless_draw(self):
        boot = BootSequence(fast_mode=True)
        surface = pygame.Surface((800, 600))
        boot.draw(surface)  # Should execute cleanly without error

    def test_launcher_open_stats_view_modal(self):
        launcher = Launcher(registry=self.registry, save_manager=self.save_manager)
        launcher.open_stats_view()
        self.assertEqual(launcher.state, LauncherState.SHOWING_STATS)

        # Press ESC to exit Stats view back to MENU
        event_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        launcher.handle_pygame_event(event_esc)
        self.assertEqual(launcher.state, LauncherState.MENU)

    def test_launcher_stats_modal_draw(self):
        launcher = Launcher(registry=self.registry, save_manager=self.save_manager)
        launcher.open_stats_view()
        surface = pygame.Surface((800, 600))
        launcher.draw(surface)  # Renders stats modal cleanly

    def test_save_manager_aggregate_statistics(self):
        self.save_manager.record_game_session("snake", 50, 20.0)
        self.save_manager.record_pong_session(5, 2, 40.0, 10)
        self.save_manager.record_tetris_session(600, 5, 1, 0, 30.0)

        self.assertEqual(self.save_manager.get_total_games_played(), 3)
        self.assertIn(self.save_manager.get_favorite_game(), ["Snake", "Pong", "Tetris"])
        self.assertGreater(self.save_manager.get_average_session_length(), 0.0)


if __name__ == "__main__":
    unittest.main()
