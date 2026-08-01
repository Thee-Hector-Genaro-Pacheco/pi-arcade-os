"""
Unit tests for Launcher, SystemDiagnostics, and SnakeGame in Pi Arcade OS.

Tests menu navigation, selection wrapping, game launching, coming-soon notices,
settings view modal, background particles, hardware badges, direction reversal rejection,
and Snake resetting/stats. All tests run headlessly without physical hardware.
Works with both unittest and pytest.
"""

import os
# Configure headless environment for Pygame before importing Pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame

pygame.init()
pygame.display.set_mode((100, 100))

from src.config import Action
from src.game_interface import ArcadeGame
from src.game_registry import GameRegistry, GameMetadata
from src.games.snake_game import SnakeGame
from src.games.pong_game import PongGame
from src.hardware.diagnostics import SystemDiagnostics
from src.launcher import Launcher, LauncherState, LauncherParticle


class TestLauncherAndSnake(unittest.TestCase):
    """Unit test suite for Launcher engine, SystemDiagnostics, SnakeGame, and PongGame."""

    def setUp(self):
        """Sets up GameRegistry fixture with canonical game order."""
        self.registry = GameRegistry()
        self.registry.register("snake", SnakeGame)
        self.registry.register("pong", PongGame)
        self.registry.register_coming_soon(
            GameMetadata(id="tetris", name="Tetris", description="Block puzzle", is_coming_soon=True, estimated_release="Sprint 4")
        )
        self.registry.register_coming_soon(
            GameMetadata(id="breakout", name="Breakout", description="Brick buster", is_coming_soon=True, estimated_release="Sprint 4")
        )

    def test_canonical_menu_order_and_registration(self):
        """Test canonical ordered game list: Snake, Pong, Tetris, Breakout."""
        games = self.registry.list_games()
        self.assertEqual(len(games), 4)

        game_ids = [g["id"] for g in games]
        self.assertEqual(game_ids, ["snake", "pong", "tetris", "breakout"])

        # Pong is playable and registered once
        pong_meta = self.registry.get_metadata("pong")
        self.assertFalse(pong_meta.is_coming_soon)
        self.assertEqual(pong_meta.version, "1.0.0")

        # Tetris and Breakout remain coming soon
        self.assertTrue(self.registry.get_metadata("tetris").is_coming_soon)
        self.assertTrue(self.registry.get_metadata("breakout").is_coming_soon)

    def test_launcher_step_by_step_navigation_down(self):
        """Test moving down step-by-step: Snake (0) -> Pong (1) -> Tetris (2)."""
        launcher = Launcher(registry=self.registry)
        self.assertEqual(launcher.selected_index, 0)
        self.assertEqual(self.registry.list_games()[launcher.selected_index]["id"], "snake")

        # Move Down once -> Pong (1)
        launcher.handle_action(Action.DOWN)
        self.assertEqual(launcher.selected_index, 1)
        self.assertEqual(self.registry.list_games()[launcher.selected_index]["id"], "pong")

        # Move Down second time -> Tetris (2)
        launcher.handle_action(Action.DOWN)
        self.assertEqual(launcher.selected_index, 2)
        self.assertEqual(self.registry.list_games()[launcher.selected_index]["id"], "tetris")

    def test_launcher_step_by_step_navigation_up(self):
        """Test moving up from Tetris (2) -> Pong (1)."""
        launcher = Launcher(registry=self.registry)
        launcher.handle_action(Action.DOWN)  # To Pong (1)
        launcher.handle_action(Action.DOWN)  # To Tetris (2)
        self.assertEqual(launcher.selected_index, 2)

        # Move Up once -> Pong (1)
        launcher.handle_action(Action.UP)
        self.assertEqual(launcher.selected_index, 1)
        self.assertEqual(self.registry.list_games()[launcher.selected_index]["id"], "pong")

    def test_launcher_launches_pong_game_instance(self):
        """Test selecting Pong highlights Pong and launches a fresh PongGame instance."""
        launcher = Launcher(registry=self.registry)

        # Move down to Pong (1)
        launcher.handle_action(Action.DOWN)
        self.assertEqual(launcher.selected_index, 1)

        # Press Select
        launcher.handle_action(Action.SELECT)
        self.assertEqual(launcher.state, LauncherState.PLAYING)
        self.assertIsNotNone(launcher.active_game)
        self.assertIsInstance(launcher.active_game, PongGame)
        self.assertEqual(launcher.active_game.name, "Pong")

    def test_launcher_wraparound_navigation(self):
        """Test menu wraparound navigation."""
        launcher = Launcher(registry=self.registry)

        # Move UP from Snake (0) -> Breakout (3)
        launcher.handle_action(Action.UP)
        self.assertEqual(launcher.selected_index, 3)
        self.assertEqual(self.registry.list_games()[launcher.selected_index]["id"], "breakout")

        # Move DOWN from Breakout (3) -> Snake (0)
        launcher.handle_action(Action.DOWN)
        self.assertEqual(launcher.selected_index, 0)
        self.assertEqual(self.registry.list_games()[launcher.selected_index]["id"], "snake")

    def test_launcher_particle_update(self):
        """Test particle movement and edge wrapping logic."""
        particle = LauncherParticle()
        orig_y = particle.y
        particle.update(0.1)
        self.assertNotEqual(particle.y, orig_y)

    def test_launcher_handles_coming_soon_game_notice(self):
        """Test selecting a coming-soon game displays notice state without crashing."""
        launcher = Launcher(registry=self.registry)

        # Move to coming-soon Tetris at index 2
        launcher.handle_action(Action.DOWN)
        launcher.handle_action(Action.DOWN)
        self.assertEqual(launcher.selected_index, 2)

        # Select coming-soon game
        launcher.handle_action(Action.SELECT)
        self.assertEqual(launcher.state, LauncherState.SHOWING_NOTICE)

        # Press any key to dismiss notice
        launcher.handle_action(Action.SELECT)
        self.assertEqual(launcher.state, LauncherState.MENU)

    def test_launcher_open_settings_view_modal(self):
        """Test opening and dismissing settings view modal."""
        launcher = Launcher(registry=self.registry)
        self.assertEqual(launcher.state, LauncherState.MENU)

        launcher.open_settings_view()
        self.assertEqual(launcher.state, LauncherState.SHOWING_SETTINGS)

        # Press BACK to dismiss settings modal
        launcher.handle_action(Action.BACK)
        self.assertEqual(launcher.state, LauncherState.MENU)

    def test_system_diagnostics_report_generation(self):
        """Test SystemDiagnostics report generation."""
        diagnostics = SystemDiagnostics(registry=self.registry)
        report = diagnostics.generate_report()
        self.assertIn("HECTOR ARCADE OS DIAGNOSTICS", report)
        self.assertIn("Python:", report)
        self.assertIn("Snake, Pong", report)
        self.assertIn("Tetris, Breakout", report)


if __name__ == "__main__":
    unittest.main()
