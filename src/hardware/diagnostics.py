"""
Diagnostics module for Pi Arcade OS.

Collects and formats hardware status, runtime environment statistics,
Python/Pygame specs, display configuration, and registered games info.
Supports Python 3.9+ typing.
"""

import logging
import platform
import sys
from typing import Dict, List, Optional
import pygame

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    LCD_I2C_ADDRESS,
    GPIO_PIN_UP,
    GPIO_PIN_DOWN,
    GPIO_PIN_LEFT,
    GPIO_PIN_RIGHT,
    GPIO_PIN_BUZZER,
)
from src.game_registry import GameRegistry
from src.hardware.input_manager import InputManager
from src.hardware.display import DisplayManager
from src.hardware.audio import AudioManager

logger = logging.getLogger(__name__)


class SystemDiagnostics:
    """Provides system environment and hardware diagnostic reporting."""

    def __init__(
        self,
        registry: Optional[GameRegistry] = None,
        input_manager: Optional[InputManager] = None,
        display_manager: Optional[DisplayManager] = None,
        audio_manager: Optional[AudioManager] = None,
    ) -> None:
        """
        Initializes SystemDiagnostics with system components.

        Args:
            registry: Active GameRegistry instance.
            input_manager: Active InputManager instance.
            display_manager: Active DisplayManager instance.
            audio_manager: Active AudioManager instance.
        """
        self._registry: Optional[GameRegistry] = registry
        self._input_manager: Optional[InputManager] = input_manager
        self._display_manager: Optional[DisplayManager] = display_manager
        self._audio_manager: Optional[AudioManager] = audio_manager

    def get_hardware_status(self) -> Dict[str, str]:
        """Collects hardware subsystem status."""
        gpio_status = "Enabled (Physical Buttons)" if (self._input_manager and self._input_manager.is_gpio_enabled) else "Disabled (Keyboard Mode)"
        lcd_status = f"Connected (0x{LCD_I2C_ADDRESS:02x})" if (self._display_manager and self._display_manager.is_lcd_enabled) else "Disabled / Mock"

        if self._audio_manager and self._audio_manager.is_audio_enabled:
            vol_pct = int(self._audio_manager.volume * 100)
            mute_str = " (MUTED)" if self._audio_manager.is_muted() else ""
            audio_status = f"Enabled (PCM Synthesis / Buzzer) Vol: {vol_pct}%{mute_str}"
        else:
            audio_status = "Disabled / Quiet Mode"

        return {
            "GPIO": gpio_status,
            "LCD": lcd_status,
            "Audio": audio_status,
            "GPIO Pins": f"UP:{GPIO_PIN_UP}, DOWN:{GPIO_PIN_DOWN}, LEFT:{GPIO_PIN_LEFT}, RIGHT:{GPIO_PIN_RIGHT}, BUZZER:{GPIO_PIN_BUZZER}",
        }

    def get_environment_info(self) -> Dict[str, str]:
        """Collects Python runtime and system platform info."""
        return {
            "Python Version": sys.version.split()[0],
            "Pygame Version": pygame.version.ver,
            "Platform": sys.platform,
            "OS Details": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "Screen Resolution": f"{SCREEN_WIDTH}x{SCREEN_HEIGHT}",
            "Target FPS": f"{FPS}",
        }

    def get_games_summary(self) -> Dict[str, object]:
        """Collects registered games info."""
        if not self._registry:
            return {"Count": 0, "Games": []}

        games = self._registry.list_games()
        playable = [g["name"] for g in games if not g.get("is_coming_soon")]
        coming_soon = [g["name"] for g in games if g.get("is_coming_soon")]

        return {
            "Total Count": len(games),
            "Playable Games": playable,
            "Coming Soon": coming_soon,
        }

    def generate_report(self) -> str:
        """Formats complete diagnostic report into a readable string."""
        hw = self.get_hardware_status()
        env = self.get_environment_info()
        games = self.get_games_summary()

        report_lines = [
            "==================================================",
            "           HECTOR ARCADE OS DIAGNOSTICS           ",
            "==================================================",
            "--- Hardware Subsystem Status ---",
            f"  • GPIO Input:    {hw['GPIO']}",
            f"  • I2C LCD (16x2):{hw['LCD']}",
            f"  • Audio Subsystem:{hw['Audio']}",
            f"  • Pin Mapping:   {hw['GPIO Pins']}",
            "",
            "--- Environment & Runtime ---",
            f"  • Python:        {env['Python Version']}",
            f"  • Pygame:        {env['Pygame Version']}",
            f"  • Platform:      {env['Platform']} ({env['OS Details']})",
            f"  • Display:       {env['Screen Resolution']} @ {env['Target FPS']} FPS",
            "",
            "--- Game Registry ---",
            f"  • Registered:    {games['Total Count']} Game(s)",
            f"  • Playable:      {', '.join(games['Playable Games']) if games['Playable Games'] else 'None'}",
            f"  • Coming Soon:   {', '.join(games['Coming Soon']) if games['Coming Soon'] else 'None'}",
            "==================================================",
        ]
        return "\n".join(report_lines)
