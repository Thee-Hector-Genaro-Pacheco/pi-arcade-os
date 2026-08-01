"""
Snake Game implementation for Pi Arcade OS.

Implements the ArcadeGame interface to provide classic Snake gameplay,
score/high-score tracking, games played stats, wall & self-collision detection,
audio feedback integration, dynamic theme rendering, and SaveManager integration.
Supports Python 3.9+ typing.
"""

import os
import random
import logging
import time
from typing import List, Tuple, Union, Optional, Dict
import pygame

from src.game_interface import ArcadeGame
from src.hardware.audio import AudioManager
from src.settings_manager import SettingsManager
from src.save_manager import SaveManager
from src.config import (
    Action,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    THEME_PALETTES,
    GRID_CELL_SIZE,
    GRID_COLS,
    GRID_ROWS,
    HIGH_SCORE_FILE,
    SNAKE_STATS_FILE,
)

logger = logging.getLogger(__name__)


class SnakeGame(ArcadeGame):
    """Classic Snake game implementing the ArcadeGame interface."""

    def __init__(
        self,
        audio_manager: Optional[AudioManager] = None,
        settings_manager: Optional[SettingsManager] = None,
        save_manager: Optional[SaveManager] = None,
    ) -> None:
        self._name: str = "Snake"
        self._description: str = "Classic arcade snake game. Eat food, grow, and avoid walls!"
        self._icon: str = "🐍"
        self._version: str = "1.3.0"
        self._author: str = "Hector Pacheco"
        self._is_finished: bool = False

        self._audio_manager: Optional[AudioManager] = audio_manager
        self._settings_manager: Optional[SettingsManager] = settings_manager
        self._save_manager: SaveManager = save_manager or SaveManager()

        # Grid offsets for centering the playfield on screen
        self._playfield_width = GRID_COLS * GRID_CELL_SIZE
        self._playfield_height = GRID_ROWS * GRID_CELL_SIZE
        self._offset_x = (SCREEN_WIDTH - self._playfield_width) // 2
        self._offset_y = (SCREEN_HEIGHT - self._playfield_height) // 2 + 20

        # Stats variables
        self._high_score: int = self._save_manager.get_high_score("snake")
        self._games_played: int = self._save_manager.get_games_played("snake")
        self._best_time: float = self._save_manager.get_best_time("snake")

        # Game round variables
        self._score: int = 0
        self._game_over: bool = False
        self._move_timer: float = 0.0
        self._move_interval: float = self._get_speed_from_difficulty()
        self._session_start_time: float = time.time()
        self._current_survival_time: float = 0.0

        # Snake state: represented as list of grid coordinates (col, row)
        self._snake: List[Tuple[int, int]] = []
        self._direction: Tuple[int, int] = (1, 0)  # Initial direction: RIGHT
        self._next_direction: Tuple[int, int] = (1, 0)
        self._food: Tuple[int, int] = (0, 0)

        # Initialize snake and food
        self.reset()

    def set_audio_manager(self, audio_manager: Optional[AudioManager]) -> None:
        """Assigns active AudioManager instance to game."""
        self._audio_manager = audio_manager

    def set_settings_manager(self, settings_manager: Optional[SettingsManager]) -> None:
        """Assigns active SettingsManager instance to game."""
        self._settings_manager = settings_manager
        self._move_interval = self._get_speed_from_difficulty()

    def set_save_manager(self, save_manager: SaveManager) -> None:
        """Assigns active SaveManager instance to game."""
        self._save_manager = save_manager
        self._high_score = self._save_manager.get_high_score("snake")
        self._games_played = self._save_manager.get_games_played("snake")
        self._best_time = self._save_manager.get_best_time("snake")

    def _get_speed_from_difficulty(self) -> float:
        """Calculates initial step interval based on active settings difficulty."""
        if self._settings_manager:
            diff = self._settings_manager.difficulty
            if diff == "Easy":
                return 0.16
            elif diff == "Hard":
                return 0.08
        return 0.12  # Normal default

    def _get_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Retrieves active theme colors from SettingsManager."""
        if self._settings_manager:
            return self._settings_manager.get_theme_colors()
        return THEME_PALETTES["Slate Dark"]

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
    def score(self) -> int:
        return self._score

    @property
    def high_score(self) -> int:
        return self._save_manager.get_high_score("snake")

    @property
    def games_played(self) -> int:
        return self._save_manager.get_games_played("snake")

    @property
    def best_time(self) -> float:
        return self._save_manager.get_best_time("snake")

    def start(self) -> None:
        """Initializes game session."""
        self._is_finished = False
        self.reset()

    def reset(self) -> None:
        """Resets the game state for a new round."""
        self._score = 0
        self._game_over = False
        self._move_timer = 0.0
        self._move_interval = self._get_speed_from_difficulty()
        self._direction = (1, 0)
        self._next_direction = (1, 0)
        self._session_start_time = time.time()
        self._current_survival_time = 0.0

        # Center snake initially with 3 segments
        start_col = GRID_COLS // 2
        start_row = GRID_ROWS // 2
        self._snake = [
            (start_col, start_row),
            (start_col - 1, start_row),
            (start_col - 2, start_row),
        ]

        self._spawn_food()

    def _spawn_food(self) -> None:
        """Spawns food at a random grid location not occupied by the snake."""
        empty_cells = [
            (c, r)
            for c in range(GRID_COLS)
            for r in range(GRID_ROWS)
            if (c, r) not in self._snake
        ]
        if empty_cells:
            self._food = random.choice(empty_cells)
        else:
            self._food = (-1, -1)

    def handle_event(self, event_or_action: Union[pygame.event.Event, Action]) -> None:
        """Processes input events from Pygame or Action enums."""
        action: Optional[Action] = None

        if isinstance(event_or_action, Action):
            action = event_or_action
        elif isinstance(event_or_action, pygame.event.Event):
            if event_or_action.type == pygame.KEYDOWN:
                if event_or_action.key in (pygame.K_UP, pygame.K_w):
                    action = Action.UP
                elif event_or_action.key in (pygame.K_DOWN, pygame.K_s):
                    action = Action.DOWN
                elif event_or_action.key in (pygame.K_LEFT, pygame.K_a):
                    action = Action.LEFT
                elif event_or_action.key in (pygame.K_RIGHT, pygame.K_d):
                    action = Action.RIGHT
                elif event_or_action.key == pygame.K_r:
                    action = Action.RESTART
                elif event_or_action.key in (pygame.K_ESCAPE, pygame.K_q):
                    action = Action.BACK

        if not action:
            return

        if action == Action.BACK:
            self._is_finished = True
            return

        if action == Action.RESTART:
            self.reset()
            if self._audio_manager:
                self._audio_manager.play_menu_move()
            return

        if self._game_over:
            return

        # Validate direction change (reject immediate reverse)
        dx, dy = self._direction
        old_next = self._next_direction

        if action == Action.UP and (dx, dy) != (0, 1):
            self._next_direction = (0, -1)
        elif action == Action.DOWN and (dx, dy) != (0, -1):
            self._next_direction = (0, 1)
        elif action == Action.LEFT and (dx, dy) != (1, 0):
            self._next_direction = (-1, 0)
        elif action == Action.RIGHT and (dx, dy) != (-1, 0):
            self._next_direction = (1, 0)

        if self._next_direction != old_next and self._audio_manager:
            self._audio_manager.play_snake_turn()

    def update(self, delta_time: float) -> None:
        """Updates snake position and checks collisions based on delta_time."""
        if self._game_over or self._is_finished:
            return

        self._current_survival_time += delta_time

        self._move_timer += delta_time
        if self._move_timer < self._move_interval:
            return

        self._move_timer %= self._move_interval
        self._direction = self._next_direction

        head_c, head_r = self._snake[0]
        dx, dy = self._direction
        new_head = (head_c + dx, head_r + dy)

        # Detect wall collision
        if not (0 <= new_head[0] < GRID_COLS and 0 <= new_head[1] < GRID_ROWS):
            self._trigger_game_over()
            return

        # Detect self-collision
        if new_head in self._snake:
            self._trigger_game_over()
            return

        # Move snake
        self._snake.insert(0, new_head)

        # Detect food collision
        if new_head == self._food:
            self._score += 10
            is_new_high = self._save_manager.record_game_session("snake", self._score, self._current_survival_time)

            if self._audio_manager:
                if is_new_high and self._score > 10:
                    self._audio_manager.play_high_score()
                else:
                    self._audio_manager.play_snake_eat()

            if self._score % 50 == 0 and self._move_interval > 0.04:
                self._move_interval -= 0.01

            self._spawn_food()
        else:
            self._snake.pop()

    def _trigger_game_over(self) -> None:
        """Sets game over state, updates SaveManager, and plays sound."""
        self._game_over = True
        self._save_manager.record_game_session("snake", self._score, self._current_survival_time)
        if self._audio_manager:
            self._audio_manager.play_game_over()
        logger.info(f"Snake Game Over! Final Score: {self._score}")

    def draw(self, surface: pygame.Surface) -> None:
        """Renders the game board, snake, food, score bar, and overlays."""
        colors = self._get_colors()
        surface.fill(colors["bg"])

        font_header = pygame.font.SysFont("sans-serif", 28, bold=True)
        score_txt = font_header.render(f"SCORE: {self._score}", True, colors["text_primary"])
        high_txt = font_header.render(f"HIGH: {self.high_score}", True, colors["accent"])
        surface.blit(score_txt, (self._offset_x, 20))
        surface.blit(high_txt, (self._offset_x + self._playfield_width - high_txt.get_width(), 20))

        playfield_rect = pygame.Rect(
            self._offset_x - 4,
            self._offset_y - 4,
            self._playfield_width + 8,
            self._playfield_height + 8,
        )
        pygame.draw.rect(surface, colors["surface"], playfield_rect, border_radius=8)
        pygame.draw.rect(surface, colors["border"], playfield_rect, width=3, border_radius=8)

        inner_rect = pygame.Rect(
            self._offset_x,
            self._offset_y,
            self._playfield_width,
            self._playfield_height,
        )
        pygame.draw.rect(surface, colors["bg"], inner_rect)

        if self._food != (-1, -1):
            fc, fr = self._food
            fx = self._offset_x + fc * GRID_CELL_SIZE + GRID_CELL_SIZE // 2
            fy = self._offset_y + fr * GRID_CELL_SIZE + GRID_CELL_SIZE // 2
            radius = GRID_CELL_SIZE // 2 - 2
            pygame.draw.circle(surface, colors["food"], (fx, fy), radius)

        for idx, (sc, sr) in enumerate(self._snake):
            sx = self._offset_x + sc * GRID_CELL_SIZE + 1
            sy = self._offset_y + sr * GRID_CELL_SIZE + 1
            s_rect = pygame.Rect(sx, sy, GRID_CELL_SIZE - 2, GRID_CELL_SIZE - 2)

            color = colors["snake_head"] if idx == 0 else colors["snake_body"]
            pygame.draw.rect(surface, color, s_rect, border_radius=5)

        font_sub = pygame.font.SysFont("sans-serif", 18)
        help_txt = font_sub.render(
            "Controls: Arrows / WASD = Move | R = Restart | ESC = Menu", True, colors["text_muted"]
        )
        surface.blit(help_txt, (SCREEN_WIDTH // 2 - help_txt.get_width() // 2, SCREEN_HEIGHT - 35))

        if self._game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((15, 23, 42, 210))
            surface.blit(overlay, (0, 0))

            modal_w, modal_h = 420, 240
            modal_rect = pygame.Rect(
                SCREEN_WIDTH // 2 - modal_w // 2,
                SCREEN_HEIGHT // 2 - modal_h // 2,
                modal_w,
                modal_h,
            )
            pygame.draw.rect(surface, colors["surface"], modal_rect, border_radius=16)
            pygame.draw.rect(surface, (239, 68, 68), modal_rect, width=3, border_radius=16)

            font_title = pygame.font.SysFont("sans-serif", 36, bold=True)
            font_body = pygame.font.SysFont("sans-serif", 22)

            go_txt = font_title.render("GAME OVER", True, (239, 68, 68))
            final_txt = font_body.render(f"Final Score: {self._score}", True, colors["text_primary"])
            hi_txt = font_body.render(f"High Score: {self.high_score}", True, colors["accent"])
            r_txt = font_body.render("Press R / GPIO to Restart", True, colors["text_primary"])
            esc_txt = font_body.render("Press ESC / BACK for Arcade Menu", True, colors["text_muted"])

            surface.blit(go_txt, (modal_rect.centerx - go_txt.get_width() // 2, modal_rect.top + 25))
            surface.blit(final_txt, (modal_rect.centerx - final_txt.get_width() // 2, modal_rect.top + 75))
            surface.blit(hi_txt, (modal_rect.centerx - hi_txt.get_width() // 2, modal_rect.top + 105))
            surface.blit(r_txt, (modal_rect.centerx - r_txt.get_width() // 2, modal_rect.top + 145))
            surface.blit(esc_txt, (modal_rect.centerx - esc_txt.get_width() // 2, modal_rect.top + 180))

    def cleanup(self) -> None:
        """Clean up resources and sync save manager."""
        self._save_manager.record_game_session("snake", self._score, self._current_survival_time)
