"""
Game Registry module for Pi Arcade OS.

Manages registration, lookup, rich metadata enumeration, and instantiation
of playable ArcadeGame classes and coming-soon game previews.
Supports Python 3.9+ typing.
"""

from dataclasses import dataclass, field
import logging
from typing import Dict, List, Optional, Type
from src.game_interface import ArcadeGame

logger = logging.getLogger(__name__)


@dataclass
class GameMetadata:
    """Dataclass encapsulating comprehensive metadata for an arcade game."""
    id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Hector Pacheco"
    icon: str = "🎮"
    supports_gpio: bool = True
    supports_keyboard: bool = True
    supports_audio: bool = True
    supports_lcd: bool = True
    thumbnail_path: Optional[str] = None
    is_coming_soon: bool = False
    estimated_release: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        """Converts metadata instance into a dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "icon": self.icon,
            "supports_gpio": self.supports_gpio,
            "supports_keyboard": self.supports_keyboard,
            "supports_audio": self.supports_audio,
            "supports_lcd": self.supports_lcd,
            "thumbnail_path": self.thumbnail_path,
            "is_coming_soon": self.is_coming_soon,
            "estimated_release": self.estimated_release,
        }


class GameRegistryError(Exception):
    """Custom exception raised for GameRegistry errors."""
    pass


class DuplicateGameError(GameRegistryError):
    """Raised when attempting to register a game ID that is already registered."""
    pass


class UnknownGameError(GameRegistryError):
    """Raised when requesting a game ID that has not been registered."""
    pass


class ComingSoonError(GameRegistryError):
    """Raised when attempting to instantiate a game marked as coming soon."""
    pass


class GameRegistry:
    """Registry class responsible for managing registered games and metadata in Pi Arcade OS."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[ArcadeGame]] = {}
        self._metadata_store: Dict[str, GameMetadata] = {}

    def register(
        self,
        game_id: str,
        game_cls: Type[ArcadeGame],
        metadata: Optional[GameMetadata] = None,
    ) -> None:
        """
        Registers a playable ArcadeGame subclass with a unique string ID and metadata.

        Args:
            game_id: Unique string identifier for the game.
            game_cls: Class implementing the ArcadeGame interface.
            metadata: Optional GameMetadata object. If omitted, metadata is inferred from the class.

        Raises:
            DuplicateGameError: If game_id is already registered as a playable game.
            TypeError: If game_cls is not a subclass of ArcadeGame.
        """
        if not issubclass(game_cls, ArcadeGame):
            raise TypeError(f"Class '{game_cls.__name__}' must implement ArcadeGame interface.")

        clean_id = game_id.strip().lower()
        if not clean_id:
            raise ValueError("Game ID cannot be empty.")

        if clean_id in self._registry:
            logger.error(f"Failed to register duplicate game ID: {clean_id}")
            raise DuplicateGameError(f"Game ID '{clean_id}' is already registered as playable.")

        # Infer metadata if not explicitly provided
        if metadata is None:
            temp_instance = game_cls()
            metadata = GameMetadata(
                id=clean_id,
                name=temp_instance.name,
                description=temp_instance.description,
                version=getattr(temp_instance, "version", "1.0.0"),
                author=getattr(temp_instance, "author", "Hector Pacheco"),
                icon=getattr(temp_instance, "icon", "🎮"),
                supports_gpio=getattr(temp_instance, "supports_gpio", True),
                supports_keyboard=getattr(temp_instance, "supports_keyboard", True),
                supports_audio=getattr(temp_instance, "supports_audio", True),
                supports_lcd=getattr(temp_instance, "supports_lcd", True),
                thumbnail_path=getattr(temp_instance, "thumbnail_path", None),
                is_coming_soon=False,
            )
        else:
            metadata.is_coming_soon = False

        self._registry[clean_id] = game_cls
        self._metadata_store[clean_id] = metadata
        logger.info(f"Successfully registered game ID '{clean_id}' with class {game_cls.__name__}")

    def register_coming_soon(self, metadata: GameMetadata) -> None:
        """
        Registers a coming-soon preview game into the registry metadata infrastructure.

        Args:
            metadata: GameMetadata object with is_coming_soon=True.
        """
        clean_id = metadata.id.strip().lower()
        if not clean_id:
            raise ValueError("Game ID cannot be empty.")

        if clean_id in self._metadata_store:
            raise DuplicateGameError(f"Game ID '{clean_id}' is already registered.")

        metadata.is_coming_soon = True
        self._metadata_store[clean_id] = metadata
        logger.info(f"Registered coming-soon game preview '{clean_id}' ({metadata.name})")

    def get_game_class(self, game_id: str) -> Type[ArcadeGame]:
        """
        Retrieves the registered game class for a given ID.

        Args:
            game_id: Unique string identifier for the game.

        Returns:
            The ArcadeGame subclass associated with game_id.

        Raises:
            UnknownGameError: If game_id is not registered.
            ComingSoonError: If game_id is a preview game with no class implementation yet.
        """
        clean_id = game_id.strip().lower()
        if clean_id not in self._metadata_store:
            raise UnknownGameError(f"Game ID '{clean_id}' is not registered in GameRegistry.")

        if clean_id not in self._registry:
            raise ComingSoonError(f"Game '{clean_id}' is currently coming soon and not yet playable.")

        return self._registry[clean_id]

    def get_metadata(self, game_id: str) -> GameMetadata:
        """Retrieves GameMetadata for a registered game ID."""
        clean_id = game_id.strip().lower()
        if clean_id not in self._metadata_store:
            raise UnknownGameError(f"Game ID '{clean_id}' is not registered in GameRegistry.")
        return self._metadata_store[clean_id]

    def create_instance(self, game_id: str) -> ArcadeGame:
        """
        Instantiates a fresh ArcadeGame object for the specified game ID.

        Args:
            game_id: Unique string identifier for the game.

        Returns:
            A new instance of the registered ArcadeGame subclass.
        """
        game_cls = self.get_game_class(game_id)
        logger.info(f"Creating fresh instance of game '{game_id}'")
        return game_cls()

    def list_games(self) -> List[Dict[str, object]]:
        """
        Returns metadata dictionaries for all registered playable and preview games in insertion order.

        Returns:
            List of metadata dictionaries.
        """
        return [meta.to_dict() for meta in self._metadata_store.values()]

    def list_metadata_objects(self) -> List[GameMetadata]:
        """Returns list of GameMetadata dataclass objects."""
        return list(self._metadata_store.values())

    def is_registered(self, game_id: str) -> bool:
        """Checks whether a game ID is currently registered."""
        return game_id.strip().lower() in self._metadata_store

    def clear(self) -> None:
        """Clears all registered games and metadata."""
        self._registry.clear()
        self._metadata_store.clear()
