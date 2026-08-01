"""
Achievement Manager module for Pi Arcade OS.

Manages persistent arcade achievement definitions, condition checking, JSON persistence
via SaveManager, toast popup triggering via NotificationManager, and fanfare sound synthesis.
Supports Python 3.9+ typing.
"""

from dataclasses import dataclass
import logging
from typing import Dict, List, Optional
from src.save_manager import SaveManager
from src.notification_manager import NotificationManager
from src.hardware.audio import AudioManager

logger = logging.getLogger(__name__)


@dataclass
class Achievement:
    """Achievement definition dataclass."""
    id: str
    title: str
    description: str
    icon: str
    color: tuple


class AchievementManager:
    """Central manager for checking, unlocking, and persisting achievements."""

    DEFINITIONS: Dict[str, Achievement] = {
        "first_launch": Achievement(
            id="first_launch",
            title="First Launch",
            description="Welcome to Pi Arcade OS!",
            icon="🚀",
            color=(59, 130, 246),
        ),
        "first_snake": Achievement(
            id="first_snake",
            title="First Snake Game",
            description="Started your first Snake match.",
            icon="🐍",
            color=(34, 197, 94),
        ),
        "first_pong_win": Achievement(
            id="first_pong_win",
            title="First Pong Win",
            description="Defeated Player 2 / AI in Pong!",
            icon="🏆",
            color=(245, 158, 11),
        ),
        "first_tetris_line": Achievement(
            id="first_tetris_line",
            title="First Tetris Line",
            description="Cleared your first line in Tetris!",
            icon="🧱",
            color=(6, 182, 212),
        ),
        "score_100_snake": Achievement(
            id="score_100_snake",
            title="Score 100 in Snake",
            description="Reached a high score of 100+ in Snake!",
            icon="👑",
            color=(234, 179, 8),
        ),
        "play_10_games": Achievement(
            id="play_10_games",
            title="Play 10 Games",
            description="Completed 10 arcade game sessions.",
            icon="🎮",
            color=(168, 85, 247),
        ),
        "play_100_games": Achievement(
            id="play_100_games",
            title="Play 100 Games",
            description="Completed 100 arcade game sessions!",
            icon="💎",
            color=(236, 72, 153),
        ),
        "arcade_veteran": Achievement(
            id="arcade_veteran",
            title="Arcade Veteran",
            description="Logged over 1 hour of total play time!",
            icon="⭐",
            color=(251, 146, 60),
        ),
    }

    def __init__(
        self,
        save_manager: SaveManager,
        notification_manager: Optional[NotificationManager] = None,
        audio_manager: Optional[AudioManager] = None,
    ) -> None:
        self._save_manager: SaveManager = save_manager
        self._notification_manager: Optional[NotificationManager] = notification_manager
        self._audio_manager: Optional[AudioManager] = audio_manager

        # Check startup achievement (First Launch)
        self.check_achievements("launch")

    def unlock(self, achievement_id: str) -> bool:
        """
        Unlocks an achievement by ID if not already unlocked.

        Args:
            achievement_id: Identifier key matching DEFINITIONS.

        Returns:
            True if newly unlocked, False if already unlocked or unknown.
        """
        clean_id = achievement_id.strip().lower()
        if clean_id not in self.DEFINITIONS:
            logger.warning(f"Unknown achievement ID '{clean_id}'")
            return False

        newly_unlocked = self._save_manager.unlock_achievement(clean_id)
        if newly_unlocked:
            ach = self.DEFINITIONS[clean_id]
            logger.info(f"🏆 Achievement Unlocked: [{ach.title}] {ach.description}")

            if self._notification_manager:
                self._notification_manager.notify(
                    title=f"Achievement: {ach.title}",
                    message=ach.description,
                    icon=ach.icon,
                    color=ach.color,
                    duration=3.8,
                )

            if self._audio_manager:
                self._audio_manager.play_achievement()

            return True

        return False

    def is_unlocked(self, achievement_id: str) -> bool:
        """Returns True if achievement has been unlocked."""
        return self._save_manager.is_achievement_unlocked(achievement_id)

    def check_achievements(self, event_type: str, data: Optional[Dict[str, float]] = None) -> None:
        """
        Evaluates system events against achievement conditions.

        Args:
            event_type: Event trigger ("launch", "game_start", "game_end", "score_update", "line_clear").
            data: Event context data (score, game_id, lines, etc.).
        """
        data = data or {}

        # 1. Startup / Launch
        if event_type == "launch":
            self.unlock("first_launch")

        # 2. Game Start
        if event_type == "game_start":
            game_id = str(data.get("game_id", "")).lower()
            if game_id == "snake":
                self.unlock("first_snake")

        # 3. Game End / Session Update
        total_sessions = self._save_manager.get_total_games_played()
        if total_sessions >= 10:
            self.unlock("play_10_games")
        if total_sessions >= 100:
            self.unlock("play_100_games")

        if self._save_manager.total_play_time >= 3600.0 or total_sessions >= 50:
            self.unlock("arcade_veteran")

        # 4. Score Updates
        snake_high = self._save_manager.get_high_score("snake")
        if snake_high >= 100:
            self.unlock("score_100_snake")

        pong_wins = self._save_manager.get_wins("pong")
        if pong_wins >= 1:
            self.unlock("first_pong_win")

        # 5. Line Clears
        tetris_lines = self._save_manager.get_total_lines("tetris")
        if tetris_lines >= 1 or data.get("lines_cleared", 0) > 0:
            self.unlock("first_tetris_line")

    def get_all_achievements(self) -> List[Dict[str, object]]:
        """Returns list of all achievement definitions with active unlocked status."""
        result = []
        for ach in self.DEFINITIONS.values():
            unlocked = self.is_unlocked(ach.id)
            unlocked_at = self._save_manager.achievements.get(ach.id, "")
            result.append({
                "id": ach.id,
                "title": ach.title,
                "description": ach.description,
                "icon": ach.icon,
                "color": ach.color,
                "unlocked": unlocked,
                "unlocked_at": unlocked_at,
            })
        return result
