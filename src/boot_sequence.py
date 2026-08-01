"""
Boot Sequence module for Pi Arcade OS.

Renders retro arcade CRT terminal boot sequence displaying system initialization steps,
hardware diagnostics checkmarks (✓), installed games catalog, version header,
boot sound synthesis, and smooth alpha fade-out transition into the launcher menu.
Supports Python 3.9+ typing.
"""

from enum import Enum
import logging
import time
from typing import Optional, List, Tuple
import pygame

from src.config import SCREEN_WIDTH, SCREEN_HEIGHT
from src.version import VERSION, get_version_info
from src.hardware.audio import AudioManager
from src.hardware.display import DisplayManager

logger = logging.getLogger(__name__)


class BootState(Enum):
    """Boot sequence animation state machine."""
    AUDIO_INIT = "AUDIO_INIT"
    SAVE_INIT = "SAVE_INIT"
    SETTINGS_INIT = "SETTINGS_INIT"
    GAME_SCAN = "GAME_SCAN"
    READY = "READY"
    FADING = "FADING"
    FINISHED = "FINISHED"


class BootSequence:
    """Manages 60 FPS terminal boot sequence rendering and state transitions."""

    def __init__(
        self,
        audio_manager: Optional[AudioManager] = None,
        display_manager: Optional[DisplayManager] = None,
        fast_mode: bool = False,
    ) -> None:
        """
        Initializes BootSequence.

        Args:
            audio_manager: Optional AudioManager instance for boot sound.
            display_manager: Optional DisplayManager instance for LCD.
            fast_mode: Accelerates timers for unit tests.
        """
        self._audio_manager: Optional[AudioManager] = audio_manager
        self._display_manager: Optional[DisplayManager] = display_manager
        self._fast_mode: bool = fast_mode

        self._state: BootState = BootState.AUDIO_INIT
        self._state_timer: float = 0.0
        self._total_timer: float = 0.0

        # Step durations
        self._step_delay: float = 0.05 if fast_mode else 0.30
        self._fade_duration: float = 0.10 if fast_mode else 0.60

        self._audio_done: bool = False
        self._save_done: bool = False
        self._settings_done: bool = False
        self._games_done: bool = False
        self._played_boot_sound: bool = False

        if self._display_manager:
            self._display_manager.write_lines("HECTOR ARCADE OS", f"Booting v{VERSION}...")

    @property
    def is_finished(self) -> bool:
        """Returns True when boot sequence animation and fade-out complete."""
        return self._state == BootState.FINISHED

    def update(self, delta_time: float) -> None:
        """Updates animation timers and state transitions."""
        if self._state == BootState.FINISHED:
            return

        self._state_timer += delta_time
        self._total_timer += delta_time

        if self._state == BootState.AUDIO_INIT:
            if self._state_timer >= self._step_delay:
                self._audio_done = True
                self._state = BootState.SAVE_INIT
                self._state_timer = 0.0

        elif self._state == BootState.SAVE_INIT:
            if self._state_timer >= self._step_delay:
                self._save_done = True
                self._state = BootState.SETTINGS_INIT
                self._state_timer = 0.0

        elif self._state == BootState.SETTINGS_INIT:
            if self._state_timer >= self._step_delay:
                self._settings_done = True
                self._state = BootState.GAME_SCAN
                self._state_timer = 0.0

        elif self._state == BootState.GAME_SCAN:
            if self._state_timer >= self._step_delay * 1.5:
                self._games_done = True
                self._state = BootState.READY
                self._state_timer = 0.0
                if self._audio_manager and not self._played_boot_sound:
                    self._audio_manager.play_boot()
                    self._played_boot_sound = True

        elif self._state == BootState.READY:
            if self._state_timer >= self._step_delay * 1.2:
                self._state = BootState.FADING
                self._state_timer = 0.0

        elif self._state == BootState.FADING:
            if self._state_timer >= self._fade_duration:
                self._state = BootState.FINISHED

    def draw(self, surface: pygame.Surface) -> None:
        """Renders CRT boot terminal lines and fade transition."""
        if self._state == BootState.FINISHED:
            return

        bg_color = (10, 15, 26)
        text_green = (34, 197, 94)
        text_muted = (148, 163, 184)
        text_ready = (59, 130, 246)
        text_gold = (234, 179, 8)

        surface.fill(bg_color)

        font_term_title = pygame.font.SysFont("monospace", 22, bold=True)
        font_term_body = pygame.font.SysFont("monospace", 18)
        font_check = pygame.font.SysFont("sans-serif", 18, bold=True)

        start_x = 120
        y = 60

        # Header Box
        sep = "-----------------------------------"
        t1 = font_term_title.render(sep, True, text_green)
        t2 = font_term_title.render("HECTOR ARCADE OS", True, (248, 250, 252))
        t3 = font_term_body.render(f"Version {VERSION}", True, text_gold)
        t4 = font_term_title.render(sep, True, text_green)

        surface.blit(t1, (start_x, y))
        y += 24
        surface.blit(t2, (start_x, y))
        y += 24
        surface.blit(t3, (start_x, y))
        y += 24
        surface.blit(t4, (start_x, y))
        y += 45

        # Subsystem Initializations
        steps = [
            ("Initializing Audio...", self._audio_done),
            ("Loading Save Data...", self._save_done),
            ("Loading Settings...", self._settings_done),
        ]

        for label, is_done in steps:
            lbl_txt = font_term_body.render(f"{label:<26}", True, text_muted)
            surface.blit(lbl_txt, (start_x, y))

            if is_done:
                check_txt = font_check.render("✓", True, text_green)
                surface.blit(check_txt, (start_x + 310, y - 2))

            y += 28

        # Game Scan Section
        if self._settings_done or self._games_done:
            y += 10
            scan_txt = font_term_body.render("Scanning Installed Games...", True, text_muted)
            surface.blit(scan_txt, (start_x, y))
            y += 30

            games = [
                ("Snake", "Loaded", text_green),
                ("Pong", "Loaded", text_green),
                ("Tetris", "Loaded", text_green),
                ("Breakout", "Coming Soon", text_gold),
            ]

            for g_name, status, status_col in games:
                dots = "." * (25 - len(g_name))
                line_str = f"{g_name}{dots}"
                g_lbl = font_term_body.render(line_str, True, text_muted)
                s_lbl = font_term_body.render(status, True, status_col)

                surface.blit(g_lbl, (start_x, y))
                surface.blit(s_lbl, (start_x + 280, y))
                y += 24

        # Ready Line
        if self._games_done:
            y += 20
            ready_txt = font_term_title.render("Ready.", True, text_ready)
            surface.blit(ready_txt, (start_x, y))

        # Smooth Fade-out Overlay
        if self._state == BootState.FADING:
            alpha = int(255 * (self._state_timer / self._fade_duration))
            fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade_surf.fill((15, 23, 42, min(255, alpha)))
            surface.blit(fade_surf, (0, 0))
