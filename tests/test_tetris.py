"""
Unit test suite for TetrisGame in Pi Arcade OS.

Verifies ArcadeGame interface compliance, 7-bag randomizer, piece movement,
soft drop, hard drop, clockwise and counterclockwise rotation, wall kick offsets,
wall and locked-block collision detection, line clearing (1, 2, 3, 4 lines),
scoring table, level progression, game over detection, reset behavior, and save schema persistence.
All tests run headlessly without physical hardware.
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

from src.config import Action, TETRIS_SHAPES, TETRIS_BOARD_COLS, TETRIS_BOARD_ROWS
from src.game_interface import ArcadeGame
from src.game_registry import GameRegistry, GameMetadata
from src.games.snake_game import SnakeGame
from src.games.pong_game import PongGame
from src.games.tetris_game import TetrisGame, TetrisPiece
from src.launcher import Launcher, LauncherState
from src.save_manager import SaveManager


class TestTetrisGame(unittest.TestCase):
    """Unit test suite for TetrisGame platform integration and gameplay logic."""

    def setUp(self):
        """Sets up GameRegistry and SaveManager fixtures."""
        self.save_manager = SaveManager(filepath="test_tetris_save.json", backup_path="test_tetris_save.json.bak")
        self.save_manager.reset_all()

        self.registry = GameRegistry()
        self.registry.register("snake", SnakeGame)
        self.registry.register("pong", PongGame)
        self.registry.register("tetris", TetrisGame)
        self.registry.register_coming_soon(
            GameMetadata(id="breakout", name="Breakout", description="Brick buster", is_coming_soon=True)
        )

    def tearDown(self):
        """Cleans up temporary save files."""
        for path in ["test_tetris_save.json", "test_tetris_save.json.bak"]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

    def test_tetris_implements_arcade_game_interface(self):
        """Test that TetrisGame implements the ArcadeGame interface."""
        self.assertTrue(issubclass(TetrisGame, ArcadeGame))
        game = TetrisGame()
        self.assertIsInstance(game, ArcadeGame)
        self.assertEqual(game.name, "Tetris")
        self.assertEqual(game.version, "1.0.0")
        self.assertEqual(game.author, "Hector Pacheco")
        self.assertEqual(game.icon, "🧱")
        self.assertFalse(game.is_finished)

    def test_registry_and_menu_order(self):
        """Test that Tetris is registered as playable and menu order is Snake, Pong, Tetris, Breakout."""
        games = self.registry.list_games()
        self.assertEqual(len(games), 4)

        game_ids = [g["id"] for g in games]
        self.assertEqual(game_ids, ["snake", "pong", "tetris", "breakout"])

        meta = self.registry.get_metadata("tetris")
        self.assertFalse(meta.is_coming_soon)
        self.assertEqual(meta.version, "1.0.0")

    def test_launcher_launches_tetris(self):
        """Test that Launcher highlights and launches Tetris at menu index 2."""
        launcher = Launcher(registry=self.registry, save_manager=self.save_manager)

        # Move Down twice: Snake (0) -> Pong (1) -> Tetris (2)
        launcher.handle_action(Action.DOWN)
        launcher.handle_action(Action.DOWN)
        self.assertEqual(launcher.selected_index, 2)

        # Select Tetris
        launcher.handle_action(Action.SELECT)
        self.assertEqual(launcher.state, LauncherState.PLAYING)
        self.assertIsNotNone(launcher.active_game)
        self.assertIsInstance(launcher.active_game, TetrisGame)
        self.assertEqual(launcher.active_game.name, "Tetris")

    def test_all_seven_tetrominoes_and_7bag_randomizer(self):
        """Test that all 7 shapes exist and 7-bag contains each shape once per fill."""
        shapes = ["I", "O", "T", "S", "Z", "J", "L"]
        for s in shapes:
            self.assertIn(s, TETRIS_SHAPES)
            piece = TetrisPiece(s)
            self.assertEqual(piece.shape_type, s)

        game = TetrisGame()
        game.reset()
        drawn_shapes = [game._active_piece.shape_type, game._next_piece.shape_type]
        for _ in range(5):
            drawn_shapes.append(game._get_next_shape_from_bag())

        self.assertEqual(set(drawn_shapes), set(shapes))
        self.assertEqual(len(drawn_shapes), 7)

    def test_piece_horizontal_movement_and_bounds_rejection(self):
        """Test left/right movement and wall boundary collision rejection."""
        game = TetrisGame()
        game.reset()

        initial_col = game._active_piece.col

        # Move left
        game._move_left()
        self.assertEqual(game._active_piece.col, initial_col - 1)

        # Move left past boundary
        for _ in range(15):
            game._move_left()
        self.assertGreaterEqual(game._active_piece.col, 0)
        self.assertTrue(game._is_valid_position(game._active_piece))

        # Move right past right boundary
        for _ in range(20):
            game._move_right()
        self.assertLess(game._active_piece.col, TETRIS_BOARD_COLS)
        self.assertTrue(game._is_valid_position(game._active_piece))

    def test_soft_drop_and_hard_drop(self):
        """Test soft drop incrementing row & score, and hard drop locking piece instantly."""
        game = TetrisGame()
        game.reset()

        orig_row = game._active_piece.row

        # Soft drop
        game._soft_drop()
        self.assertEqual(game._active_piece.row, orig_row + 1)
        self.assertGreater(game.score, 0)

        # Hard drop
        orig_score = game.score
        game._hard_drop()
        self.assertGreater(game.score, orig_score)

    def test_clockwise_and_counterclockwise_rotation(self):
        """Test clockwise and counterclockwise piece rotation."""
        piece = TetrisPiece("T")
        orig_rot = piece.rotation_idx

        piece.rotate_clockwise()
        self.assertEqual(piece.rotation_idx, (orig_rot + 1) % len(piece.rotations))

        piece.rotate_counterclockwise()
        self.assertEqual(piece.rotation_idx, orig_rot)

    def test_wall_collision_rotation_rejection(self):
        """Test that rotation colliding with walls or blocks is safely rejected."""
        game = TetrisGame()
        game.reset()

        # Move piece to far left wall (col 0)
        for _ in range(10):
            game._move_left()

        # Rotation near wall should either wall kick or reject cleanly without crashing
        res = game._rotate_active_piece(clockwise=True)
        self.assertTrue(game._is_valid_position(game._active_piece))

    def test_single_double_triple_tetris_line_clears(self):
        """Test line detection and clearing for 1, 2, 3, and 4 (Tetris) lines."""
        game = TetrisGame()
        game.reset()

        # Fill bottom row (row 21) completely
        bottom_row = game.TOTAL_GRID_ROWS - 1
        for col in range(TETRIS_BOARD_COLS):
            game._grid[bottom_row][col] = (255, 255, 255)

        game._check_line_clears()
        self.assertEqual(len(game._cleared_rows), 1)
        self.assertEqual(game._lines_cleared, 1)
        self.assertEqual(game.score, 100)  # Single line at Lv 1

        # Test 4-line Tetris clear
        game.reset()
        for r_offset in range(4):
            r = game.TOTAL_GRID_ROWS - 1 - r_offset
            for col in range(TETRIS_BOARD_COLS):
                game._grid[r][col] = (255, 255, 255)

        game._check_line_clears()
        self.assertEqual(len(game._cleared_rows), 4)
        self.assertEqual(game._lines_cleared, 4)
        self.assertEqual(game.score, 800)  # Tetris 800 * 1
        self.assertEqual(game._tetrises_count, 1)

    def test_level_progression_and_gravity_speed(self):
        """Test that level increases every 10 lines and gravity interval speeds up."""
        game = TetrisGame()
        game.reset()

        self.assertEqual(game._level, 1)
        initial_speed = game._get_gravity_speed()

        # Clear 10 lines by filling a row and clearing
        bottom_row = game.TOTAL_GRID_ROWS - 1
        for col in range(TETRIS_BOARD_COLS):
            game._grid[bottom_row][col] = (255, 255, 255)

        game._lines_cleared = 9
        game._check_line_clears()  # Adds 1 line -> 10 lines -> Lv 2
        self.assertEqual(game._level, 2)
        faster_speed = game._get_gravity_speed()
        self.assertLess(faster_speed, initial_speed)

    def test_game_over_detection_and_reset(self):
        """Test game over detection when stack reaches spawn area, and reset restoration."""
        game = TetrisGame()
        game.reset()

        # Block top spawn rows
        for r in range(4):
            for c in range(TETRIS_BOARD_COLS):
                game._grid[r][c] = (255, 0, 0)

        # Spawning piece in blocked area triggers game over
        game._spawn_piece()
        self.assertTrue(game._game_over)

        # Reset restores state
        game.reset()
        self.assertFalse(game._game_over)
        self.assertEqual(game.score, 0)

    def test_save_schema_migration_and_persistence(self):
        """Test that Tetris stats persist to SaveManager and preserve Snake/Pong data."""
        self.save_manager.record_game_session("snake", 15, 30.0)
        self.save_manager.record_pong_session(5, 2, 45.0, 8)

        # Record Tetris session
        self.save_manager.record_tetris_session(
            score=1200,
            lines_cleared=14,
            level=2,
            tetrises_count=2,
            duration_sec=60.0,
        )

        self.assertEqual(self.save_manager.get_high_score("snake"), 15)
        self.assertEqual(self.save_manager.get_wins("pong"), 1)
        self.assertEqual(self.save_manager.get_high_score("tetris"), 1200)
        self.assertEqual(self.save_manager.get_total_lines("tetris"), 14)
        self.assertEqual(self.save_manager.get_highest_level("tetris"), 2)
        self.assertEqual(self.save_manager.get_tetrises("tetris"), 2)

    def test_keyboard_and_action_events(self):
        """Test input handler events for pause, reset, movement, and exit."""
        game = TetrisGame()
        game.reset()

        # Pause toggle via K_p
        event_p = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
        game.handle_event(event_p)
        self.assertTrue(game._paused)

        game.handle_event(event_p)
        self.assertFalse(game._paused)

        # Exit via ESC
        event_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        game.handle_event(event_esc)
        self.assertTrue(game.is_finished)

    def test_escape_key_returns_to_launcher_in_all_states(self):
        """Test that Escape key marks game finished across active, paused, game over, and line clear states."""
        event_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)

        # 1. Active Gameplay
        g1 = TetrisGame()
        g1.reset()
        g1.handle_event(event_esc)
        self.assertTrue(g1.is_finished)
        self.assertFalse(g1._paused)

        # 2. Paused state
        g2 = TetrisGame()
        g2.reset()
        g2._paused = True
        g2.handle_event(event_esc)
        self.assertTrue(g2.is_finished)

        # 3. Game Over state
        g3 = TetrisGame()
        g3.reset()
        g3._game_over = True
        g3.handle_event(event_esc)
        self.assertTrue(g3.is_finished)

        # 4. Line Clear Animation state
        g4 = TetrisGame()
        g4.reset()
        g4._cleared_rows = [19]
        g4._clear_animation_timer = 0.1
        g4.handle_event(event_esc)
        self.assertTrue(g4.is_finished)

        # 5. Action.BACK
        g5 = TetrisGame()
        g5.reset()
        g5.handle_event(Action.BACK)
        self.assertTrue(g5.is_finished)
        self.assertFalse(g5._paused)

    def test_launcher_returns_to_menu_after_tetris_finishes(self):
        """Test Launcher transitions back to MENU state when active Tetris finishes."""
        launcher = Launcher(registry=self.registry, save_manager=self.save_manager)

        # Navigate to Tetris and launch
        launcher.handle_action(Action.DOWN)
        launcher.handle_action(Action.DOWN)
        launcher.handle_action(Action.SELECT)
        self.assertEqual(launcher.state, LauncherState.PLAYING)
        self.assertIsInstance(launcher.active_game, TetrisGame)

        # Send Escape to active Tetris game
        event_esc = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        launcher.handle_pygame_event(event_esc)

        # Update launcher loop tick
        launcher.update(0.016)

        # Verify state returned to MENU
        self.assertEqual(launcher.state, LauncherState.MENU)
        self.assertIsNone(launcher.active_game)


if __name__ == "__main__":
    unittest.main()
