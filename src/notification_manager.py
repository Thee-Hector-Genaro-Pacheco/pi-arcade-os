"""
Notification Manager module for Pi Arcade OS.

Renders animated popup toast notifications (Achievements, High Scores, Settings Saved, Audio Changes)
with auto-fade animation timers, accent borders, icon badges, and sound effect integration.
Supports Python 3.9+ typing.
"""

import logging
from typing import List, Optional, Tuple, Dict
import pygame

from src.config import SCREEN_WIDTH, SCREEN_HEIGHT

logger = logging.getLogger(__name__)


class Notification:
    """Represents a single active popup notification toast."""

    def __init__(
        self,
        title: str,
        message: str,
        icon: str = "🔔",
        border_color: Tuple[int, int, int] = (59, 130, 246),
        duration: float = 3.2,
    ) -> None:
        self.title: str = title
        self.message: str = message
        self.icon: str = icon
        self.border_color: Tuple[int, int, int] = border_color
        self.duration: float = max(0.5, float(duration))
        self.elapsed: float = 0.0

    @property
    def is_expired(self) -> bool:
        """Returns True if notification timer has exceeded duration."""
        return self.elapsed >= self.duration

    @property
    def alpha(self) -> int:
        """Calculates alpha transparency (0-255) for smooth fade-in and fade-out."""
        fade_time = 0.4
        if self.elapsed < fade_time:
            return int(255 * (self.elapsed / fade_time))
        remaining = self.duration - self.elapsed
        if remaining < fade_time:
            return int(255 * (remaining / fade_time))
        return 255


class NotificationManager:
    """Manages creation, queueing, timer updates, and rendering of toast notifications."""

    def __init__(self) -> None:
        self._notifications: List[Notification] = []

    def notify(
        self,
        title: str,
        message: str,
        icon: str = "🔔",
        color: Tuple[int, int, int] = (59, 130, 246),
        duration: float = 3.2,
    ) -> None:
        """
        Adds a new toast notification to the active queue.

        Args:
            title: Bold notification header.
            message: Detail description text.
            icon: Emoji icon badge.
            color: Accent RGB border color.
            duration: Display duration in seconds.
        """
        notif = Notification(
            title=title,
            message=message,
            icon=icon,
            border_color=color,
            duration=duration,
        )
        self._notifications.append(notif)
        logger.info(f"Notification Toast Queued: [{title}] {message}")

    def update(self, delta_time: float) -> None:
        """Updates animation timers and purges expired notifications."""
        for notif in self._notifications:
            notif.elapsed += delta_time

        self._notifications = [n for n in self._notifications if not n.is_expired]

    def draw(self, surface: pygame.Surface) -> None:
        """Renders active toast notifications in top-right screen area."""
        if not self._notifications:
            return

        font_title = pygame.font.SysFont("sans-serif", 16, bold=True)
        font_msg = pygame.font.SysFont("sans-serif", 14)

        toast_w, toast_h = 320, 64
        margin_right = 20
        start_y = 20

        # Limit max simultaneous visible toasts to 3
        visible_toasts = self._notifications[:3]

        for idx, notif in enumerate(visible_toasts):
            y_pos = start_y + idx * (toast_h + 10)
            x_pos = SCREEN_WIDTH - toast_w - margin_right

            # Create transparent surface for smooth alpha fading
            toast_surf = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
            alpha = notif.alpha

            # Card background and border
            r_bg = (15, 23, 42, min(240, alpha))
            r_border = (notif.border_color[0], notif.border_color[1], notif.border_color[2], alpha)

            card_rect = pygame.Rect(0, 0, toast_w, toast_h)
            pygame.draw.rect(toast_surf, r_bg, card_rect, border_radius=10)
            pygame.draw.rect(toast_surf, r_border, card_rect, width=2, border_radius=10)

            # Icon badge box
            icon_txt = font_title.render(notif.icon, True, (255, 255, 255))
            toast_surf.blit(icon_txt, (14, 18))

            # Header & Message text
            t_txt = font_title.render(notif.title, True, (248, 250, 252))
            m_txt = font_msg.render(notif.message, True, (148, 163, 184))

            toast_surf.blit(t_txt, (48, 12))
            toast_surf.blit(m_txt, (48, 34))

            # Bottom progress bar
            progress = max(0.0, 1.0 - (notif.elapsed / notif.duration))
            bar_w = int((toast_w - 20) * progress)
            if bar_w > 0:
                bar_rect = pygame.Rect(10, toast_h - 6, bar_w, 3)
                pygame.draw.rect(toast_surf, r_border, bar_rect, border_radius=2)

            surface.blit(toast_surf, (x_pos, y_pos))

    def clear(self) -> None:
        """Clears all active notification toasts."""
        self._notifications.clear()
