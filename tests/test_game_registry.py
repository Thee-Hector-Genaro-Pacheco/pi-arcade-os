"""
Unit tests for GameRegistry and GameMetadata in Pi Arcade OS.

Verifies registration, duplicate rejection, error handling, metadata enumeration,
coming-soon game previews, and fresh instance creation. Works with both unittest and pytest.
"""

import unittest
from src.game_interface import ArcadeGame
from src.game_registry import (
    GameRegistry,
    GameMetadata,
    DuplicateGameError,
    UnknownGameError,
    ComingSoonError,
)
from src.games.snake_game import SnakeGame


class MockGame(ArcadeGame):
    """Mock game implementation for unit testing."""

    def __init__(self) -> None:
        self._finished = False

    @property
    def name(self) -> str:
        return "Mock Game"

    @property
    def description(self) -> str:
        return "A mock game for testing."

    @property
    def is_finished(self) -> bool:
        return self._finished

    def start(self) -> None:
        self._finished = False

    def handle_event(self, event_or_action) -> None:
        pass

    def update(self, delta_time: float) -> None:
        pass

    def draw(self, surface) -> None:
        pass

    def reset(self) -> None:
        self._finished = False

    def cleanup(self) -> None:
        pass


class TestGameRegistry(unittest.TestCase):
    """Unit test suite for GameRegistry and metadata infrastructure."""

    def test_game_registration_succeeds(self):
        """Test registering a valid ArcadeGame class."""
        registry = GameRegistry()
        registry.register("mock", MockGame)
        self.assertTrue(registry.is_registered("mock"))
        self.assertEqual(registry.get_game_class("mock"), MockGame)

    def test_duplicate_game_id_rejected(self):
        """Test that registering a duplicate game ID raises DuplicateGameError."""
        registry = GameRegistry()
        registry.register("snake", SnakeGame)
        with self.assertRaises(DuplicateGameError):
            registry.register("snake", MockGame)

    def test_unknown_game_id_raises_clear_error(self):
        """Test that requesting an unregistered game ID raises UnknownGameError."""
        registry = GameRegistry()
        with self.assertRaises(UnknownGameError) as ctx:
            registry.create_instance("nonexistent_game")
        self.assertIn("nonexistent_game", str(ctx.exception))

    def test_registry_creates_fresh_instance_each_time(self):
        """Test that create_instance returns a distinct, fresh object every call."""
        registry = GameRegistry()
        registry.register("mock", MockGame)

        instance1 = registry.create_instance("mock")
        instance2 = registry.create_instance("mock")

        self.assertIsInstance(instance1, MockGame)
        self.assertIsInstance(instance2, MockGame)
        self.assertIsNot(instance1, instance2)

    def test_coming_soon_registration_and_error(self):
        """Test registering coming-soon games and catching ComingSoonError."""
        registry = GameRegistry()
        meta = GameMetadata(
            id="tetris",
            name="Tetris",
            description="Classic block-stacking puzzle game.",
            is_coming_soon=True,
        )
        registry.register_coming_soon(meta)

        self.assertTrue(registry.is_registered("tetris"))
        retrieved_meta = registry.get_metadata("tetris")
        self.assertEqual(retrieved_meta.name, "Tetris")
        self.assertTrue(retrieved_meta.is_coming_soon)

        with self.assertRaises(ComingSoonError):
            registry.get_game_class("tetris")

    def test_list_games_metadata(self):
        """Test that list_games returns accurate metadata dictionaries."""
        registry = GameRegistry()
        registry.register("snake", SnakeGame)
        registry.register_coming_soon(
            GameMetadata(id="pong", name="Pong", description="Table tennis", is_coming_soon=True)
        )

        games = registry.list_games()
        self.assertEqual(len(games), 2)
        ids = [g["id"] for g in games]
        self.assertIn("snake", ids)
        self.assertIn("pong", ids)


if __name__ == "__main__":
    unittest.main()
