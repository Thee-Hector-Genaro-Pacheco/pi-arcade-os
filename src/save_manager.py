"""
Save Manager module for Pi Arcade OS.

Provides centralized, atomic, crash-resilient JSON save storage for high scores,
game stats, total play time, recent games, player profiles, and settings.
Includes automatic corruption recovery via backup restoration.
Supports Python 3.9+ typing.
"""

import json
import logging
import os
import shutil
import tempfile
from typing import Any, Dict, Optional, Union
from src.config import SAVE_DATA_FILE, SAVE_DATA_BACKUP

logger = logging.getLogger(__name__)


class SaveManager:
    """Centralized save manager handling atomic I/O and corruption recovery."""

    def __init__(self, filepath: str = SAVE_DATA_FILE, backup_path: str = SAVE_DATA_BACKUP) -> None:
        """
        Initializes SaveManager.

        Args:
            filepath: Path to primary JSON save file.
            backup_path: Path to backup JSON save file.
        """
        self._filepath: str = filepath
        self._backup_path: str = backup_path

        # Primary Save Data Fields
        self.player_name: str = "HECTOR"
        self.recent_game: str = "snake"
        self.total_play_time: float = 0.0
        self.high_scores: Dict[str, int] = {}
        self.games_played: Dict[str, int] = {}
        self.best_times: Dict[str, float] = {}
        self.play_times: Dict[str, float] = {}
        self.wins: Dict[str, int] = {}
        self.losses: Dict[str, int] = {}
        self.longest_rally: Dict[str, int] = {}
        self.highest_winning_score: Dict[str, int] = {}
        self.total_lines: Dict[str, int] = {}
        self.highest_level: Dict[str, int] = {}
        self.tetrises_cleared: Dict[str, int] = {}
        self.achievements: Dict[str, str] = {}
        self.settings: Dict[str, Any] = {}

        # Load save data from disk
        self.load()

    def _get_default_schema(self) -> Dict[str, Any]:
        """Returns clean default save data dictionary."""
        return {
            "player_name": "HECTOR",
            "recent_game": "snake",
            "total_play_time": 0.0,
            "high_scores": {},
            "games_played": {},
            "best_times": {},
            "play_times": {},
            "wins": {},
            "losses": {},
            "longest_rally": {},
            "highest_winning_score": {},
            "total_lines": {},
            "highest_level": {},
            "tetrises_cleared": {},
            "achievements": {},
            "settings": {},
        }

    def load(self) -> None:
        """
        Loads save data from disk with automatic corruption recovery.
        Falls back to backup file if primary file is corrupted.
        """
        data: Optional[Dict[str, Any]] = self._try_read_file(self._filepath)

        if data is None and os.path.exists(self._backup_path):
            logger.warning(f"Primary save file corrupted or unreadable. Attempting backup recovery from {self._backup_path}...")
            data = self._try_read_file(self._backup_path)
            if data is not None:
                logger.info("Backup save file successfully recovered.")

        if data is None:
            logger.info("Initializing fresh save schema defaults.")
            data = self._get_default_schema()

        self._populate_from_dict(data)

    def _try_read_file(self, path: str) -> Optional[Dict[str, Any]]:
        """Safely reads and parses a JSON file, returning None if corrupt or missing."""
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError, ValueError) as e:
            logger.warning(f"Failed to parse JSON save file '{path}': {e}")
        return None

    def _populate_from_dict(self, data: Dict[str, Any]) -> None:
        """Populates instance attributes from parsed data dictionary."""
        self.player_name = str(data.get("player_name", "HECTOR")).strip() or "HECTOR"
        self.recent_game = str(data.get("recent_game", "snake"))
        self.total_play_time = max(0.0, float(data.get("total_play_time", 0.0)))

        self.high_scores = {str(k): int(v) for k, v in data.get("high_scores", {}).items()}
        self.games_played = {str(k): int(v) for k, v in data.get("games_played", {}).items()}
        self.best_times = {str(k): float(v) for k, v in data.get("best_times", {}).items()}
        self.play_times = {str(k): float(v) for k, v in data.get("play_times", {}).items()}

        self.wins = {str(k): int(v) for k, v in data.get("wins", {}).items()}
        self.losses = {str(k): int(v) for k, v in data.get("losses", {}).items()}
        self.longest_rally = {str(k): int(v) for k, v in data.get("longest_rally", {}).items()}
        self.highest_winning_score = {str(k): int(v) for k, v in data.get("highest_winning_score", {}).items()}

        self.total_lines = {str(k): int(v) for k, v in data.get("total_lines", {}).items()}
        self.highest_level = {str(k): int(v) for k, v in data.get("highest_level", {}).items()}
        self.tetrises_cleared = {str(k): int(v) for k, v in data.get("tetrises_cleared", {}).items()}
        self.achievements = {str(k): str(v) for k, v in data.get("achievements", {}).items()}

        if isinstance(data.get("settings"), dict):
            self.settings = data["settings"]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes instance attributes into dictionary representation."""
        return {
            "player_name": self.player_name,
            "recent_game": self.recent_game,
            "total_play_time": round(self.total_play_time, 1),
            "high_scores": self.high_scores,
            "games_played": self.games_played,
            "best_times": {k: round(v, 1) for k, v in self.best_times.items()},
            "play_times": {k: round(v, 1) for k, v in self.play_times.items()},
            "wins": self.wins,
            "losses": self.losses,
            "longest_rally": self.longest_rally,
            "highest_winning_score": self.highest_winning_score,
            "total_lines": self.total_lines,
            "highest_level": self.highest_level,
            "tetrises_cleared": self.tetrises_cleared,
            "achievements": self.achievements,
            "settings": self.settings,
        }

    def save(self) -> None:
        """
        Executes atomic file save and updates backup copy.
        Prevents zero-byte corruption during power interruptions.
        """
        data = self.to_dict()

        dir_name = os.path.dirname(self._filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        try:
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                json.dump(data, tf, indent=2)
                temp_name = tf.name

            os.replace(temp_name, self._filepath)

            try:
                shutil.copy2(self._filepath, self._backup_path)
            except Exception as e:
                logger.debug(f"Could not create backup save file: {e}")

        except Exception as e:
            logger.error(f"Failed to execute atomic save write: {e}")

    # Game Stats API
    def record_game_start(self, game_id: str) -> None:
        """Records launching of a game session."""
        clean_id = game_id.strip().lower()
        self.recent_game = clean_id
        self.games_played[clean_id] = self.games_played.get(clean_id, 0) + 1
        self.games_played["total"] = self.games_played.get("total", 0) + 1
        self.save()

    def record_game_session(
        self, game_id: str, score: int, duration_sec: float
    ) -> bool:
        """
        Records completed generic game session stats.

        Args:
            game_id: Unique string game identifier.
            score: Game score achieved.
            duration_sec: Session survival duration in seconds.

        Returns:
            True if a new high score was set.
        """
        clean_id = game_id.strip().lower()
        is_new_high = False

        if clean_id not in self.games_played:
            self.games_played[clean_id] = 1

        current_high = self.high_scores.get(clean_id, 0)
        if score > current_high:
            self.high_scores[clean_id] = score
            is_new_high = True

        current_best = self.best_times.get(clean_id, 0.0)
        if duration_sec > current_best:
            self.best_times[clean_id] = duration_sec

        self.play_times[clean_id] = self.play_times.get(clean_id, 0.0) + duration_sec
        self.total_play_time += duration_sec

        self.save()
        return is_new_high

    def record_pong_session(
        self, p1_score: int, p2_score: int, duration_sec: float, rally_count: int
    ) -> bool:
        """
        Records completed Pong session stats.

        Args:
            p1_score: Player 1 score achieved.
            p2_score: Player 2 / AI score achieved.
            duration_sec: Session duration in seconds.
            rally_count: Longest rally achieved during match.

        Returns:
            True if Player 1 won the match.
        """
        game_id = "pong"
        if game_id not in self.games_played:
            self.games_played[game_id] = 1

        p1_won = p1_score > p2_score

        if p1_won:
            self.wins[game_id] = self.wins.get(game_id, 0) + 1
            winning_score = p1_score
        else:
            self.losses[game_id] = self.losses.get(game_id, 0) + 1
            winning_score = p2_score

        if winning_score > self.highest_winning_score.get(game_id, 0):
            self.highest_winning_score[game_id] = winning_score

        if rally_count > self.longest_rally.get(game_id, 0):
            self.longest_rally[game_id] = rally_count

        self.play_times[game_id] = self.play_times.get(game_id, 0.0) + duration_sec
        self.total_play_time += duration_sec

        self.save()
        return p1_won

    def record_tetris_session(
        self, score: int, lines_cleared: int, level: int, tetrises_count: int, duration_sec: float
    ) -> bool:
        """
        Records completed Tetris session stats.

        Args:
            score: Final score achieved.
            lines_cleared: Total lines cleared during session.
            level: Highest level reached.
            tetrises_count: Number of 4-line Tetris clears executed.
            duration_sec: Session duration in seconds.

        Returns:
            True if a new high score was set.
        """
        game_id = "tetris"
        if game_id not in self.games_played:
            self.games_played[game_id] = 1

        is_new_high = False

        current_high = self.high_scores.get(game_id, 0)
        if score > current_high:
            self.high_scores[game_id] = score
            is_new_high = True

        self.total_lines[game_id] = self.total_lines.get(game_id, 0) + lines_cleared
        
        current_lvl = self.highest_level.get(game_id, 1)
        if level > current_lvl:
            self.highest_level[game_id] = level

        self.tetrises_cleared[game_id] = self.tetrises_cleared.get(game_id, 0) + tetrises_count

        current_best = self.best_times.get(game_id, 0.0)
        if duration_sec > current_best:
            self.best_times[game_id] = duration_sec

        self.play_times[game_id] = self.play_times.get(game_id, 0.0) + duration_sec
        self.total_play_time += duration_sec

        self.save()
        return is_new_high

    def get_high_score(self, game_id: str) -> int:
        """Retrieves high score for a game ID."""
        return self.high_scores.get(game_id.strip().lower(), 0)

    def get_games_played(self, game_id: str) -> int:
        """Retrieves games played count for a game ID."""
        return self.games_played.get(game_id.strip().lower(), 0)

    def get_wins(self, game_id: str) -> int:
        """Retrieves win count for a game ID."""
        return self.wins.get(game_id.strip().lower(), 0)

    def get_losses(self, game_id: str) -> int:
        """Retrieves loss count for a game ID."""
        return self.losses.get(game_id.strip().lower(), 0)

    def get_longest_rally(self, game_id: str) -> int:
        """Retrieves longest rally for a game ID."""
        return self.longest_rally.get(game_id.strip().lower(), 0)

    def get_total_lines(self, game_id: str = "tetris") -> int:
        """Retrieves total lines cleared for a game ID."""
        return self.total_lines.get(game_id.strip().lower(), 0)

    def get_highest_level(self, game_id: str = "tetris") -> int:
        """Retrieves highest level reached for a game ID."""
        return self.highest_level.get(game_id.strip().lower(), 1)

    def get_tetrises(self, game_id: str = "tetris") -> int:
        """Retrieves total 4-line Tetris clears count for a game ID."""
        return self.tetrises_cleared.get(game_id.strip().lower(), 0)

    def get_best_time(self, game_id: str) -> float:
        """Retrieves best survival time for a game ID."""
        return self.best_times.get(game_id.strip().lower(), 0.0)

    def get_recent_game(self) -> str:
        """Retrieves ID of most recently played game."""
        return self.recent_game

    def set_player_name(self, name: str) -> None:
        """Updates active player profile name."""
        clean_name = name.strip()
        if clean_name:
            self.player_name = clean_name
            self.save()

    def reset_game_stats(self, game_id: Optional[str] = None) -> None:
        """Resets statistics for a specific game or all games."""
        if game_id:
            clean_id = game_id.strip().lower()
            self.high_scores.pop(clean_id, None)
            self.games_played.pop(clean_id, None)
            self.best_times.pop(clean_id, None)
            self.play_times.pop(clean_id, None)
            self.wins.pop(clean_id, None)
            self.losses.pop(clean_id, None)
            self.longest_rally.pop(clean_id, None)
            self.highest_winning_score.pop(clean_id, None)
            self.total_lines.pop(clean_id, None)
            self.highest_level.pop(clean_id, None)
            self.tetrises_cleared.pop(clean_id, None)
        else:
            self.high_scores.clear()
            self.games_played.clear()
            self.best_times.clear()
            self.play_times.clear()
            self.wins.clear()
            self.losses.clear()
            self.longest_rally.clear()
            self.highest_winning_score.clear()
            self.total_lines.clear()
            self.highest_level.clear()
            self.tetrises_cleared.clear()
            self.total_play_time = 0.0

        self.save()

    def get_total_games_played(self) -> int:
        """Returns the total number of game sessions played across all games."""
        return sum(v for k, v in self.games_played.items() if k != "total")

    def get_favorite_game(self) -> str:
        """Returns the name of the most played game based on session count."""
        if not self.games_played:
            return "Snake"
        fav_id = max(self.games_played, key=lambda k: self.games_played[k])
        names = {"snake": "Snake", "pong": "Pong", "tetris": "Tetris", "breakout": "Breakout"}
        return names.get(fav_id, fav_id.capitalize())

    def get_average_session_length(self) -> float:
        """Returns average session length in seconds."""
        total_sessions = self.get_total_games_played()
        if total_sessions <= 0:
            return 0.0
        return self.total_play_time / float(total_sessions)

    def unlock_achievement(self, achievement_id: str, timestamp: str = "") -> bool:
        """
        Unlocks an achievement if not already unlocked.

        Returns:
            True if achievement was newly unlocked, False if already unlocked.
        """
        clean_id = achievement_id.strip().lower()
        if clean_id not in self.achievements:
            import datetime
            ts = timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.achievements[clean_id] = ts
            self.save()
            return True
        return False

    def is_achievement_unlocked(self, achievement_id: str) -> bool:
        """Returns True if the given achievement has been unlocked."""
        return achievement_id.strip().lower() in self.achievements

    def reset_all(self) -> None:
        """Resets all save data and backups to clean schema defaults."""
        self._populate_from_dict(self._get_default_schema())
        self.save()
