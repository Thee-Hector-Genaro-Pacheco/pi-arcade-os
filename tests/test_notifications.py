"""
Unit test suite for NotificationManager in Pi Arcade OS.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import pygame

pygame.init()
pygame.display.set_mode((100, 100))

from src.notification_manager import NotificationManager, Notification


class TestNotificationManager(unittest.TestCase):
    """Unit tests for toast notification queueing, timers, auto-fade, and drawing."""

    def test_notification_object_initialization_and_alpha(self):
        n = Notification("Title", "Message", icon="🏆", duration=2.0)
        self.assertEqual(n.title, "Title")
        self.assertEqual(n.message, "Message")
        self.assertFalse(n.is_expired)
        n.elapsed = 0.2
        self.assertGreater(n.alpha, 0)

    def test_notification_manager_notify_queues_toast(self):
        nm = NotificationManager()
        nm.notify("Test Header", "Test Detail", icon="⭐")
        self.assertEqual(len(nm._notifications), 1)
        self.assertEqual(nm._notifications[0].title, "Test Header")

    def test_notification_manager_update_timer_and_expiration(self):
        nm = NotificationManager()
        nm.notify("Short", "Quick toast", duration=1.0)
        self.assertEqual(len(nm._notifications), 1)

        nm.update(0.5)
        self.assertEqual(len(nm._notifications), 1)

        nm.update(0.6)  # Elapsed 1.1s > 1.0s
        self.assertEqual(len(nm._notifications), 0)

    def test_notification_manager_clear(self):
        nm = NotificationManager()
        nm.notify("T1", "M1")
        nm.notify("T2", "M2")
        self.assertEqual(len(nm._notifications), 2)
        nm.clear()
        self.assertEqual(len(nm._notifications), 0)

    def test_notification_manager_draw_headless(self):
        nm = NotificationManager()
        nm.notify("Visual Test", "Drawing toast notification", icon="🎨")
        surface = pygame.Surface((800, 600))
        nm.draw(surface)  # Should draw cleanly without error


if __name__ == "__main__":
    unittest.main()
