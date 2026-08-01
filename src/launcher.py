"""
Launcher module for Pi Arcade OS.

Manages top-level arcade state transitions (MENU, PLAYING, SHOWING_NOTICE, SHOWING_SETTINGS, SHOWING_STATS, EXITING),
animated background particles, multi-layered glowing title banners, smooth fade-in transitions,
game selection cards with hardware support badges (GPIO, LCD, Audio, Keyboard),
gameplay statistics (Snake, Pong, and Tetris), interactive Settings Subsystem,
System Statistics modal view, Achievement System popups, and Toast Notification overlay.
Supports Python 3.9+ typing.
"""

from enum import Enum
import logging
import math
import random
import sys
from typing import Optional, List, Dict, Tuple
import pygame

from src.config import (
    Action,
    SoundType,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    THEME_PALETTES,
    COLOR_BADGE_BG,
    COLOR_BADGE_TEXT,
    COLOR_BADGE_SUCCESS,
    CURSOR_PULSE_SPEED,
    PARTICLE_COUNT,
    FADE_IN_DURATION,
)
from src.version import VERSION, BUILD, AUTHOR, get_version_info
from src.save_manager import SaveManager
from src.settings_manager import SettingsManager
from src.notification_manager import NotificationManager
from src.achievement_manager import AchievementManager
from src.game_registry import GameRegistry, ComingSoonError
from src.game_interface import ArcadeGame
from src.hardware.display import DisplayManager
from src.hardware.audio import AudioManager

logger = logging.getLogger(__name__)


class LauncherState(Enum):
    """Launcher system state enumeration."""
    MENU = "MENU"
    PLAYING = "PLAYING"
    SHOWING_NOTICE = "SHOWING_NOTICE"
    SHOWING_SETTINGS = "SHOWING_SETTINGS"
    SHOWING_STATS = "SHOWING_STATS"
    EXITING = "EXITING"


class LauncherParticle:
    """Ambient background particle drifting across the screen."""

    def __init__(self) -> None:
        self.x: float = random.uniform(0, SCREEN_WIDTH)
        self.y: float = random.uniform(0, SCREEN_HEIGHT)
        self.speed_y: float = random.uniform(-18, -6)
        self.speed_x: float = random.uniform(-4, 4)
        self.radius: float = random.uniform(1.5, 3.5)
        self.alpha: int = random.randint(30, 110)

    def update(self, delta_time: float) -> None:
        """Updates particle position and wraps around screen edges."""
        self.x += self.speed_x * delta_time
        self.y += self.speed_y * delta_time

        if self.y < -10:
            self.y = SCREEN_HEIGHT + 10
            self.x = random.uniform(0, SCREEN_WIDTH)
        if self.x < -10:
            self.x = SCREEN_WIDTH + 10
        elif self.x > SCREEN_WIDTH + 10:
            self.x = -10

    def draw(self, surface: pygame.Surface, accent_color: Tuple[int, int, int]) -> None:
        """Renders particle with alpha transparency in dynamic accent color."""
        p_surf = pygame.Surface((int(self.radius * 2), int(self.radius * 2)), pygame.SRCALPHA)
        r, g, b = accent_color
        pygame.draw.circle(p_surf, (r, g, b, self.alpha), (int(self.radius), int(self.radius)), int(self.radius))
        surface.blit(p_surf, (self.x - self.radius, self.y - self.radius))


class Launcher:
    """Main Arcade OS launcher controller."""

    SETTINGS_ITEMS: List[str] = [
        "Master Volume",
        "Music Volume",
        "Effects Volume",
        "LCD Brightness",
        "Theme",
        "Difficulty",
        "Controls",
        "Reset High Scores",
        "Restore Defaults",
    ]

    def __init__(
        self,
        registry: GameRegistry,
        display_manager: Optional[DisplayManager] = None,
        audio_manager: Optional[AudioManager] = None,
        settings_manager: Optional[SettingsManager] = None,
        save_manager: Optional[SaveManager] = None,
        notification_manager: Optional[NotificationManager] = None,
        achievement_manager: Optional[AchievementManager] = None,
    ) -> None:
        """
        Initializes Launcher with registered games, hardware services, and OS features.
        """
        self._registry: GameRegistry = registry
        self._display_manager: Optional[DisplayManager] = display_manager
        self._audio_manager: Optional[AudioManager] = audio_manager
        self._save_manager: SaveManager = save_manager or SaveManager()
        self._settings_manager: SettingsManager = settings_manager or SettingsManager(save_manager=self._save_manager)

        self._notification_manager: NotificationManager = notification_manager or NotificationManager()
        self._achievement_manager: AchievementManager = achievement_manager or AchievementManager(
            save_manager=self._save_manager,
            notification_manager=self._notification_manager,
            audio_manager=self._audio_manager,
        )

        self._state: LauncherState = LauncherState.MENU
        self._selected_index: int = 0
        self._settings_selected_index: int = 0
        self._active_game: Optional[ArcadeGame] = None

        # Animation state
        self._cursor_timer: float = 0.0
        self._fade_timer: float = 0.0
        self._particles: List[LauncherParticle] = [LauncherParticle() for _ in range(PARTICLE_COUNT)]

        self._notice_message: str = ""
        self._notice_title: str = ""
        self._settings_toast: str = ""

        # Trigger startup jingle audio effect
        if self._audio_manager:
            self._audio_manager.play_startup_jingle()

        self._update_lcd_menu()

    @property
    def state(self) -> LauncherState:
        """Returns the current launcher state."""
        return self._state

    @property
    def active_game(self) -> Optional[ArcadeGame]:
        """Returns the currently running ArcadeGame instance, if any."""
        return self._active_game

    @property
    def selected_index(self) -> int:
        """Returns the current menu selection index."""
        return self._selected_index

    @property
    def notification_manager(self) -> NotificationManager:
        """Returns the active NotificationManager instance."""
        return self._notification_manager

    @property
    def achievement_manager(self) -> AchievementManager:
        """Returns the active AchievementManager instance."""
        return self._achievement_manager

    def _get_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Returns active theme colors."""
        return self._settings_manager.get_theme_colors()

    def open_settings_view(self) -> None:
        """Opens the System Settings & Diagnostics view modal."""
        self._state = LauncherState.SHOWING_SETTINGS
        self._settings_selected_index = 0
        if self._audio_manager:
            self._audio_manager.play_menu_move()

    def open_stats_view(self) -> None:
        """Opens the System Statistics & Version metadata view modal."""
        self._state = LauncherState.SHOWING_STATS
        if self._audio_manager:
            self._audio_manager.play_stats_open()

    def _get_games_list(self) -> List[Dict[str, object]]:
        """Helper to get list of registered game metadata."""
        return self._registry.list_games()

    def _update_lcd_menu(self) -> None:
        """Updates physical LCD with currently selected menu game."""
        games = self._get_games_list()
        if self._display_manager and games:
            selected_game = games[self._selected_index]
            name = str(selected_game["name"])
            if selected_game.get("is_coming_soon"):
                name = f"(Soon) {name}"
            self._display_manager.show_launcher_menu(name)

    def handle_action(self, action: Action) -> None:
        """
        Processes a normalized Action event based on current launcher state.
        """
        if self._state == LauncherState.SHOWING_NOTICE:
            self._state = LauncherState.MENU
            if self._audio_manager:
                self._audio_manager.play_menu_move()
            return

        if self._state == LauncherState.SHOWING_SETTINGS:
            self._handle_settings_action(action)
            return

        if self._state == LauncherState.SHOWING_STATS:
            if action in (Action.BACK, Action.QUIT, Action.SELECT, Action.LEFT):
                self._state = LauncherState.MENU
                if self._audio_manager:
                    self._audio_manager.play_menu_back()
            return

        if self._state == LauncherState.MENU:
            self._handle_menu_action(action)
        elif self._state == LauncherState.PLAYING and self._active_game:
            self._active_game.handle_event(action)

    def handle_pygame_event(self, event: pygame.event.Event) -> None:
        """
        Processes raw Pygame events.
        """
        if event.type == pygame.QUIT:
            self._state = LauncherState.EXITING
            return

        if self._state == LauncherState.SHOWING_NOTICE and event.type == pygame.KEYDOWN:
            self._state = LauncherState.MENU
            if self._audio_manager:
                self._audio_manager.play_menu_move()
            return

        if self._state == LauncherState.SHOWING_SETTINGS and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                self._state = LauncherState.MENU
                if self._audio_manager:
                    self._audio_manager.play_menu_back()
                return

        if self._state == LauncherState.SHOWING_STATS and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q, pygame.K_RETURN, pygame.K_SPACE):
                self._state = LauncherState.MENU
                if self._audio_manager:
                    self._audio_manager.play_menu_back()
                return

        if self._state == LauncherState.MENU and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                self.open_stats_view()
                return

        if self._state == LauncherState.PLAYING and self._active_game:
            self._active_game.handle_event(event)

    def _handle_menu_action(self, action: Action) -> None:
        """Handles menu navigation and game launch actions."""
        games = self._get_games_list()
        if not games:
            if action in (Action.BACK, Action.QUIT):
                self._state = LauncherState.EXITING
            return

        num_games = len(games)

        if action == Action.UP:
            self._selected_index = (self._selected_index - 1) % num_games
            if self._audio_manager:
                self._audio_manager.play_menu_move()
            self._update_lcd_menu()

        elif action == Action.DOWN:
            self._selected_index = (self._selected_index + 1) % num_games
            if self._audio_manager:
                self._audio_manager.play_menu_move()
            self._update_lcd_menu()

        elif action in (Action.SELECT, Action.RIGHT):
            self.launch_selected_game()

        elif action in (Action.BACK, Action.LEFT, Action.QUIT):
            self._state = LauncherState.EXITING

    def _handle_settings_action(self, action: Action) -> None:
        """Handles navigation and adjustment inside interactive Settings menu."""
        num_items = len(self.SETTINGS_ITEMS)

        if action == Action.UP:
            self._settings_selected_index = (self._settings_selected_index - 1) % num_items
            if self._audio_manager:
                self._audio_manager.play_menu_move()

        elif action == Action.DOWN:
            self._settings_selected_index = (self._settings_selected_index + 1) % num_items
            if self._audio_manager:
                self._audio_manager.play_menu_move()

        elif action in (Action.LEFT, Action.RIGHT, Action.SELECT):
            step = 1 if action in (Action.RIGHT, Action.SELECT) else -1
            idx = self._settings_selected_index

            if idx == 0:
                self._settings_manager.master_volume = max(0.0, min(1.0, self._settings_manager.master_volume + step * 0.05))
                self._settings_manager.save()
                self._notification_manager.notify(
                    "Volume Adjusted",
                    f"Master Volume: {int(self._settings_manager.master_volume * 100)}%",
                    icon="🔊",
                    color=(59, 130, 246),
                )
            elif idx == 1:
                self._settings_manager.music_volume = max(0.0, min(1.0, self._settings_manager.music_volume + step * 0.05))
                self._settings_manager.save()
            elif idx == 2:
                self._settings_manager.effects_volume = max(0.0, min(1.0, self._settings_manager.effects_volume + step * 0.05))
                self._settings_manager.save()
            elif idx == 3:
                self._settings_manager.lcd_brightness = max(0.0, min(1.0, self._settings_manager.lcd_brightness + step * 0.05))
                self._settings_manager.save()
            elif idx == 4:
                self._settings_manager.cycle_theme(step)
                self._notification_manager.notify(
                    "Theme Applied",
                    f"Active Theme: {self._settings_manager.theme}",
                    icon="🎨",
                    color=(168, 85, 247),
                )
            elif idx == 5:
                self._settings_manager.cycle_difficulty(step)
            elif idx == 6:
                self._settings_manager.cycle_controls(step)
            elif idx == 7:
                self._settings_manager.reset_high_scores()
                self._settings_toast = "High Scores Cleared!"
                self._notification_manager.notify(
                    "Stats Cleared",
                    "All game high scores reset to 0.",
                    icon="🧹",
                    color=(239, 68, 68),
                )
            elif idx == 8:
                self._settings_manager.restore_defaults()
                self._settings_toast = "Defaults Restored!"
                self._notification_manager.notify(
                    "Defaults Restored",
                    "All system settings restored to default.",
                    icon="⚙️",
                    color=(34, 197, 94),
                )

            if self._audio_manager:
                self._audio_manager.play_settings_save()

        elif action in (Action.BACK, Action.QUIT):
            self._state = LauncherState.MENU
            if self._audio_manager:
                self._audio_manager.play_menu_back()

    def launch_selected_game(self) -> None:
        """Launches the game currently highlighted in the menu."""
        games = self._get_games_list()
        if not games or self._selected_index >= len(games):
            return

        game_data = games[self._selected_index]
        game_id = str(game_data["id"])
        game_name = str(game_data["name"])

        if game_data.get("is_coming_soon"):
            logger.info(f"Selected coming-soon game preview '{game_id}'. Displaying preview notice.")
            if self._audio_manager:
                self._audio_manager.play_error()
            self._notice_title = game_name
            est = game_data.get("estimated_release", "Sprint 6")
            self._notice_message = f"{game_name} is currently under active development! (Est. Release: {est})"
            self._state = LauncherState.SHOWING_NOTICE
            return

        logger.info(f"Launching game ID '{game_id}'")
        if self._audio_manager:
            self._audio_manager.play_menu_select()

        # Record game start in SaveManager and check achievements
        self._save_manager.record_game_start(game_id)
        self._achievement_manager.check_achievements("game_start", {"game_id": game_id})

        try:
            self._active_game = self._registry.create_instance(game_id)
            if hasattr(self._active_game, "set_audio_manager"):
                getattr(self._active_game, "set_audio_manager")(self._audio_manager)
            if hasattr(self._active_game, "set_display_manager"):
                getattr(self._active_game, "set_display_manager")(self._display_manager)
            if hasattr(self._active_game, "set_settings_manager"):
                getattr(self._active_game, "set_settings_manager")(self._settings_manager)
            if hasattr(self._active_game, "set_save_manager"):
                getattr(self._active_game, "set_save_manager")(self._save_manager)

            self._active_game.start()
            self._state = LauncherState.PLAYING
        except ComingSoonError as e:
            logger.warning(f"Could not launch game: {e}")
            if self._audio_manager:
                self._audio_manager.play_error()
            self._notice_title = game_name
            self._notice_message = str(e)
            self._state = LauncherState.SHOWING_NOTICE

    def update(self, delta_time: float) -> None:
        """Updates animation timers, notifications, particles, and active game state."""
        self._cursor_timer += delta_time
        if self._fade_timer < FADE_IN_DURATION:
            self._fade_timer += delta_time

        self._notification_manager.update(delta_time)

        for particle in self._particles:
            particle.update(delta_time)

        if self._state == LauncherState.PLAYING and self._active_game:
            self._active_game.update(delta_time)

            if self._active_game.is_finished:
                logger.info(f"Game '{self._active_game.name}' finished. Returning to menu.")
                self._active_game.cleanup()
                self._active_game = None
                self._state = LauncherState.MENU
                self._update_lcd_menu()
                # Check achievements after game session ends
                self._achievement_manager.check_achievements("game_end")

    def draw(self, surface: pygame.Surface) -> None:
        """Renders launcher menu, background particles, glowing title, game cards, and overlays."""
        colors = self._get_colors()

        if self._state == LauncherState.PLAYING and self._active_game:
            self._active_game.draw(surface)
            self._notification_manager.draw(surface)
            return

        surface.fill(colors["bg"])
        for particle in self._particles:
            particle.draw(surface, colors["accent"])

        font_header_deco = pygame.font.SysFont("monospace", 20, bold=True)
        font_title = pygame.font.SysFont("sans-serif", 38, bold=True)
        font_item = pygame.font.SysFont("sans-serif", 24, bold=True)
        font_desc = pygame.font.SysFont("sans-serif", 16)
        font_badge = pygame.font.SysFont("sans-serif", 13, bold=True)
        font_footer = pygame.font.SysFont("sans-serif", 18, bold=True)

        glow_pulse = (math.sin(self._cursor_timer * 3.0) + 1.0) * 0.5
        glow_offset = 2 + int(glow_pulse * 3)

        title_str = "Hector Arcade OS"

        glow_txt = font_title.render(title_str, True, colors["accent"])
        surface.blit(glow_txt, (SCREEN_WIDTH // 2 - glow_txt.get_width() // 2 - glow_offset, 32))
        surface.blit(glow_txt, (SCREEN_WIDTH // 2 - glow_txt.get_width() // 2 + glow_offset, 32))

        title_txt = font_title.render(title_str, True, colors["text_primary"])
        deco_bar = font_header_deco.render("==========================================", True, colors["border"])

        surface.blit(deco_bar, (SCREEN_WIDTH // 2 - deco_bar.get_width() // 2, 10))
        surface.blit(title_txt, (SCREEN_WIDTH // 2 - title_txt.get_width() // 2, 32))
        surface.blit(deco_bar, (SCREEN_WIDTH // 2 - deco_bar.get_width() // 2, 75))

        # Profile Badge Header
        player_lbl = font_desc.render(f"Player: {self._save_manager.player_name}", True, colors["accent"])
        ver_lbl = font_desc.render(f"v{VERSION}", True, colors["text_muted"])
        surface.blit(player_lbl, (25, 42))
        surface.blit(ver_lbl, (SCREEN_WIDTH - ver_lbl.get_width() - 25, 42))

        games = self._get_games_list()
        if not games:
            no_games_txt = font_item.render("No Games Registered", True, colors["text_muted"])
            surface.blit(no_games_txt, (SCREEN_WIDTH // 2 - no_games_txt.get_width() // 2, 250))
            return

        cursor_pulse_offset = int(math.sin(self._cursor_timer * CURSOR_PULSE_SPEED) * 5)

        card_w = 620
        start_y = 105

        for idx, game in enumerate(games):
            is_selected = (idx == self._selected_index)
            is_coming_soon = bool(game.get("is_coming_soon", False))

            card_h = 105 if is_selected else 70
            y_pos = start_y + idx * (75) + (35 if idx > self._selected_index else 0)

            card_rect = pygame.Rect(SCREEN_WIDTH // 2 - card_w // 2, y_pos, card_w, card_h)

            bg_col = colors["surface_selected"] if is_selected else colors["surface"]
            border_col = colors["accent"] if is_selected else colors["border"]

            pygame.draw.rect(surface, bg_col, card_rect, border_radius=12)
            pygame.draw.rect(surface, border_col, card_rect, width=2 if is_selected else 1, border_radius=12)

            cursor_str = "> " if is_selected else "  "
            cursor_x_pos = card_rect.left + 15 + (cursor_pulse_offset if is_selected else 0)

            icon = str(game.get("icon", "🎮"))
            game_name = str(game["name"])
            version = str(game.get("version", "v1.0.0"))
            author = str(game.get("author", "Hector Pacheco"))

            if is_coming_soon:
                display_title = f"{icon} {game_name}  (Coming Soon)"
                name_col = (251, 146, 60) if is_selected else colors["text_muted"]
            else:
                display_title = f"{icon} {game_name}  ({version})"
                name_col = colors["accent"] if is_selected else colors["text_primary"]

            name_txt = font_item.render(f"{cursor_str}{display_title}", True, name_col)
            author_txt = font_desc.render(f"by {author}", True, colors["text_muted"])
            desc_txt = font_desc.render(str(game["description"]), True, colors["text_muted"])

            surface.blit(name_txt, (cursor_x_pos, card_rect.top + 8))
            surface.blit(author_txt, (card_rect.left + card_w - author_txt.get_width() - 20, card_rect.top + 12))
            surface.blit(desc_txt, (card_rect.left + 42, card_rect.top + 36))

            if is_selected:
                if not is_coming_soon and game["id"] == "snake":
                    high_score = self._save_manager.get_high_score("snake")
                    played = self._save_manager.get_games_played("snake")
                    best_t = self._save_manager.get_best_time("snake")
                    stats_str = f"📊 High Score: {high_score}  |  Games Played: {played}  |  Best Time: {best_t:.1f}s"
                    stats_txt = font_desc.render(stats_str, True, colors["snake_head"])
                    surface.blit(stats_txt, (card_rect.left + 42, card_rect.top + 58))

                elif not is_coming_soon and game["id"] == "pong":
                    played = self._save_manager.get_games_played("pong")
                    wins = self._save_manager.get_wins("pong")
                    losses = self._save_manager.get_losses("pong")
                    stats_str = f"📊 Games Played: {played}  |  Wins: {wins}  |  Losses: {losses}"
                    stats_txt = font_desc.render(stats_str, True, colors["accent"])
                    surface.blit(stats_txt, (card_rect.left + 42, card_rect.top + 58))

                elif not is_coming_soon and game["id"] == "tetris":
                    high_score = self._save_manager.get_high_score("tetris")
                    played = self._save_manager.get_games_played("tetris")
                    lvl = self._save_manager.get_highest_level("tetris")
                    lines = self._save_manager.get_total_lines("tetris")
                    tetrises = self._save_manager.get_tetrises("tetris")
                    stats_str = f"📊 High Score: {high_score}  |  Played: {played}  |  Lv: {lvl}  |  Lines: {lines}  |  Tetrises: {tetrises}"
                    stats_txt = font_desc.render(stats_str, True, (6, 182, 212))
                    surface.blit(stats_txt, (card_rect.left + 42, card_rect.top + 58))

                elif is_coming_soon:
                    est_rel = str(game.get("estimated_release", "Sprint 6"))
                    est_txt = font_desc.render(f"⏳ Estimated Target: {est_rel}", True, (251, 146, 60))
                    surface.blit(est_txt, (card_rect.left + 42, card_rect.top + 58))

                badge_x = card_rect.left + 42
                badge_y = card_rect.top + (80 if not is_coming_soon or is_coming_soon else 60)

                badges = ["✓ GPIO", "✓ LCD", "✓ Audio", "✓ Keyboard"]
                for badge_text in badges:
                    badge_lbl = font_badge.render(badge_text, True, colors["accent"])
                    b_w = badge_lbl.get_width() + 10
                    b_h = 18
                    b_rect = pygame.Rect(badge_x, badge_y, b_w, b_h)

                    pygame.draw.rect(surface, colors["bg"], b_rect, border_radius=4)
                    pygame.draw.rect(surface, colors["border"], b_rect, width=1, border_radius=4)
                    surface.blit(badge_lbl, (badge_x + 5, badge_y + 2))

                    badge_x += b_w + 8

        # Footer Instruction Bar
        footer_txt = font_footer.render(
            "Enter = Launch   |   ESC = Exit   |   S = Settings   |   T = Stats", True, colors["text_primary"]
        )
        nav_sub = font_desc.render("Controls: ↑ ↓ / W S / GPIO 27 & 22", True, colors["text_muted"])

        surface.blit(footer_txt, (SCREEN_WIDTH // 2 - footer_txt.get_width() // 2, SCREEN_HEIGHT - 45))
        surface.blit(nav_sub, (SCREEN_WIDTH // 2 - nav_sub.get_width() // 2, SCREEN_HEIGHT - 22))

        # Smooth Startup Fade-In Overlay
        if self._fade_timer < FADE_IN_DURATION:
            fade_alpha = int(255 * (1.0 - (self._fade_timer / FADE_IN_DURATION)))
            fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surf.fill(colors["bg"])
            fade_surf.set_alpha(fade_alpha)
            surface.blit(fade_surf, (0, 0))

        # Modal Overlays
        if self._state == LauncherState.SHOWING_NOTICE:
            self._draw_notice_modal(surface, colors)
        elif self._state == LauncherState.SHOWING_SETTINGS:
            self._draw_settings_modal(surface, colors)
        elif self._state == LauncherState.SHOWING_STATS:
            self._draw_stats_modal(surface, colors)

        # Always render active toast notifications on top
        self._notification_manager.draw(surface)

    def _draw_notice_modal(self, surface: pygame.Surface, colors: Dict[str, Tuple[int, int, int]]) -> None:
        """Renders coming-soon notice modal overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 220))
        surface.blit(overlay, (0, 0))

        modal_w, modal_h = 480, 200
        modal_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - modal_w // 2,
            SCREEN_HEIGHT // 2 - modal_h // 2,
            modal_w,
            modal_h,
        )
        pygame.draw.rect(surface, colors["surface"], modal_rect, border_radius=14)
        pygame.draw.rect(surface, (251, 146, 60), modal_rect, width=3, border_radius=14)

        font_notice_title = pygame.font.SysFont("sans-serif", 30, bold=True)
        font_notice_body = pygame.font.SysFont("sans-serif", 20)
        font_muted = pygame.font.SysFont("sans-serif", 16)

        t_txt = font_notice_title.render(f"🎮 {self._notice_title}", True, (251, 146, 60))
        b_txt = font_notice_body.render(self._notice_message, True, colors["text_primary"])
        dismiss_txt = font_muted.render("Press Enter / ESC / Any Key to Return", True, colors["text_muted"])

        surface.blit(t_txt, (modal_rect.centerx - t_txt.get_width() // 2, modal_rect.top + 30))
        surface.blit(b_txt, (modal_rect.centerx - b_txt.get_width() // 2, modal_rect.top + 85))
        surface.blit(dismiss_txt, (modal_rect.centerx - dismiss_txt.get_width() // 2, modal_rect.top + 140))

    def _draw_settings_modal(self, surface: pygame.Surface, colors: Dict[str, Tuple[int, int, int]]) -> None:
        """Renders interactive System Settings menu modal overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 230))
        surface.blit(overlay, (0, 0))

        modal_w, modal_h = 600, 440
        modal_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - modal_w // 2,
            SCREEN_HEIGHT // 2 - modal_h // 2,
            modal_w,
            modal_h,
        )
        pygame.draw.rect(surface, colors["surface"], modal_rect, border_radius=16)
        pygame.draw.rect(surface, colors["accent"], modal_rect, width=3, border_radius=16)

        font_title = pygame.font.SysFont("sans-serif", 28, bold=True)
        font_row = pygame.font.SysFont("sans-serif", 20, bold=True)
        font_val = pygame.font.SysFont("sans-serif", 20)
        font_sub = pygame.font.SysFont("sans-serif", 16)

        t_txt = font_title.render("⚙️ System Settings", True, colors["accent"])
        surface.blit(t_txt, (modal_rect.centerx - t_txt.get_width() // 2, modal_rect.top + 18))

        start_y = modal_rect.top + 60
        row_height = 36

        for idx, item in enumerate(self.SETTINGS_ITEMS):
            is_selected = (idx == self._settings_selected_index)
            r_y = start_y + idx * row_height

            r_rect = pygame.Rect(modal_rect.left + 20, r_y, modal_w - 40, row_height - 4)
            if is_selected:
                pygame.draw.rect(surface, colors["surface_selected"], r_rect, border_radius=6)
                pygame.draw.rect(surface, colors["accent"], r_rect, width=2, border_radius=6)

            prefix = "► " if is_selected else "  "
            label_col = colors["accent"] if is_selected else colors["text_primary"]
            label_txt = font_row.render(f"{prefix}{item}", True, label_col)
            surface.blit(label_txt, (r_rect.left + 10, r_rect.top + 6))

            val_str = ""
            if idx == 0:
                val_str = f"[{'█' * int(self._settings_manager.master_volume * 10)}{'░' * (10 - int(self._settings_manager.master_volume * 10))}] {int(self._settings_manager.master_volume * 100)}%"
            elif idx == 1:
                val_str = f"[{'█' * int(self._settings_manager.music_volume * 10)}{'░' * (10 - int(self._settings_manager.music_volume * 10))}] {int(self._settings_manager.music_volume * 100)}%"
            elif idx == 2:
                val_str = f"[{'█' * int(self._settings_manager.effects_volume * 10)}{'░' * (10 - int(self._settings_manager.effects_volume * 10))}] {int(self._settings_manager.effects_volume * 100)}%"
            elif idx == 3:
                val_str = f"[{'█' * int(self._settings_manager.lcd_brightness * 10)}{'░' * (10 - int(self._settings_manager.lcd_brightness * 10))}] {int(self._settings_manager.lcd_brightness * 100)}%"
            elif idx == 4:
                val_str = f"◄ {self._settings_manager.theme} ►"
            elif idx == 5:
                val_str = f"◄ {self._settings_manager.difficulty} ►"
            elif idx == 6:
                val_str = f"◄ {self._settings_manager.controls} ►"
            elif idx == 7:
                val_str = "Press SELECT to Clear"
            elif idx == 8:
                val_str = "Press SELECT to Reset"

            val_txt = font_val.render(val_str, True, colors["accent"] if is_selected else colors["text_muted"])
            surface.blit(val_txt, (r_rect.right - val_txt.get_width() - 15, r_rect.top + 6))

        footer_str = "Use ↑ ↓ / Left Right to Adjust  |  ESC to Close"
        if self._settings_toast:
            footer_str = self._settings_toast
        dismiss_txt = font_sub.render(footer_str, True, colors["text_muted"])
        surface.blit(dismiss_txt, (modal_rect.centerx - dismiss_txt.get_width() // 2, modal_rect.bottom - 26))

    def _draw_stats_modal(self, surface: pygame.Surface, colors: Dict[str, Tuple[int, int, int]]) -> None:
        """Renders System Statistics & Version Metadata overlay modal."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 235))
        surface.blit(overlay, (0, 0))

        modal_w, modal_h = 680, 490
        modal_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - modal_w // 2,
            SCREEN_HEIGHT // 2 - modal_h // 2,
            modal_w,
            modal_h,
        )
        pygame.draw.rect(surface, colors["surface"], modal_rect, border_radius=16)
        pygame.draw.rect(surface, (59, 130, 246), modal_rect, width=3, border_radius=16)

        font_title = pygame.font.SysFont("sans-serif", 28, bold=True)
        font_section = pygame.font.SysFont("sans-serif", 18, bold=True)
        font_label = pygame.font.SysFont("sans-serif", 15)
        font_val = pygame.font.SysFont("sans-serif", 15, bold=True)
        font_sub = pygame.font.SysFont("sans-serif", 15)

        t_txt = font_title.render("📊 System & Gameplay Statistics", True, (59, 130, 246))
        surface.blit(t_txt, (modal_rect.centerx - t_txt.get_width() // 2, modal_rect.top + 18))

        # Column 1: Gameplay Stats
        col1_x = modal_rect.left + 30
        y1 = modal_rect.top + 65

        sec1 = font_section.render("🎮 Gameplay Metrics", True, colors["accent"])
        surface.blit(sec1, (col1_x, y1))
        y1 += 28

        total_time = self._save_manager.total_play_time
        time_str = f"{int(total_time // 3600)}h {int((total_time % 3600) // 60)}m {int(total_time % 60)}s" if total_time >= 60 else f"{total_time:.1f}s"

        stats1 = [
            ("Total Play Time:", time_str),
            ("Games Played:", str(self._save_manager.get_total_games_played())),
            ("Favorite Game:", self._save_manager.get_favorite_game()),
            ("Avg Session Length:", f"{self._save_manager.get_average_session_length():.1f}s"),
            ("Snake High Score:", str(self._save_manager.get_high_score("snake"))),
            ("Longest Snake Time:", f"{self._save_manager.get_best_time('snake'):.1f}s"),
            ("Pong Wins / Losses:", f"{self._save_manager.get_wins('pong')} W / {self._save_manager.get_losses('pong')} L"),
            ("Tetris High Score:", str(self._save_manager.get_high_score("tetris"))),
            ("Tetris Lines Cleared:", str(self._save_manager.get_total_lines("tetris"))),
        ]

        for lbl, val in stats1:
            l_txt = font_label.render(lbl, True, colors["text_primary"])
            v_txt = font_val.render(val, True, colors["accent"])
            surface.blit(l_txt, (col1_x, y1))
            surface.blit(v_txt, (col1_x + 180, y1))
            y1 += 25

        # Column 2: System Metadata & Achievements
        col2_x = modal_rect.left + 360
        y2 = modal_rect.top + 65

        sec2 = font_section.render("💻 System & Versions", True, colors["accent"])
        surface.blit(sec2, (col2_x, y2))
        y2 += 28

        stats2 = [
            ("OS Version:", f"v{VERSION}"),
            ("Build Target:", BUILD),
            ("Python Version:", sys.version.split()[0]),
            ("Pygame Version:", pygame.__version__),
            ("Save File Version:", "1.0.0"),
            ("Author:", AUTHOR),
        ]

        for lbl, val in stats2:
            l_txt = font_label.render(lbl, True, colors["text_primary"])
            v_txt = font_val.render(val, True, colors["text_muted"])
            surface.blit(l_txt, (col2_x, y2))
            surface.blit(v_txt, (col2_x + 145, y2))
            y2 += 25

        y2 += 10
        sec3 = font_section.render("🏆 Unlocked Achievements", True, (234, 179, 8))
        surface.blit(sec3, (col2_x, y2))
        y2 += 28

        achievements = self._achievement_manager.get_all_achievements()
        unlocked_count = sum(1 for a in achievements if a["unlocked"])
        summary_txt = font_val.render(f"{unlocked_count} / {len(achievements)} Unlocked", True, (234, 179, 8))
        surface.blit(summary_txt, (col2_x, y2))
        y2 += 24

        for ach in achievements[:4]:  # Show top 4 in compact column
            status_symbol = "✓" if ach["unlocked"] else "🔒"
            a_col = (34, 197, 94) if ach["unlocked"] else colors["text_muted"]
            a_txt = font_label.render(f"{status_symbol} {ach['icon']} {ach['title']}", True, a_col)
            surface.blit(a_txt, (col2_x, y2))
            y2 += 22

        dismiss_txt = font_sub.render("Press ESC / Enter / BACK to Return", True, colors["text_muted"])
        surface.blit(dismiss_txt, (modal_rect.centerx - dismiss_txt.get_width() // 2, modal_rect.bottom - 26))

    def cleanup(self) -> None:
        """Cleans up active game instance if running."""
        if self._active_game:
            self._active_game.cleanup()
            self._active_game = None
        self._state = LauncherState.EXITING
