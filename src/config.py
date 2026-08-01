"""
Configuration module for Pi Arcade OS.

Contains application settings, window dimensions, color palettes,
GPIO mappings, LCD settings, audio configuration, theme palettes, and game-specific settings.
Supports Python 3.9+ typing.
"""

from enum import Enum
import os
from typing import Dict, Tuple, List, Any


class Action(Enum):
    """Enumeration of system and game action events."""
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    SELECT = "SELECT"
    BACK = "BACK"
    RESTART = "RESTART"
    QUIT = "QUIT"


class SoundType(Enum):
    """Enumeration of system and game sound effect events."""
    MENU_MOVE = "MENU_MOVE"
    MENU_SELECT = "MENU_SELECT"
    ERROR = "ERROR"
    SNAKE_EAT = "SNAKE_EAT"
    SNAKE_TURN = "SNAKE_TURN"
    GAME_OVER = "GAME_OVER"
    HIGH_SCORE = "HIGH_SCORE"
    STARTUP_JINGLE = "STARTUP_JINGLE"
    # Pong sound events
    PADDLE_HIT = "PADDLE_HIT"
    WALL_BOUNCE = "WALL_BOUNCE"
    POINT_SCORED = "POINT_SCORED"
    MATCH_START = "MATCH_START"
    PAUSE = "PAUSE"
    VICTORY = "VICTORY"
    DEFEAT = "DEFEAT"
    # Tetris sound events
    TETRIS_MOVE = "TETRIS_MOVE"
    TETRIS_ROTATE = "TETRIS_ROTATE"
    TETRIS_SOFT_DROP = "TETRIS_SOFT_DROP"
    TETRIS_HARD_DROP = "TETRIS_HARD_DROP"
    TETRIS_LOCK = "TETRIS_LOCK"
    TETRIS_LINE_CLEAR = "TETRIS_LINE_CLEAR"
    TETRIS_TETRIS_CLEAR = "TETRIS_TETRIS_CLEAR"
    TETRIS_LEVEL_UP = "TETRIS_LEVEL_UP"
    TETRIS_GAME_OVER = "TETRIS_GAME_OVER"


# Display & Window Settings
SCREEN_WIDTH: int = 800
SCREEN_HEIGHT: int = 600
FPS: int = 60
WINDOW_TITLE: str = "Hector Arcade OS"

# Files & Persistence
SAVE_DATA_FILE: str = os.path.join(os.path.dirname(__file__), "..", "save_data.json")
SAVE_DATA_BACKUP: str = os.path.join(os.path.dirname(__file__), "..", "save_data.json.bak")
SETTINGS_FILE: str = os.path.join(os.path.dirname(__file__), "..", "settings.json")
HIGH_SCORE_FILE: str = os.path.join(os.path.dirname(__file__), "..", "snake_highscore.txt")
SNAKE_STATS_FILE: str = os.path.join(os.path.dirname(__file__), "..", "snake_stats.json")

# Theme Palette Definitions (RGB)
THEME_PALETTES: Dict[str, Dict[str, Tuple[int, int, int]]] = {
    "Slate Dark": {
        "bg": (15, 23, 42),
        "surface": (30, 41, 59),
        "surface_selected": (38, 56, 89),
        "border": (51, 65, 85),
        "text_primary": (248, 250, 252),
        "text_muted": (148, 163, 184),
        "accent": (56, 189, 248),
        "snake_head": (34, 197, 94),
        "snake_body": (74, 222, 128),
        "food": (244, 63, 94),
    },
    "Cyberpunk Gold": {
        "bg": (20, 15, 30),
        "surface": (40, 28, 60),
        "surface_selected": (70, 48, 100),
        "border": (90, 60, 130),
        "text_primary": (255, 250, 230),
        "text_muted": (180, 160, 200),
        "accent": (251, 191, 36),
        "snake_head": (245, 158, 11),
        "snake_body": (252, 211, 77),
        "food": (236, 72, 153),
    },
    "Retro Monokai": {
        "bg": (39, 40, 34),
        "surface": (62, 62, 50),
        "surface_selected": (85, 85, 65),
        "border": (110, 110, 85),
        "text_primary": (248, 248, 242),
        "text_muted": (150, 150, 140),
        "accent": (249, 38, 114),
        "snake_head": (166, 226, 46),
        "snake_body": (190, 240, 110),
        "food": (253, 151, 31),
    },
    "Neon Synthwave": {
        "bg": (24, 12, 44),
        "surface": (48, 24, 80),
        "surface_selected": (80, 40, 130),
        "border": (110, 50, 170),
        "text_primary": (255, 255, 255),
        "text_muted": (190, 160, 220),
        "accent": (236, 72, 153),
        "snake_head": (6, 182, 212),
        "snake_body": (103, 232, 249),
        "food": (250, 204, 21),
    },
}

# Default Color Constants (Slate Dark)
COLOR_BG: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["bg"]
COLOR_SURFACE: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["surface"]
COLOR_SURFACE_SELECTED: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["surface_selected"]
COLOR_BORDER: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["border"]
COLOR_TEXT_PRIMARY: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["text_primary"]
COLOR_TEXT_MUTED: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["text_muted"]
COLOR_ACCENT: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["accent"]
COLOR_ACCENT_HOVER: Tuple[int, int, int] = (14, 165, 233)
COLOR_COMING_SOON: Tuple[int, int, int] = (251, 146, 60)

# Hardware Badge Colors
COLOR_BADGE_BG: Tuple[int, int, int] = (20, 40, 70)
COLOR_BADGE_TEXT: Tuple[int, int, int] = (56, 189, 248)
COLOR_BADGE_SUCCESS: Tuple[int, int, int] = (34, 197, 94)

# Snake Game Colors
COLOR_SNAKE_HEAD: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["snake_head"]
COLOR_SNAKE_BODY: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["snake_body"]
COLOR_FOOD: Tuple[int, int, int] = THEME_PALETTES["Slate Dark"]["food"]
COLOR_GAME_OVER: Tuple[int, int, int] = (239, 68, 68)

# GPIO Pin Configuration (BCM pin numbers)
GPIO_PIN_UP: int = 27     # Physical Pin 13
GPIO_PIN_DOWN: int = 22   # Physical Pin 15
GPIO_PIN_LEFT: int = 23   # Physical Pin 16
GPIO_PIN_RIGHT: int = 24  # Physical Pin 18
GPIO_PIN_BUZZER: int = 12 # Physical Pin 32 (PWM / Passive Buzzer)

# 16x2 I2C LCD Configuration
LCD_I2C_ADDRESS: int = 0x27
LCD_COLS: int = 16
LCD_ROWS: int = 2

# Audio Configuration
DEFAULT_VOLUME: float = 0.7
AUDIO_SAMPLE_RATE: int = 44100

# Snake Specific Configuration
GRID_CELL_SIZE: int = 25
GRID_COLS: int = 24
GRID_ROWS: int = 18
SNAKE_INITIAL_SPEED: float = 0.12  # Seconds per step

# Pong Specific Configuration
PONG_WINNING_SCORE: int = 5
PONG_PADDLE_WIDTH: int = 15
PONG_PADDLE_HEIGHT: int = 90
PONG_PADDLE_SPEED: float = 420.0  # Pixels per second
PONG_BALL_SIZE: int = 15
PONG_BALL_INITIAL_SPEED: float = 340.0  # Pixels per second
PONG_BALL_MAX_SPEED: float = 720.0
PONG_BALL_SPEED_INC: float = 25.0

PONG_AI_CONFIG: Dict[str, Dict[str, Any]] = {
    "Easy": {
        "speed": 230.0,
        "delay": 0.15,
        "target_error": 35.0,
    },
    "Normal": {
        "speed": 340.0,
        "delay": 0.08,
        "target_error": 18.0,
    },
    "Hard": {
        "speed": 460.0,
        "delay": 0.02,
        "target_error": 5.0,
    },
}

# Tetris Specific Configuration
TETRIS_BOARD_COLS: int = 10
TETRIS_BOARD_ROWS: int = 20  # Visible rows
TETRIS_SPAWN_HIDDEN_ROWS: int = 2  # Total grid height = 22 rows
TETRIS_CELL_SIZE: int = 24

# Base scoring table multiplied by level
TETRIS_BASE_SCORES: Dict[int, int] = {
    1: 100,  # Single
    2: 300,  # Double
    3: 500,  # Triple
    4: 800,  # Tetris
}

TETRIS_SOFT_DROP_POINTS: int = 1
TETRIS_HARD_DROP_POINTS: int = 2

# Tetromino Colors (RGB)
TETRIS_PIECE_COLORS: Dict[str, Tuple[int, int, int]] = {
    "I": (6, 182, 212),    # Cyan
    "O": (250, 204, 21),   # Yellow
    "T": (168, 85, 247),   # Purple
    "S": (34, 197, 94),    # Green
    "Z": (239, 68, 68),    # Red
    "J": (59, 130, 246),   # Blue
    "L": (249, 115, 22),   # Orange
}

# Tetromino Shape Matrix Definitions (4x4 or 3x3 rotational matrices)
TETRIS_SHAPES: Dict[str, List[List[List[int]]]] = {
    "I": [
        [[0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],

        [[0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0]],

        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0]],

        [[0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0]],
    ],
    "O": [
        [[1, 1],
         [1, 1]],
    ],
    "T": [
        [[0, 1, 0],
         [1, 1, 1],
         [0, 0, 0]],

        [[0, 1, 0],
         [0, 1, 1],
         [0, 1, 0]],

        [[0, 0, 0],
         [1, 1, 1],
         [0, 1, 0]],

        [[0, 1, 0],
         [1, 1, 0],
         [0, 1, 0]],
    ],
    "S": [
        [[0, 1, 1],
         [1, 1, 0],
         [0, 0, 0]],

        [[0, 1, 0],
         [0, 1, 1],
         [0, 0, 1]],

        [[0, 0, 0],
         [0, 1, 1],
         [1, 1, 0]],

        [[1, 0, 0],
         [1, 1, 0],
         [0, 1, 0]],
    ],
    "Z": [
        [[1, 1, 0],
         [0, 1, 1],
         [0, 0, 0]],

        [[0, 0, 1],
         [0, 1, 1],
         [0, 1, 0]],

        [[0, 0, 0],
         [1, 1, 0],
         [0, 1, 1]],

        [[0, 1, 0],
         [1, 1, 0],
         [1, 0, 0]],
    ],
    "J": [
        [[1, 0, 0],
         [1, 1, 1],
         [0, 0, 0]],

        [[0, 1, 1],
         [0, 1, 0],
         [0, 1, 0]],

        [[0, 0, 0],
         [1, 1, 1],
         [0, 0, 1]],

        [[0, 1, 0],
         [0, 1, 0],
         [1, 1, 0]],
    ],
    "L": [
        [[0, 0, 1],
         [1, 1, 1],
         [0, 0, 0]],

        [[0, 1, 0],
         [0, 1, 0],
         [0, 1, 1]],

        [[0, 0, 0],
         [1, 1, 1],
         [1, 0, 0]],

        [[1, 1, 0],
         [0, 1, 0],
         [0, 1, 0]],
    ],
}

# Launcher Animation Settings
CURSOR_PULSE_SPEED: float = 6.0  # Radians per second for menu cursor pulse
PARTICLE_COUNT: int = 35
FADE_IN_DURATION: float = 0.5
