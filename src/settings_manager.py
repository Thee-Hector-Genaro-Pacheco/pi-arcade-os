"""
Settings Manager module for Pi Arcade OS.

Provides persistent configuration management for audio channels, UI themes,
LCD brightness, game difficulty, and control schemes. Synchronized with SaveManager.
Supports live callbacks, score resetting, and default restoration.
Supports Python 3.9+ typing.
"""

import json
import logging
import os
from typing import Callable, Dict, List, Optional, Tuple, Union
from src.config import SETTINGS_FILE, THEME_PALETTES
from src.save_manager import SaveManager

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages application settings and synchronizes persistence with SaveManager."""

    THEME_OPTIONS: List[str] = ["Slate Dark", "Cyberpunk Gold", "Retro Monokai", "Neon Synthwave"]
    DIFFICULTY_OPTIONS: List[str] = ["Easy", "Normal", "Hard"]
    CONTROL_OPTIONS: List[str] = ["Arcade (GPIO + WASD)", "Keyboard Only"]

    def __init__(
        self,
        filepath: str = SETTINGS_FILE,
        save_manager: Optional[SaveManager] = None,
    ) -> None:
        """
        Initializes SettingsManager.

        Args:
            filepath: Path to legacy settings JSON file.
            save_manager: Optional active SaveManager instance.
        """
        self._filepath: str = filepath
        self._save_manager: Optional[SaveManager] = save_manager

        # Default Settings State
        self.master_volume: float = 0.7
        self.music_volume: float = 0.7
        self.effects_volume: float = 0.7
        self.lcd_brightness: float = 0.8
        self.theme: str = "Slate Dark"
        self.difficulty: str = "Normal"
        self.controls: str = "Arcade (GPIO + WASD)"

        # Registered change listeners
        self._listeners: List[Callable[["SettingsManager"], None]] = []

        # Load settings from disk or SaveManager
        self.load()

    def set_save_manager(self, save_manager: SaveManager) -> None:
        """Assigns active SaveManager instance and syncs settings."""
        self._save_manager = save_manager
        if self._save_manager and self._save_manager.settings:
            self._populate_from_dict(self._save_manager.settings)

    def register_listener(self, listener: Callable[["SettingsManager"], None]) -> None:
        """Registers a callback function to be invoked when settings change."""
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unregister_listener(self, listener: Callable[["SettingsManager"], None]) -> None:
        """Unregisters a settings change callback."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self) -> None:
        """Invokes all registered listener callbacks."""
        for listener in self._listeners:
            try:
                listener(self)
            except Exception as e:
                logger.error(f"Error in settings listener callback: {e}")

    def _populate_from_dict(self, data: Dict[str, Union[float, str]]) -> None:
        """Populates instance attributes from dictionary."""
        self.master_volume = max(0.0, min(1.0, float(data.get("master_volume", 0.7))))
        self.music_volume = max(0.0, min(1.0, float(data.get("music_volume", 0.7))))
        self.effects_volume = max(0.0, min(1.0, float(data.get("effects_volume", 0.7))))
        self.lcd_brightness = max(0.0, min(1.0, float(data.get("lcd_brightness", 0.8))))

        loaded_theme = str(data.get("theme", "Slate Dark"))
        self.theme = loaded_theme if loaded_theme in self.THEME_OPTIONS else "Slate Dark"

        loaded_diff = str(data.get("difficulty", "Normal"))
        self.difficulty = loaded_diff if loaded_diff in self.DIFFICULTY_OPTIONS else "Normal"

        loaded_ctrl = str(data.get("controls", "Arcade (GPIO + WASD)"))
        self.controls = loaded_ctrl if loaded_ctrl in self.CONTROL_OPTIONS else "Arcade (GPIO + WASD)"

    def load(self) -> None:
        """Loads settings from SaveManager or JSON disk storage."""
        if self._save_manager and self._save_manager.settings:
            self._populate_from_dict(self._save_manager.settings)
            logger.info(f"Loaded settings from SaveManager (Theme: {self.theme})")
            return

        if not os.path.exists(self._filepath):
            logger.info("No settings file found. Initializing defaults.")
            return

        try:
            with open(self._filepath, "r") as f:
                data = json.load(f)
            self._populate_from_dict(data)
            logger.info(f"Loaded settings from {self._filepath} (Theme: {self.theme})")
        except Exception as e:
            logger.warning(f"Error reading settings file ({e}). Falling back to defaults.")

    def save(self) -> None:
        """Saves current settings to SaveManager and JSON file."""
        data = {
            "master_volume": round(self.master_volume, 2),
            "music_volume": round(self.music_volume, 2),
            "effects_volume": round(self.effects_volume, 2),
            "lcd_brightness": round(self.lcd_brightness, 2),
            "theme": self.theme,
            "difficulty": self.difficulty,
            "controls": self.controls,
        }

        if self._save_manager:
            self._save_manager.settings = data
            self._save_manager.save()

        try:
            with open(self._filepath, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Settings saved to {self._filepath}")
        except Exception as e:
            logger.error(f"Failed to save settings file: {e}")

        self._notify_listeners()

    def restore_defaults(self) -> None:
        """Resets all settings to default values and saves."""
        self.master_volume = 0.7
        self.music_volume = 0.7
        self.effects_volume = 0.7
        self.lcd_brightness = 0.8
        self.theme = "Slate Dark"
        self.difficulty = "Normal"
        self.controls = "Arcade (GPIO + WASD)"
        self.save()
        logger.info("Restored default settings.")

    def reset_high_scores(self) -> None:
        """Clears all persistent high score and game stats files via SaveManager."""
        if self._save_manager:
            self._save_manager.reset_game_stats()
        self._notify_listeners()

    def get_theme_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Returns the active RGB color palette dictionary."""
        return THEME_PALETTES.get(self.theme, THEME_PALETTES["Slate Dark"])

    def get_effective_effects_volume(self) -> float:
        """Calculates effective sound effects volume."""
        return self.master_volume * self.effects_volume

    def get_effective_music_volume(self) -> float:
        """Calculates effective music volume."""
        return self.master_volume * self.music_volume

    def cycle_theme(self, step: int = 1) -> str:
        """Cycles to the next or previous theme and saves."""
        idx = self.THEME_OPTIONS.index(self.theme) if self.theme in self.THEME_OPTIONS else 0
        self.theme = self.THEME_OPTIONS[(idx + step) % len(self.THEME_OPTIONS)]
        self.save()
        return self.theme

    def cycle_difficulty(self, step: int = 1) -> str:
        """Cycles to the next or previous difficulty and saves."""
        idx = self.DIFFICULTY_OPTIONS.index(self.difficulty) if self.difficulty in self.DIFFICULTY_OPTIONS else 1
        self.difficulty = self.DIFFICULTY_OPTIONS[(idx + step) % len(self.DIFFICULTY_OPTIONS)]
        self.save()
        return self.difficulty

    def cycle_controls(self, step: int = 1) -> str:
        """Cycles to the next or previous control scheme and saves."""
        idx = self.CONTROL_OPTIONS.index(self.controls) if self.controls in self.CONTROL_OPTIONS else 0
        self.controls = self.CONTROL_OPTIONS[(idx + step) % len(self.CONTROL_OPTIONS)]
        self.save()
        return self.controls
