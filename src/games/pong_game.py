"""
Pong Game implementation for Pi Arcade OS.

Implements the ArcadeGame interface to provide classic 2-player paddle gameplay,
beatable AI opponent for single-player/GPIO mode, dynamic ball physics,
rally tracking, audio feedback, LCD display integration, and SaveManager statistics.
Supports Python 3.9+ typing.
"""

import logging
import math
import random
import time
from typing import Dict, Optional, Tuple, Union
import pygame

from src.game_interface import ArcadeGame
from src.hardware.audio import AudioManager
from src.hardware.display import DisplayManager
from src.settings_manager import SettingsManager
from src.save_manager import SaveManager
from src.config import (
    Action,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    THEME_PALETTES,
    PONG_WINNING_SCORE,
    PONG_PADDLE_WIDTH,
    PONG_PADDLE_HEIGHT,
    PONG_PADDLE_SPEED,
    PONG_BALL_SIZE,
    PONG_BALL_INITIAL_SPEED,
    PONG_BALL_MAX_SPEED,
    PONG_BALL_SPEED_INC,
    PONG_AI_CONFIG,
)

logger = logging.getLogger(__name__)


class PongGame(ArcadeGame):
    """Classic Pong game implementing the ArcadeGame interface."""

    def __init__(
        self,
        audio_manager: Optional[AudioManager] = None,
        display_manager: Optional[DisplayManager] = None,
        settings_manager: Optional[SettingsManager] = None,
        save_manager: Optional[SaveManager] = None,
        use_ai: bool = False,
    ) -> None:
        self._name: str = "Pong"
        self._description: str = "Classic paddle game with local multiplayer and GPIO single-player mode."
        self._icon: str = "🏓"
        self._version: str = "1.0.0"
        self._author: str = "Hector Pacheco"
        self._is_finished: bool = False

        self._audio_manager: Optional[AudioManager] = audio_manager
        self._display_manager: Optional[DisplayManager] = display_manager
        self._settings_manager: Optional[SettingsManager] = settings_manager
        self._save_manager: SaveManager = save_manager or SaveManager()

        # Mode configuration: if use_ai is True or GPIO mode is active, P2 is AI
        self._use_ai: bool = use_ai

        # Match State
        self._p1_score: int = 0
        self._p2_score: int = 0
        self._game_over: bool = False
        self._is_paused: bool = False
        self._winner_name: str = ""

        # Rally & Stats
        self._current_rally: int = 0
        self._longest_rally: int = 0
        self._session_start_time: float = time.time()

        # Paddles (rect: x, y, w, h)
        paddle_y = (SCREEN_HEIGHT - PONG_PADDLE_HEIGHT) // 2
        self._p1_y: float = float(paddle_y)
        self._p2_y: float = float(paddle_y)

        # Paddle Movement Flags
        self._p1_up: bool = False
        self._p1_down: bool = False
        self._p2_up: bool = False
        self._p2_down: bool = False

        # Ball State
        self._ball_x: float = float((SCREEN_WIDTH - PONG_BALL_SIZE) // 2)
        self._ball_y: float = float((SCREEN_HEIGHT - PONG_BALL_SIZE) // 2)
        self._ball_vx: float = 0.0
        self._ball_vy: float = 0.0
        self._ball_speed: float = PONG_BALL_INITIAL_SPEED

        # AI State
        self._ai_timer: float = 0.0
        self._ai_target_y: float = float(paddle_y)

        # Initialize ball vector
        self.reset()
        logger.info(f"Initialized PongGame (AI Mode: {self._use_ai})")

    def set_audio_manager(self, audio_manager: Optional[AudioManager]) -> None:
        """Assigns active AudioManager instance."""
        self._audio_manager = audio_manager

    def set_display_manager(self, display_manager: Optional[DisplayManager]) -> None:
        """Assigns active DisplayManager instance."""
        self._display_manager = display_manager

    def set_settings_manager(self, settings_manager: Optional[SettingsManager]) -> None:
        """Assigns active SettingsManager instance."""
        self._settings_manager = settings_manager

    def set_save_manager(self, save_manager: SaveManager) -> None:
        """Assigns active SaveManager instance."""
        self._save_manager = save_manager

    def set_ai_mode(self, use_ai: bool) -> None:
        """Sets single-player AI mode status."""
        self._use_ai = use_ai

    def _get_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Retrieves active theme colors from SettingsManager."""
        if self._settings_manager:
            return self._settings_manager.get_theme_colors()
        return THEME_PALETTES["Slate Dark"]

    def _get_ai_config(self) -> Dict[str, Union[float, int]]:
        """Retrieves AI behavior parameters based on shared difficulty setting."""
        diff = "Normal"
        if self._settings_manager:
            diff = self._settings_manager.difficulty
        return PONG_AI_CONFIG.get(diff, PONG_AI_CONFIG["Normal"])

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def icon(self) -> str:
        return self._icon

    @property
    def version(self) -> str:
        return self._version

    @property
    def author(self) -> str:
        return self._author

    @property
    def is_finished(self) -> bool:
        return self._is_finished

    @property
    def p1_score(self) -> int:
        return self._p1_score

    @property
    def p2_score(self) -> int:
        return self._p2_score

    def start(self) -> None:
        """Initializes match session."""
        self._is_finished = False
        self._session_start_time = time.time()
        self.reset()
        if self._audio_manager:
            self._audio_manager.play_match_start()
        logger.info("Pong Match Started")

    def reset(self) -> None:
        """Resets paddles, ball, and scores for a new match."""
        self._p1_score = 0
        self._p2_score = 0
        self._game_over = False
        self._is_paused = False
        self._winner_name = ""
        self._current_rally = 0
        self._longest_rally = 0

        paddle_y = (SCREEN_HEIGHT - PONG_PADDLE_HEIGHT) // 2
        self._p1_y = float(paddle_y)
        self._p2_y = float(paddle_y)
        self._ai_target_y = float(paddle_y)

        self._reset_ball(direction=random.choice([-1, 1]))

        if self._display_manager:
            self._display_manager.show_pong_score(self._p1_score, self._p2_score)

    def _reset_ball(self, direction: int = 1) -> None:
        """Resets ball to center position with randomized launch angle."""
        self._ball_x = float((SCREEN_WIDTH - PONG_BALL_SIZE) // 2)
        self._ball_y = float((SCREEN_HEIGHT - PONG_BALL_SIZE) // 2)
        self._ball_speed = PONG_BALL_INITIAL_SPEED

        # Angle between -30deg and +30deg
        angle_deg = random.uniform(-30.0, 30.0)
        angle_rad = math.radians(angle_deg)

        self._ball_vx = direction * self._ball_speed * math.cos(angle_rad)
        self._ball_vy = self._ball_speed * math.sin(angle_rad)

    def handle_event(self, event_or_action: Union[pygame.event.Event, Action]) -> None:
        """Processes input events from Pygame or Action enums."""
        action: Optional[Action] = None

        if isinstance(event_or_action, Action):
            action = event_or_action
            # In GPIO mode, default Player 2 to AI opponent
            self._use_ai = True
        elif isinstance(event_or_action, pygame.event.Event):
            if event_or_action.type == pygame.KEYDOWN:
                key = event_or_action.key
                if key == pygame.K_w:
                    self._p1_up = True
                elif key == pygame.K_s:
                    self._p1_down = True
                elif key == pygame.K_UP:
                    if not self._use_ai:
                        self._p2_up = True
                    else:
                        action = Action.UP
                elif key == pygame.K_DOWN:
                    if not self._use_ai:
                        self._p2_down = True
                    else:
                        action = Action.DOWN
                elif key == pygame.K_p:
                    self._toggle_pause()
                    return
                elif key == pygame.K_r:
                    action = Action.RESTART
                elif key in (pygame.K_ESCAPE, pygame.K_q):
                    action = Action.BACK

            elif event_or_action.type == pygame.KEYUP:
                key = event_or_action.key
                if key == pygame.K_w:
                    self._p1_up = False
                elif key == pygame.K_s:
                    self._p1_down = False
                elif key == pygame.K_UP and not self._use_ai:
                    self._p2_up = False
                elif key == pygame.K_DOWN and not self._use_ai:
                    self._p2_down = False

        if not action:
            return

        if action == Action.BACK:
            logger.info("Pong: Return to arcade launcher menu")
            self._is_finished = True
            return

        if action == Action.RESTART:
            logger.info("Pong: Restarting match")
            self.reset()
            if self._audio_manager:
                self._audio_manager.play_match_start()
            return

        if action == Action.LEFT:  # Toggle pause in action mode
            self._toggle_pause()
            return

        # GPIO Action Mapping for P1 (Up=GPIO27, Down=GPIO22)
        if action == Action.UP:
            self._p1_y = max(0.0, self._p1_y - PONG_PADDLE_SPEED * 0.04)
        elif action == Action.DOWN:
            self._p1_y = min(float(SCREEN_HEIGHT - PONG_PADDLE_HEIGHT), self._p1_y + PONG_PADDLE_SPEED * 0.04)

    def _toggle_pause(self) -> None:
        """Toggles match pause state and updates LCD display."""
        if self._game_over:
            return
        self._is_paused = not self._is_paused
        logger.info(f"Pong Pause Toggled: {self._is_paused}")
        if self._audio_manager:
            self._audio_manager.play_pause()
        if self._display_manager:
            if self._is_paused:
                self._display_manager.show_pong_paused()
            else:
                self._display_manager.show_pong_score(self._p1_score, self._p2_score)

    def update(self, delta_time: float) -> None:
        """Updates paddle movement, ball physics, AI logic, and scoring."""
        if self._game_over or self._is_paused or self._is_finished:
            return

        # 1. Update Player 1 Keyboard Movement
        if self._p1_up:
            self._p1_y -= PONG_PADDLE_SPEED * delta_time
        if self._p1_down:
            self._p1_y += PONG_PADDLE_SPEED * delta_time
        self._p1_y = max(0.0, min(float(SCREEN_HEIGHT - PONG_PADDLE_HEIGHT), self._p1_y))

        # 2. Update Player 2 / AI Movement
        if self._use_ai:
            self._update_ai(delta_time)
        else:
            if self._p2_up:
                self._p2_y -= PONG_PADDLE_SPEED * delta_time
            if self._p2_down:
                self._p2_y += PONG_PADDLE_SPEED * delta_time
            self._p2_y = max(0.0, min(float(SCREEN_HEIGHT - PONG_PADDLE_HEIGHT), self._p2_y))

        # 3. Update Ball Position
        self._ball_x += self._ball_vx * delta_time
        self._ball_y += self._ball_vy * delta_time

        ball_rect = pygame.Rect(int(self._ball_x), int(self._ball_y), PONG_BALL_SIZE, PONG_BALL_SIZE)
        p1_rect = pygame.Rect(30, int(self._p1_y), PONG_PADDLE_WIDTH, PONG_PADDLE_HEIGHT)
        p2_rect = pygame.Rect(SCREEN_WIDTH - 30 - PONG_PADDLE_WIDTH, int(self._p2_y), PONG_PADDLE_WIDTH, PONG_PADDLE_HEIGHT)

        # 4. Top & Bottom Wall Bounce
        if self._ball_y <= 0:
            self._ball_y = 0.0
            self._ball_vy = abs(self._ball_vy)
            if self._audio_manager:
                self._audio_manager.play_wall_bounce()
            logger.debug("Pong: Wall Bounce (Top)")

        elif self._ball_y >= SCREEN_HEIGHT - PONG_BALL_SIZE:
            self._ball_y = float(SCREEN_HEIGHT - PONG_BALL_SIZE)
            self._ball_vy = -abs(self._ball_vy)
            if self._audio_manager:
                self._audio_manager.play_wall_bounce()
            logger.debug("Pong: Wall Bounce (Bottom)")

        # 5. Paddle Collision Handling
        # Left Paddle (P1)
        if self._ball_vx < 0 and ball_rect.colliderect(p1_rect):
            self._handle_paddle_bounce(p1_rect, is_left=True)

        # Right Paddle (P2 / AI)
        elif self._ball_vx > 0 and ball_rect.colliderect(p2_rect):
            self._handle_paddle_bounce(p2_rect, is_left=False)

        # 6. Goal & Scoring Check
        if self._ball_x > SCREEN_WIDTH:
            self._score_point(p1_scored=True)
        elif self._ball_x < -PONG_BALL_SIZE:
            self._score_point(p1_scored=False)

    def _handle_paddle_bounce(self, paddle_rect: pygame.Rect, is_left: bool) -> None:
        """Calculates dynamic reflection angle and speed boost on paddle hit."""
        self._current_rally += 1
        if self._current_rally > self._longest_rally:
            self._longest_rally = self._current_rally

        # Speed boost up to max limit
        self._ball_speed = min(PONG_BALL_MAX_SPEED, self._ball_speed + PONG_BALL_SPEED_INC)

        # Calculate relative impact offset (-1.0 top to +1.0 bottom)
        impact_offset = (self._ball_y + PONG_BALL_SIZE / 2.0 - paddle_rect.centery) / (PONG_PADDLE_HEIGHT / 2.0)
        impact_offset = max(-1.0, min(1.0, impact_offset))

        # Dynamic angle shift (up to 45 deg)
        max_angle_rad = math.radians(45.0)
        bounce_angle = impact_offset * max_angle_rad

        direction = 1 if is_left else -1
        self._ball_vx = direction * self._ball_speed * math.cos(bounce_angle)
        self._ball_vy = self._ball_speed * math.sin(bounce_angle)

        if is_left:
            self._ball_x = float(paddle_rect.right + 1)
        else:
            self._ball_x = float(paddle_rect.left - PONG_BALL_SIZE - 1)

        if self._audio_manager:
            self._audio_manager.play_paddle_hit()
        logger.debug(f"Pong: Paddle Hit (Rally: {self._current_rally}, Speed: {self._ball_speed:.1f})")

    def _update_ai(self, delta_time: float) -> None:
        """Updates AI opponent target position and paddle tracking."""
        ai_config = self._get_ai_config()
        self._ai_timer += delta_time

        # Update target prediction with reaction delay
        if self._ai_timer >= float(ai_config["delay"]):
            self._ai_timer = 0.0
            error = random.uniform(-float(ai_config["target_error"]), float(ai_config["target_error"]))
            self._ai_target_y = (self._ball_y + PONG_BALL_SIZE / 2.0) - (PONG_PADDLE_HEIGHT / 2.0) + error

        # Move AI paddle towards target
        diff = self._ai_target_y - self._p2_y
        speed = float(ai_config["speed"])

        if abs(diff) > 4.0:
            step = speed * delta_time
            if diff > 0:
                self._p2_y += min(diff, step)
            else:
                self._p2_y += max(diff, -step)

        self._p2_y = max(0.0, min(float(SCREEN_HEIGHT - PONG_PADDLE_HEIGHT), self._p2_y))

    def _score_point(self, p1_scored: bool) -> None:
        """Handles point scoring and checks for match winner."""
        if p1_scored:
            self._p1_score += 1
            logger.info(f"Pong: Point Scored by Player 1! (P1:{self._p1_score} - P2:{self._p2_score})")
        else:
            self._p2_score += 1
            scorer_str = "AI Opponent" if self._use_ai else "Player 2"
            logger.info(f"Pong: Point Scored by {scorer_str}! (P1:{self._p1_score} - P2:{self._p2_score})")

        self._current_rally = 0

        if self._audio_manager:
            self._audio_manager.play_point_scored()

        if self._display_manager:
            self._display_manager.show_pong_score(self._p1_score, self._p2_score)

        # Match Win Condition
        if self._p1_score >= PONG_WINNING_SCORE or self._p2_score >= PONG_WINNING_SCORE:
            self._finish_match()
        else:
            self._reset_ball(direction=-1 if p1_scored else 1)

    def _finish_match(self) -> None:
        """Handles match victory state and updates persistent save manager."""
        self._game_over = True
        duration = time.time() - self._session_start_time

        p1_won = self._p1_score >= PONG_WINNING_SCORE
        if p1_won:
            self._winner_name = "Player 1"
            if self._audio_manager:
                self._audio_manager.play_victory()
        else:
            self._winner_name = "AI Opponent" if self._use_ai else "Player 2"
            if self._audio_manager:
                self._audio_manager.play_defeat()

        logger.info(f"Pong Match Winner: {self._winner_name} (Final Score: {self._p1_score}-{self._p2_score})")

        if self._display_manager:
            self._display_manager.show_pong_game_over(self._winner_name)

        # Update SaveManager
        self._save_manager.record_pong_session(
            p1_score=self._p1_score,
            p2_score=self._p2_score,
            duration_sec=duration,
            rally_count=self._longest_rally,
        )

    def draw(self, surface: pygame.Surface) -> None:
        """Renders the Pong court, paddles, ball, score, and overlays."""
        colors = self._get_colors()
        surface.fill(colors["bg"])

        # Center Dividing Dashed Line
        dash_w = 4
        dash_h = 16
        dash_gap = 12
        line_x = SCREEN_WIDTH // 2 - dash_w // 2

        for y in range(0, SCREEN_HEIGHT, dash_h + dash_gap):
            pygame.draw.rect(surface, colors["border"], (line_x, y, dash_w, dash_h))

        # Render Header Score Text
        font_score = pygame.font.SysFont("sans-serif", 44, bold=True)
        p1_txt = font_score.render(str(self._p1_score), True, colors["accent"])
        p2_txt = font_score.render(str(self._p2_score), True, colors["text_primary"])

        surface.blit(p1_txt, (SCREEN_WIDTH // 2 - 80 - p1_txt.get_width(), 25))
        surface.blit(p2_txt, (SCREEN_WIDTH // 2 + 80, 25))

        # Mode Badge Label
        font_mode = pygame.font.SysFont("sans-serif", 16)
        mode_str = "Single-Player vs AI" if self._use_ai else "2-Player Local Keyboard"
        mode_txt = font_mode.render(mode_str, True, colors["text_muted"])
        surface.blit(mode_txt, (SCREEN_WIDTH // 2 - mode_txt.get_width() // 2, 75))

        # Render Left Paddle (P1)
        p1_rect = pygame.Rect(30, int(self._p1_y), PONG_PADDLE_WIDTH, PONG_PADDLE_HEIGHT)
        pygame.draw.rect(surface, colors["accent"], p1_rect, border_radius=4)

        # Render Right Paddle (P2 / AI)
        p2_rect = pygame.Rect(SCREEN_WIDTH - 30 - PONG_PADDLE_WIDTH, int(self._p2_y), PONG_PADDLE_WIDTH, PONG_PADDLE_HEIGHT)
        p2_color = colors["snake_head"] if self._use_ai else colors["text_primary"]
        pygame.draw.rect(surface, p2_color, p2_rect, border_radius=4)

        # Render Ball
        ball_rect = pygame.Rect(int(self._ball_x), int(self._ball_y), PONG_BALL_SIZE, PONG_BALL_SIZE)
        pygame.draw.rect(surface, colors["food"], ball_rect, border_radius=3)

        # Footer Instruction Line
        font_sub = pygame.font.SysFont("sans-serif", 16)
        help_txt = font_sub.render(
            "Controls: P1: W/S | P2: Up/Down | P: Pause | R: Restart | ESC: Menu", True, colors["text_muted"]
        )
        surface.blit(help_txt, (SCREEN_WIDTH // 2 - help_txt.get_width() // 2, SCREEN_HEIGHT - 30))

        # Pause Overlay
        if self._is_paused and not self._game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 23, 42, 200))
            surface.blit(overlay, (0, 0))

            modal_w, modal_h = 360, 160
            modal_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - modal_w // 2,
                SCREEN_HEIGHT // 2 - modal_h // 2,
                modal_w,
                modal_h,
            )
            pygame.draw.rect(surface, colors["surface"], modal_rect, border_radius=14)
            pygame.draw.rect(surface, colors["accent"], modal_rect, width=3, border_radius=14)

            font_pause = pygame.font.SysFont("sans-serif", 32, bold=True)
            p_txt = font_pause.render("MATCH PAUSED", True, colors["accent"])
            res_txt = font_sub.render("Press P / GPIO to Resume", True, colors["text_primary"])

            surface.blit(p_txt, (modal_rect.centerx - p_txt.get_width() // 2, modal_rect.top + 35))
            surface.blit(res_txt, (modal_rect.centerx - res_txt.get_width() // 2, modal_rect.top + 95))

        # Game Over Victory Overlay
        if self._game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 23, 42, 220))
            surface.blit(overlay, (0, 0))

            modal_w, modal_h = 440, 220
            modal_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - modal_w // 2,
                SCREEN_HEIGHT // 2 - modal_h // 2,
                modal_w,
                modal_h,
            )
            pygame.draw.rect(surface, colors["surface"], modal_rect, border_radius=16)
            win_color = colors["accent"] if self._winner_name == "Player 1" else (239, 68, 68)
            pygame.draw.rect(surface, win_color, modal_rect, width=3, border_radius=16)

            font_title = pygame.font.SysFont("sans-serif", 34, bold=True)
            font_body = pygame.font.SysFont("sans-serif", 20)

            win_txt = font_title.render(f"🏆 {self._winner_name} Wins!", True, win_color)
            score_summary = font_body.render(f"Final Score: {self._p1_score} - {self._p2_score}", True, colors["text_primary"])
            rally_txt = font_body.render(f"Longest Rally: {self._longest_rally} hits", True, colors["text_muted"])
            r_txt = font_sub.render("Press R / GPIO to Play Again  |  ESC for Arcade Menu", True, colors["text_primary"])

            surface.blit(win_txt, (modal_rect.centerx - win_txt.get_width() // 2, modal_rect.top + 25))
            surface.blit(score_summary, (modal_rect.centerx - score_summary.get_width() // 2, modal_rect.top + 75))
            surface.blit(rally_txt, (modal_rect.centerx - rally_txt.get_width() // 2, modal_rect.top + 110))
            surface.blit(r_txt, (modal_rect.centerx - r_txt.get_width() // 2, modal_rect.top + 160))

    def cleanup(self) -> None:
        """Clean up game session and save stats."""
        duration = time.time() - self._session_start_time
        self._save_manager.record_pong_session(
            p1_score=self._p1_score,
            p2_score=self._p2_score,
            duration_sec=duration,
            rally_count=self._longest_rally,
        )
        logger.info("PongGame resources cleaned up.")
