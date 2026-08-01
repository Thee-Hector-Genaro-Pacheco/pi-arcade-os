# Developer Guide: Adding a New Game to Pi Arcade OS

This guide provides step-by-step instructions for creating a new game module and registering it with **Pi Arcade OS**.

---

## Overview

All games in Pi Arcade OS must implement the `ArcadeGame` interface located in [`src/game_interface.py`](file:///Users/hectorpacheco/.gemini/antigravity-ide/scratch/pi-arcade-os/src/game_interface.py). The `Launcher` engine automatically handles displaying your game in the menu, instantiating it, delegating inputs, passing shared service dependencies (`SaveManager`, `SettingsManager`, `AudioManager`, `DisplayManager`), and returning to the menu when finished.

---

## Step 1: Create Game Module File

Create a new Python file under `src/games/`, for example `src/games/tetris_game.py`.

```python
"""
Tetris Game implementation for Pi Arcade OS.
"""

from typing import Union, Optional
import pygame
from src.game_interface import ArcadeGame
from src.config import Action, SCREEN_WIDTH, SCREEN_HEIGHT
from src.save_manager import SaveManager
from src.settings_manager import SettingsManager
from src.hardware.audio import AudioManager
from src.hardware.display import DisplayManager


class TetrisGame(ArcadeGame):
    """Classic Tetris implementation for Pi Arcade OS."""

    def __init__(
        self,
        audio_manager: Optional[AudioManager] = None,
        display_manager: Optional[DisplayManager] = None,
        settings_manager: Optional[SettingsManager] = None,
        save_manager: Optional[SaveManager] = None,
    ) -> None:
        self._name: str = "Tetris"
        self._description: str = "Classic block-stacking puzzle game."
        self._version: str = "1.0.0"
        self._author: str = "Hector Pacheco"
        self._icon: str = "🧱"
        self._is_finished: bool = False
        self._score: int = 0

        self._audio_manager = audio_manager
        self._display_manager = display_manager
        self._settings_manager = settings_manager
        self._save_manager = save_manager or SaveManager()

        self.reset()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def version(self) -> str:
        return self._version

    @property
    def author(self) -> str:
        return self._author

    @property
    def icon(self) -> str:
        return self._icon

    @property
    def is_finished(self) -> bool:
        return self._is_finished

    def start(self) -> None:
        """Called when game is launched from arcade menu."""
        self._is_finished = False
        self.reset()

    def reset(self) -> None:
        """Reset game state."""
        self._score = 0
        self._is_finished = False

    def handle_event(self, event_or_action: Union[pygame.event.Event, Action]) -> None:
        """Process directional action or Pygame event."""
        if event_or_action in (Action.BACK, Action.QUIT):
            self._is_finished = True
            return

    def update(self, delta_time: float) -> None:
        """Update game physics, block drop, and line clears."""
        if self._is_finished:
            return

    def draw(self, surface: pygame.Surface) -> None:
        """Render graphics onto main Pygame surface using active theme colors."""
        colors = self._settings_manager.get_theme_colors() if self._settings_manager else {}
        surface.fill(colors.get("bg", (15, 23, 42)))

    def cleanup(self) -> None:
        """Release resources before returning to menu."""
        pass
```

---

## Step 2: Register Game Metadata in `src/main.py`

Open [`src/main.py`](file:///Users/hectorpacheco/.gemini/antigravity-ide/scratch/pi-arcade-os/src/main.py) and register your new game class with `GameRegistry`:

```python
from src.game_registry import GameRegistry, GameMetadata
from src.games.tetris_game import TetrisGame

# Inside main() function:
registry = GameRegistry()

registry.register(
    "tetris",
    TetrisGame,
    metadata=GameMetadata(
        id="tetris",
        name="Tetris",
        description="Classic block-stacking puzzle game.",
        version="1.0.0",
        author="Hector Pacheco",
        icon="🧱",
        supports_gpio=True,
        supports_keyboard=True,
        supports_audio=True,
        supports_lcd=True,
        is_coming_soon=False,
    ),
)
```

---

## Step 3: Write Unit Tests

Add tests in `tests/test_tetris.py` verifying interface compliance, registration, and physics:

```python
def test_tetris_game_implements_interface():
    from src.games.tetris_game import TetrisGame
    from src.game_interface import ArcadeGame
    assert issubclass(TetrisGame, ArcadeGame)
    game = TetrisGame()
    assert game.name == "Tetris"
    assert game.is_finished is False
```

---

## Step 4: Verify in Launcher

Run the launcher in keyboard mode:
```bash
python3 -m src.main
```
Your new game will now be listed in the **Hector Arcade OS** launcher menu alongside Snake and Pong with live hardware badges and persistent statistics!
