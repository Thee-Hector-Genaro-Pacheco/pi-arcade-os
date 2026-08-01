"""
Tetris Game implementation for Pi Arcade OS.

Classic falling-block puzzle game with 7-bag randomizer, SRS-inspired wall kick rotation,
ghost piece preview, line clearing animations, scoring table, level progression,
keyboard & 4-button GPIO hardware support, non-blocking PCM audio, and 16x2 I2C LCD integration.
Supports Python 3.9+ typing.
"""

import logging
import random
import time
from typing import Dict, List, Optional, Tuple, Union
import pygame

from src.config import (
    Action,
    SoundType,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TETRIS_BOARD_COLS,
    TETRIS_BOARD_ROWS,
    TETRIS_SPAWN_HIDDEN_ROWS,
    TETRIS_CELL_SIZE,
    TETRIS_BASE_SCORES,
    TETRIS_SOFT_DROP_POINTS,
    TETRIS_HARD_DROP_POINTS,
    TETRIS_PIECE_COLORS,
    TETRIS_SHAPES,
)
from src.game_interface import ArcadeGame
from src.hardware.audio import AudioManager
from src.hardware.display import DisplayManager
from src.save_manager import SaveManager
from src.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class TetrisPiece:
    """Represents an active or preview Tetromino piece."""

    def __init__(self, shape_type: str) -> None:
        self.shape_type: str = shape_type
        self.rotations: List[List[List[int]]] = TETRIS_SHAPES[shape_type]
        self.color: Tuple[int, int, int] = TETRIS_PIECE_COLORS[shape_type]
        self.rotation_idx: int = 0
        self.col: int = (TETRIS_BOARD_COLS - len(self.rotations[0][0])) // 2
        self.row: int = 0  # Spawn in hidden row area

    @property
    def matrix(self) -> List[List[int]]:
        """Returns the current 2D rotation matrix."""
        return self.rotations[self.rotation_idx % len(self.rotations)]

    def rotate_clockwise(self) -> None:
        """Rotates piece matrix clockwise."""
        self.rotation_idx = (self.rotation_idx + 1) % len(self.rotations)

    def rotate_counterclockwise(self) -> None:
        """Rotates piece matrix counterclockwise."""
        self.rotation_idx = (self.rotation_idx - 1) % len(self.rotations)


class TetrisGame(ArcadeGame):
    """Classic Tetris game implementation for Pi Arcade OS."""

    TOTAL_GRID_ROWS: int = TETRIS_BOARD_ROWS + TETRIS_SPAWN_HIDDEN_ROWS  # 22 rows total

    def __init__(
        self,
        audio_manager: Optional[AudioManager] = None,
        display_manager: Optional[DisplayManager] = None,
        settings_manager: Optional[SettingsManager] = None,
        save_manager: Optional[SaveManager] = None,
    ) -> None:
        self._name: str = "Tetris"
        self._description: str = "Classic falling-block puzzle game with rotation, line clearing, level progression, and GPIO support."
        self._version: str = "1.0.0"
        self._author: str = "Hector Pacheco"
        self._icon: str = "🧱"

        self._is_finished: bool = False
        self._paused: bool = False
        self._game_over: bool = False
        self._score: int = 0
        self._lines_cleared: int = 0
        self._level: int = 1
        self._tetrises_count: int = 0
        self._session_start_time: float = time.time()
        self._high_score: int = 0

        self._audio_manager: Optional[AudioManager] = audio_manager
        self._display_manager: Optional[DisplayManager] = display_manager
        self._settings_manager: Optional[SettingsManager] = settings_manager
        self._save_manager: SaveManager = save_manager or SaveManager()

        # 7-Bag Randomizer
        self._bag: List[str] = []

        # Grid state: 22 rows x 10 cols (0 = empty, RGB tuple = locked color)
        self._grid: List[List[Optional[Tuple[int, int, int]]]] = [
            [None for _ in range(TETRIS_BOARD_COLS)] for _ in range(self.TOTAL_GRID_ROWS)
        ]

        self._active_piece: Optional[TetrisPiece] = None
        self._next_piece: Optional[TetrisPiece] = None

        # Timing and Gravity
        self._drop_timer: float = 0.0
        self._lock_delay_timer: float = 0.0
        self._is_on_ground: bool = False

        # Visual Flash Animation for Line Clears
        self._cleared_rows: List[int] = []
        self._clear_animation_timer: float = 0.0

        # Board Position on Screen
        self._board_w: int = TETRIS_BOARD_COLS * TETRIS_CELL_SIZE
        self._board_h: int = TETRIS_BOARD_ROWS * TETRIS_CELL_SIZE
        self._start_x: int = (SCREEN_WIDTH - self._board_w) // 2
        self._start_y: int = (SCREEN_HEIGHT - self._board_h) // 2 + 10

        self.reset()

    # ArcadeGame Property Implementations
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

    @property
    def score(self) -> int:
        return self._score

    @property
    def high_score(self) -> int:
        return self._high_score

    # Dependency Injection Setters
    def set_audio_manager(self, audio_manager: Optional[AudioManager]) -> None:
        self._audio_manager = audio_manager

    def set_display_manager(self, display_manager: Optional[DisplayManager]) -> None:
        self._display_manager = display_manager

    def set_settings_manager(self, settings_manager: Optional[SettingsManager]) -> None:
        self._settings_manager = settings_manager

    def set_save_manager(self, save_manager: Optional[SaveManager]) -> None:
        self._save_manager = save_manager or SaveManager()
        self._high_score = self._save_manager.get_high_score("tetris")

    def _get_gravity_speed(self) -> float:
        """Calculates gravity drop interval in seconds based on level and difficulty setting."""
        diff = self._settings_manager.difficulty if self._settings_manager else "Normal"
        base_interval = max(0.05, 0.8 - (self._level - 1) * 0.065)
        if diff == "Easy":
            return base_interval * 1.3
        elif diff == "Hard":
            return base_interval * 0.75
        return base_interval

    def _fill_bag(self) -> None:
        """Refills the 7-bag randomizer piece list."""
        pieces = ["I", "O", "T", "S", "Z", "J", "L"]
        random.shuffle(pieces)
        self._bag.extend(pieces)

    def _get_next_shape_from_bag(self) -> str:
        """Pops the next shape type from the 7-bag randomizer."""
        if not self._bag:
            self._fill_bag()
        return self._bag.pop(0)

    def start(self) -> None:
        """Called when game is launched from arcade launcher."""
        self._is_finished = False
        self._session_start_time = time.time()
        self.reset()

        if self._audio_manager:
            self._audio_manager.play_match_start()

        self._update_lcd()

    def reset(self) -> None:
        """Resets Tetris grid, score, level, and piece state."""
        self._score = 0
        self._lines_cleared = 0
        self._level = 1
        self._tetrises_count = 0
        self._paused = False
        self._game_over = False
        self._is_finished = False
        self._cleared_rows = []
        self._clear_animation_timer = 0.0

        if self._save_manager:
            self._high_score = self._save_manager.get_high_score("tetris")

        # Clear 22x10 grid
        self._grid = [
            [None for _ in range(TETRIS_BOARD_COLS)] for _ in range(self.TOTAL_GRID_ROWS)
        ]

        self._bag = []
        self._next_piece = TetrisPiece(self._get_next_shape_from_bag())
        self._spawn_piece()

    def _spawn_piece(self) -> None:
        """Spawns next piece at top center of board."""
        self._active_piece = self._next_piece
        self._next_piece = TetrisPiece(self._get_next_shape_from_bag())
        self._drop_timer = 0.0
        self._lock_delay_timer = 0.0
        self._is_on_ground = False

        if self._active_piece and not self._is_valid_position(self._active_piece):
            logger.info("New piece spawned in occupied position. Game Over.")
            self._trigger_game_over()

    def _is_valid_position(self, piece: TetrisPiece, offset_col: int = 0, offset_row: int = 0) -> bool:
        """Checks if piece position is within board bounds and free of locked blocks."""
        matrix = piece.matrix
        for r_idx, row in enumerate(matrix):
            for c_idx, cell in enumerate(row):
                if cell:
                    target_col = piece.col + c_idx + offset_col
                    target_row = piece.row + r_idx + offset_row

                    # Wall and floor boundaries
                    if target_col < 0 or target_col >= TETRIS_BOARD_COLS:
                        return False
                    if target_row >= self.TOTAL_GRID_ROWS:
                        return False

                    # Locked block collision
                    if target_row >= 0 and self._grid[target_row][target_col] is not None:
                        return False
        return True

    def _get_ghost_row(self) -> int:
        """Calculates bottommost row offset for active piece projection."""
        if not self._active_piece:
            return 0

        ghost_offset = 0
        while self._is_valid_position(self._active_piece, offset_row=ghost_offset + 1):
            ghost_offset += 1
        return self._active_piece.row + ghost_offset

    def _rotate_active_piece(self, clockwise: bool = True) -> bool:
        """Attempts rotation with wall-kick offsets (-1, +1, -2, +2)."""
        if not self._active_piece or self._game_over or self._paused:
            return False

        orig_idx = self._active_piece.rotation_idx
        if clockwise:
            self._active_piece.rotate_clockwise()
        else:
            self._active_piece.rotate_counterclockwise()

        # Wall-kick test offsets
        kick_offsets = [0, -1, 1, -2, 2]
        for offset in kick_offsets:
            if self._is_valid_position(self._active_piece, offset_col=offset):
                self._active_piece.col += offset
                if self._audio_manager:
                    self._audio_manager.play(SoundType.TETRIS_ROTATE)
                return True

        # Revert rotation if all kick offsets failed
        self._active_piece.rotation_idx = orig_idx
        return False

    def _move_left(self) -> None:
        """Moves active piece left by 1 column if valid."""
        if self._active_piece and self._is_valid_position(self._active_piece, offset_col=-1):
            self._active_piece.col -= 1
            if self._audio_manager:
                self._audio_manager.play(SoundType.TETRIS_MOVE)

    def _move_right(self) -> None:
        """Moves active piece right by 1 column if valid."""
        if self._active_piece and self._is_valid_position(self._active_piece, offset_col=1):
            self._active_piece.col += 1
            if self._audio_manager:
                self._audio_manager.play(SoundType.TETRIS_MOVE)

    def _soft_drop(self) -> None:
        """Moves active piece down by 1 row and awards soft drop points."""
        if not self._active_piece or self._game_over or self._paused:
            return

        if self._is_valid_position(self._active_piece, offset_row=1):
            self._active_piece.row += 1
            self._score += TETRIS_SOFT_DROP_POINTS
            self._drop_timer = 0.0
            if self._audio_manager:
                self._audio_manager.play(SoundType.TETRIS_SOFT_DROP)
        else:
            self._lock_active_piece()

    def _hard_drop(self) -> None:
        """Instantly drops active piece to ghost row, awards hard drop points, and locks."""
        if not self._active_piece or self._game_over or self._paused:
            return

        drop_distance = 0
        while self._is_valid_position(self._active_piece, offset_row=1):
            self._active_piece.row += 1
            drop_distance += 1

        self._score += drop_distance * TETRIS_HARD_DROP_POINTS
        if self._audio_manager:
            self._audio_manager.play(SoundType.TETRIS_HARD_DROP)

        self._lock_active_piece()

    def _lock_active_piece(self) -> None:
        """Locks active piece into grid matrix and checks line clears."""
        if not self._active_piece:
            return

        matrix = self._active_piece.matrix
        color = self._active_piece.color

        for r_idx, row in enumerate(matrix):
            for c_idx, cell in enumerate(row):
                if cell:
                    target_col = self._active_piece.col + c_idx
                    target_row = self._active_piece.row + r_idx
                    if 0 <= target_row < self.TOTAL_GRID_ROWS and 0 <= target_col < TETRIS_BOARD_COLS:
                        self._grid[target_row][target_col] = color

        if self._audio_manager:
            self._audio_manager.play(SoundType.TETRIS_LOCK)

        self._check_line_clears()

    def _check_line_clears(self) -> None:
        """Detects full horizontal rows, triggers visual flash animation, and updates score."""
        full_rows: List[int] = []
        for r in range(self.TOTAL_GRID_ROWS):
            if all(cell is not None for cell in self._grid[r]):
                full_rows.append(r)

        if full_rows:
            self._cleared_rows = full_rows
            self._clear_animation_timer = 0.15  # 150ms flash animation

            num_cleared = len(full_rows)
            self._lines_cleared += num_cleared

            # Scoring
            points = TETRIS_BASE_SCORES.get(num_cleared, 100 * num_cleared) * self._level
            self._score += points

            if num_cleared == 4:
                self._tetrises_count += 1
                if self._audio_manager:
                    self._audio_manager.play(SoundType.TETRIS_TETRIS_CLEAR)
            else:
                if self._audio_manager:
                    self._audio_manager.play(SoundType.TETRIS_LINE_CLEAR)

            # Level Progression every 10 lines
            new_level = 1 + (self._lines_cleared // 10)
            if new_level > self._level:
                self._level = new_level
                if self._audio_manager:
                    self._audio_manager.play(SoundType.TETRIS_LEVEL_UP)

            self._update_lcd()
        else:
            self._spawn_piece()

    def _finish_line_clears(self) -> None:
        """Removes cleared rows from grid matrix and shifts rows down."""
        for r in sorted(self._cleared_rows):
            del self._grid[r]
            self._grid.insert(0, [None for _ in range(TETRIS_BOARD_COLS)])

        self._cleared_rows.clear()
        self._spawn_piece()

    def _trigger_game_over(self) -> None:
        """Triggers game-over state and persists statistics."""
        self._game_over = True
        duration = time.time() - self._session_start_time

        is_high = self._save_manager.record_tetris_session(
            score=self._score,
            lines_cleared=self._lines_cleared,
            level=self._level,
            tetrises_count=self._tetrises_count,
            duration_sec=duration,
        )

        if is_high:
            self._high_score = self._score
            if self._audio_manager:
                self._audio_manager.play_high_score()
            if self._display_manager:
                self._display_manager.show_tetris_new_high_score(self._score)
        else:
            if self._audio_manager:
                self._audio_manager.play(SoundType.TETRIS_GAME_OVER)
            if self._display_manager:
                self._display_manager.show_tetris_game_over(self._score)

    def _update_lcd(self) -> None:
        """Updates physical 16x2 LCD display."""
        if not self._display_manager:
            return

        if self._paused:
            self._display_manager.show_tetris_paused()
        elif self._game_over:
            self._display_manager.show_tetris_game_over(self._score)
        else:
            self._display_manager.show_tetris_score(self._score, self._lines_cleared, self._level)

    def _toggle_pause(self) -> None:
        """Toggles game pause state and updates LCD and audio feedback."""
        if self._game_over or self._is_finished:
            return
        self._paused = not self._paused
        logger.info(f"Tetris Pause Toggled: {self._paused}")
        if self._audio_manager:
            self._audio_manager.play_pause()
        self._update_lcd()

    def handle_event(self, event_or_action: Union[pygame.event.Event, Action]) -> None:
        """Processes keypresses and normalized GPIO Actions."""
        action: Optional[Action] = None

        if isinstance(event_or_action, Action):
            action = event_or_action
        elif isinstance(event_or_action, pygame.event.Event):
            if event_or_action.type == pygame.KEYDOWN:
                key = event_or_action.key
                if key in (pygame.K_ESCAPE, pygame.K_q):
                    action = Action.BACK
                elif key == pygame.K_p:
                    self._toggle_pause()
                    return
                elif key == pygame.K_r and self._game_over:
                    action = Action.RESTART
                elif not self._paused and not self._game_over:
                    if key in (pygame.K_UP, pygame.K_x):
                        self._rotate_active_piece(clockwise=True)
                    elif key == pygame.K_z:
                        self._rotate_active_piece(clockwise=False)
                    elif key in (pygame.K_LEFT, pygame.K_a):
                        self._move_left()
                    elif key in (pygame.K_RIGHT, pygame.K_d):
                        self._move_right()
                    elif key in (pygame.K_DOWN, pygame.K_s):
                        self._soft_drop()
                    elif key == pygame.K_SPACE:
                        self._hard_drop()

        if not action:
            return

        if action == Action.BACK:
            logger.info("Tetris: Returning to arcade launcher menu")
            self._is_finished = True
            return

        if action == Action.RESTART and self._game_over:
            self.reset()
            return

        if self._paused or self._game_over:
            return

        if action == Action.UP:
            self._rotate_active_piece(clockwise=True)
        elif action == Action.LEFT:
            self._move_left()
        elif action == Action.RIGHT:
            self._move_right()
        elif action == Action.DOWN:
            self._soft_drop()
        elif action == Action.SELECT:
            self._hard_drop()

    def update(self, delta_time: float) -> None:
        """Updates gravity, line clear animations, and piece placement."""
        if self._is_finished or self._paused or self._game_over:
            return

        # Line clear flash animation delay
        if self._clear_animation_timer > 0:
            self._clear_animation_timer -= delta_time
            if self._clear_animation_timer <= 0:
                self._finish_line_clears()
            return

        if not self._active_piece:
            return

        # Gravity Drop Timer
        self._drop_timer += delta_time
        gravity_interval = self._get_gravity_speed()

        if self._drop_timer >= gravity_interval:
            self._drop_timer = 0.0
            if self._is_valid_position(self._active_piece, offset_row=1):
                self._active_piece.row += 1
                self._is_on_ground = False
            else:
                self._is_on_ground = True

        # Lock Delay when touching floor/locked blocks
        if not self._is_valid_position(self._active_piece, offset_row=1):
            self._lock_delay_timer += delta_time
            if self._lock_delay_timer >= 0.4:  # 400ms lock delay
                self._lock_active_piece()
        else:
            self._lock_delay_timer = 0.0

    def draw(self, surface: pygame.Surface) -> None:
        """Renders playfield, active/ghost pieces, next piece, score, and overlays."""
        colors = self._settings_manager.get_theme_colors() if self._settings_manager else {
            "bg": (15, 23, 42),
            "surface": (30, 41, 59),
            "border": (51, 65, 85),
            "text_primary": (248, 250, 252),
            "text_muted": (148, 163, 184),
            "accent": (56, 189, 248),
        }

        surface.fill(colors["bg"])

        font_title = pygame.font.SysFont("sans-serif", 32, bold=True)
        font_stat_lbl = pygame.font.SysFont("sans-serif", 16)
        font_stat_val = pygame.font.SysFont("sans-serif", 24, bold=True)
        font_sub = pygame.font.SysFont("sans-serif", 14)

        # 1. Main Playfield Board Outline
        board_rect = pygame.Rect(self._start_x, self._start_y, self._board_w, self._board_h)
        pygame.draw.rect(surface, colors["surface"], board_rect, border_radius=6)
        pygame.draw.rect(surface, colors["border"], board_rect, width=3, border_radius=6)

        # Draw Grid Cells (Visible rows 2..21)
        for r in range(TETRIS_SPAWN_HIDDEN_ROWS, self.TOTAL_GRID_ROWS):
            for c in range(TETRIS_BOARD_COLS):
                cell_rect = pygame.Rect(
                    self._start_x + c * TETRIS_CELL_SIZE,
                    self._start_y + (r - TETRIS_SPAWN_HIDDEN_ROWS) * TETRIS_CELL_SIZE,
                    TETRIS_CELL_SIZE,
                    TETRIS_CELL_SIZE,
                )

                cell_color = self._grid[r][c]
                if r in self._cleared_rows:
                    # Flash line clear white
                    pygame.draw.rect(surface, (255, 255, 255), cell_rect)
                    pygame.draw.rect(surface, colors["bg"], cell_rect, width=1)
                elif cell_color is not None:
                    pygame.draw.rect(surface, cell_color, cell_rect, border_radius=4)
                    pygame.draw.rect(surface, (255, 255, 255), cell_rect, width=1, border_radius=4)
                else:
                    # Subtle grid lines
                    pygame.draw.rect(surface, (colors["border"][0] // 2, colors["border"][1] // 2, colors["border"][2] // 2), cell_rect, width=1)

        # 2. Render Ghost Piece Projection
        diff = self._settings_manager.difficulty if self._settings_manager else "Normal"
        show_ghost = (diff != "Hard") and (self._active_piece is not None) and not self._game_over and not self._paused

        if show_ghost and self._active_piece:
            ghost_row = self._get_ghost_row()
            ghost_matrix = self._active_piece.matrix
            for r_idx, row in enumerate(ghost_matrix):
                for c_idx, cell in enumerate(row):
                    if cell:
                        vis_row = ghost_row + r_idx - TETRIS_SPAWN_HIDDEN_ROWS
                        vis_col = self._active_piece.col + c_idx
                        if 0 <= vis_row < TETRIS_BOARD_ROWS and 0 <= vis_col < TETRIS_BOARD_COLS:
                            ghost_rect = pygame.Rect(
                                self._start_x + vis_col * TETRIS_CELL_SIZE,
                                self._start_y + vis_row * TETRIS_CELL_SIZE,
                                TETRIS_CELL_SIZE,
                                TETRIS_CELL_SIZE,
                            )
                            g_surf = pygame.Surface((TETRIS_CELL_SIZE, TETRIS_CELL_SIZE), pygame.SRCALPHA)
                            r_c, g_c, b_c = self._active_piece.color
                            g_surf.fill((r_c, g_c, b_c, 50))
                            surface.blit(g_surf, ghost_rect)
                            pygame.draw.rect(surface, (r_c, g_c, b_c, 100), ghost_rect, width=1)

        # 3. Render Active Piece
        if self._active_piece and not self._game_over and self._clear_animation_timer <= 0:
            matrix = self._active_piece.matrix
            for r_idx, row in enumerate(matrix):
                for c_idx, cell in enumerate(row):
                    if cell:
                        vis_row = self._active_piece.row + r_idx - TETRIS_SPAWN_HIDDEN_ROWS
                        vis_col = self._active_piece.col + c_idx
                        if 0 <= vis_row < TETRIS_BOARD_ROWS and 0 <= vis_col < TETRIS_BOARD_COLS:
                            piece_rect = pygame.Rect(
                                self._start_x + vis_col * TETRIS_CELL_SIZE,
                                self._start_y + vis_row * TETRIS_CELL_SIZE,
                                TETRIS_CELL_SIZE,
                                TETRIS_CELL_SIZE,
                            )
                            pygame.draw.rect(surface, self._active_piece.color, piece_rect, border_radius=4)
                            pygame.draw.rect(surface, (255, 255, 255), piece_rect, width=1, border_radius=4)

        # 4. Next Piece Preview Box (Right Side)
        preview_x = self._start_x + self._board_w + 35
        preview_y = self._start_y
        preview_rect = pygame.Rect(preview_x, preview_y, 160, 140)

        pygame.draw.rect(surface, colors["surface"], preview_rect, border_radius=10)
        pygame.draw.rect(surface, colors["border"], preview_rect, width=2, border_radius=10)

        lbl_next = font_stat_lbl.render("NEXT PIECE", True, colors["text_muted"])
        surface.blit(lbl_next, (preview_rect.centerx - lbl_next.get_width() // 2, preview_rect.top + 12))

        if self._next_piece:
            n_matrix = self._next_piece.matrix
            n_rows = len(n_matrix)
            n_cols = len(n_matrix[0])
            offset_x = preview_rect.left + (160 - n_cols * 20) // 2
            offset_y = preview_rect.top + 45 + (80 - n_rows * 20) // 2

            for r_idx, row in enumerate(n_matrix):
                for c_idx, cell in enumerate(row):
                    if cell:
                        p_cell_rect = pygame.Rect(offset_x + c_idx * 20, offset_y + r_idx * 20, 20, 20)
                        pygame.draw.rect(surface, self._next_piece.color, p_cell_rect, border_radius=3)
                        pygame.draw.rect(surface, (255, 255, 255), p_cell_rect, width=1, border_radius=3)

        # 5. Left Statistics Sidebar
        stats_x = self._start_x - 195
        stats_y = self._start_y

        t_lbl = font_title.render("TETRIS", True, colors["accent"])
        surface.blit(t_lbl, (stats_x + 10, stats_y))

        y_offset = stats_y + 55
        stat_boxes = [
            ("SCORE", str(self._score), colors["text_primary"]),
            ("HIGH SCORE", str(self._high_score), colors["accent"]),
            ("LINES CLEARED", str(self._lines_cleared), (34, 197, 94)),
            ("LEVEL", str(self._level), (251, 146, 60)),
        ]

        for label, val, val_col in stat_boxes:
            box_r = pygame.Rect(stats_x, y_offset, 165, 54)
            pygame.draw.rect(surface, colors["surface"], box_r, border_radius=8)
            pygame.draw.rect(surface, colors["border"], box_r, width=1, border_radius=8)

            l_txt = font_stat_lbl.render(label, True, colors["text_muted"])
            v_txt = font_stat_val.render(val, True, val_col)
            surface.blit(l_txt, (box_r.left + 12, box_r.top + 6))
            surface.blit(v_txt, (box_r.left + 12, box_r.top + 24))
            y_offset += 64

        # Controls Hint Footer
        hint_txt = font_sub.render("Controls: ↑ / X (Rotate)  |  A / D (Move)  |  S (Soft)  |  Space (Hard)", True, colors["text_muted"])
        surface.blit(hint_txt, (SCREEN_WIDTH // 2 - hint_txt.get_width() // 2, SCREEN_HEIGHT - 30))

        # 6. Pause / Game Over Overlay Modals
        if self._paused:
            self._draw_overlay_modal(surface, colors, "PAUSED", "Press P / Resume to Continue")
        elif self._game_over:
            self._draw_overlay_modal(surface, colors, "GAME OVER", f"Final Score: {self._score}  |  R to Restart")

    def _draw_overlay_modal(
        self, surface: pygame.Surface, colors: Dict[str, Tuple[int, int, int]], title: str, subtitle: str
    ) -> None:
        """Renders transparent modal overlay for pause and game over states."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 23, 42, 210))
        surface.blit(overlay, (0, 0))

        modal_w, modal_h = 440, 180
        modal_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - modal_w // 2,
            SCREEN_HEIGHT // 2 - modal_h // 2,
            modal_w,
            modal_h,
        )

        pygame.draw.rect(surface, colors["surface"], modal_rect, border_radius=14)
        border_col = (239, 68, 68) if title == "GAME OVER" else colors["accent"]
        pygame.draw.rect(surface, border_col, modal_rect, width=3, border_radius=14)

        font_m_title = pygame.font.SysFont("sans-serif", 36, bold=True)
        font_m_sub = pygame.font.SysFont("sans-serif", 20)

        t_txt = font_m_title.render(title, True, border_col)
        s_txt = font_m_sub.render(subtitle, True, colors["text_primary"])

        surface.blit(t_txt, (modal_rect.centerx - t_txt.get_width() // 2, modal_rect.top + 40))
        surface.blit(s_txt, (modal_rect.centerx - s_txt.get_width() // 2, modal_rect.top + 105))

    def cleanup(self) -> None:
        """Releases resources before exit."""
        self._is_finished = True
        logger.info("TetrisGame resources cleaned up.")
