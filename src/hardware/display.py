"""
Display Manager module for Pi Arcade OS.

Provides physical 16x2 I2C LCD hardware abstraction with safe fallbacks and mock support.
Displays launcher menus, score lines, and system diagnostics without blocking the Pygame thread.
Supports Python 3.9+ typing.
"""

import logging
import threading
from typing import Optional

from src.config import LCD_I2C_ADDRESS, LCD_COLS, LCD_ROWS

logger = logging.getLogger(__name__)

# Optional import of RPLCD for physical I2C LCD display
try:
    from RPLCD.i2c import CharLCD
    RPLCD_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.info(f"RPLCD hardware package unavailable ({e}). LCD running in Mock mode.")
    CharLCD = None
    RPLCD_AVAILABLE = False


class DisplayManager:
    """Manages 16x2 I2C physical LCD display hardware with thread safety and mock fallbacks."""

    def __init__(self, enable_lcd: bool = True, i2c_address: int = LCD_I2C_ADDRESS) -> None:
        """
        Initializes DisplayManager.

        Args:
            enable_lcd: If True, attempts physical LCD hardware initialization.
            i2c_address: I2C bus address (default 0x27).
        """
        self._enabled: bool = enable_lcd
        self._address: int = i2c_address
        self._lcd: Optional[object] = None
        self._lock: threading.Lock = threading.Lock()
        self._line1: str = ""
        self._line2: str = ""

        if enable_lcd:
            self._init_lcd_hardware()

    def _init_lcd_hardware(self) -> None:
        """Attempts to initialize RPLCD CharLCD instance."""
        if not RPLCD_AVAILABLE:
            logger.info("LCD disabled or RPLCD package missing.")
            return

        try:
            self._lcd = CharLCD(
                i2c_expander="PCF8574",
                address=self._address,
                port=1,
                cols=LCD_COLS,
                rows=LCD_ROWS,
                dotsize=8,
            )
            self._lcd.clear()
            logger.info(f"16x2 I2C LCD initialized at address {hex(self._address)}.")
        except Exception as e:
            logger.warning(f"Failed to initialize physical LCD ({e}). Falling back to Mock mode.")
            self._lcd = None

    @property
    def is_lcd_enabled(self) -> bool:
        """Returns True if physical LCD hardware is connected and active."""
        return self._enabled and self._lcd is not None

    def write_lines(self, line1: str, line2: str) -> None:
        """
        Writes two lines to the 16x2 LCD display, padded/truncated to 16 characters.

        Args:
            line1: First line text (max 16 chars).
            line2: Second line text (max 16 chars).
        """
        if not self._enabled:
            return

        formatted_l1 = f"{line1:<16}"[:16]
        formatted_l2 = f"{line2:<16}"[:16]

        with self._lock:
            self._line1 = formatted_l1
            self._line2 = formatted_l2

            if self._lcd:
                try:
                    self._lcd.home()
                    self._lcd.write_string(f"{formatted_l1}\n{formatted_l2}")
                except Exception as e:
                    logger.warning(f"LCD write error ({e}).")
            else:
                logger.debug(f"[LCD Mock] Line 1: '{formatted_l1}' | Line 2: '{formatted_l2}'")

    def show_launcher_menu(self, game_name: str) -> None:
        """Displays current launcher game selection on LCD."""
        self.write_lines("Pi Arcade OS", f"> {game_name}")

    def show_game_score(self, score: int, high_score: int) -> None:
        """Displays gameplay score on LCD."""
        self.write_lines(f"Score: {score}", f"High: {high_score}")

    def show_pong_score(self, p1_score: int, p2_score: int) -> None:
        """Displays active Pong game score on LCD."""
        self.write_lines(f"P1:{p1_score}  P2:{p2_score}", "First to 5")

    def show_pong_paused(self) -> None:
        """Displays Pong paused message on LCD."""
        self.write_lines("Pong Paused", "Press Resume")

    def show_pong_game_over(self, winner_name: str) -> None:
        """Displays Pong game over winner message on LCD."""
        self.write_lines(f"{winner_name} Wins", "R to Restart")

    def show_tetris_score(self, score: int, lines: int, level: int) -> None:
        """Displays Tetris score, lines, and level on LCD."""
        self.write_lines(f"Score: {score}", f"L:{lines} Lv:{level}")

    def show_tetris_paused(self) -> None:
        """Displays Tetris paused message on LCD."""
        self.write_lines("Tetris Paused", "Press Resume")

    def show_tetris_game_over(self, score: int) -> None:
        """Displays Tetris game over score on LCD."""
        self.write_lines("Game Over", f"Score: {score}")

    def show_tetris_new_high_score(self, score: int) -> None:
        """Displays Tetris new high score message on LCD."""
        self.write_lines("New High Score", f"Score: {score}")

    def clear(self) -> None:
        """Clears the LCD screen."""
        with self._lock:
            self._line1 = ""
            self._line2 = ""
            if self._lcd:
                try:
                    self._lcd.clear()
                except Exception as e:
                    logger.debug(f"Error clearing LCD: {e}")

    def cleanup(self) -> None:
        """Clears screen and releases hardware resources."""
        self.clear()
        with self._lock:
            if self._lcd:
                try:
                    self._lcd.close()
                except Exception as e:
                    logger.debug(f"Error closing LCD hardware: {e}")
            self._lcd = None
        logger.info("DisplayManager resources cleaned up.")
