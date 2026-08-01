"""
Abstract Game Interface for Pi Arcade OS.

Defines the contract that all arcade games (Snake, Pong, Breakout, etc.)
must implement to integrate seamlessly into the Launcher framework.
Supports Python 3.9+ typing.
"""

from abc import ABC, abstractmethod
from typing import Optional, Union
import pygame
from src.config import Action


class ArcadeGame(ABC):
    """Abstract base class representing an arcade game in Pi Arcade OS."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the human-readable display name of the game."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Returns a short description of the game."""
        pass

    @property
    @abstractmethod
    def is_finished(self) -> bool:
        """Indicates whether the game session has concluded and should return to menu."""
        pass

    # Extended optional metadata properties with default values
    @property
    def version(self) -> str:
        """Returns the semantic version string of the game."""
        return "1.0.0"

    @property
    def author(self) -> str:
        """Returns the author or developer name of the game."""
        return "Hector Pacheco"

    @property
    def supports_gpio(self) -> bool:
        """Indicates whether the game supports physical GPIO button input."""
        return True

    @property
    def supports_keyboard(self) -> bool:
        """Indicates whether the game supports desktop keyboard controls."""
        return True

    @property
    def supports_audio(self) -> bool:
        """Indicates whether the game emits audio tones/sound effects."""
        return True

    @property
    def supports_lcd(self) -> bool:
        """Indicates whether the game displays score/status on the physical 16x2 LCD."""
        return True

    @property
    def thumbnail_path(self) -> Optional[str]:
        """Returns an optional path to a game thumbnail preview image."""
        return None

    @abstractmethod
    def start(self) -> None:
        """Initializes game state when launched from the arcade menu."""
        pass

    @abstractmethod
    def handle_event(self, event_or_action: Union[pygame.event.Event, Action]) -> None:
        """Processes user input, which can be a Pygame Event or an Action enum."""
        pass

    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Updates game state based on elapsed time (in seconds)."""
        pass

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Renders the game graphics onto the main Pygame surface."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Resets game logic back to the initial playable state."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Releases any resources held by the game instance before destruction."""
        pass
