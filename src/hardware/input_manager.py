"""
Input Manager module for Pi Arcade OS.

Handles keyboard inputs and optional gpiozero GPIO button inputs,
enqueuing normalized Action events onto a thread-safe Queue for consumption
by the Pygame main loop.
"""

import logging
import queue
from typing import Optional, List
import pygame
from src.config import (
    Action,
    GPIO_PIN_UP,
    GPIO_PIN_DOWN,
    GPIO_PIN_LEFT,
    GPIO_PIN_RIGHT,
)

logger = logging.getLogger(__name__)

# Optional import of gpiozero for Raspberry Pi hardware
try:
    from gpiozero import Button
    GPIO_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.info(f"GPIO functionality unavailable ({e}). Running in Keyboard-only mode.")
    Button = None
    GPIO_AVAILABLE = False


class InputManager:
    """Manages input events from Pygame keyboard and hardware GPIO buttons."""

    def __init__(self, enable_gpio: bool = False) -> None:
        """
        Initializes the InputManager.

        Args:
            enable_gpio: If True, attempts to initialize Raspberry Pi GPIO buttons.
        """
        self._action_queue: queue.Queue[Action] = queue.Queue()
        self._gpio_enabled: bool = False
        self._buttons: List = []

        if enable_gpio:
            self._init_gpio()

    def _init_gpio(self) -> None:
        """Initializes GPIO buttons if hardware and libraries are available."""
        if not GPIO_AVAILABLE:
            logger.warning("GPIO requested but gpiozero is not available. Continuing in Keyboard-only mode.")
            return

        try:
            # Physical button setup with internal pull-up resistor
            self._btn_up = Button(GPIO_PIN_UP, pull_up=True, bounce_time=0.05)
            self._btn_down = Button(GPIO_PIN_DOWN, pull_up=True, bounce_time=0.05)
            self._btn_left = Button(GPIO_PIN_LEFT, pull_up=True, bounce_time=0.05)
            self._btn_right = Button(GPIO_PIN_RIGHT, pull_up=True, bounce_time=0.05)

            # Assign thread-safe callbacks that push to action queue
            self._btn_up.when_pressed = lambda: self._enqueue_action(Action.UP)
            self._btn_down.when_pressed = lambda: self._enqueue_action(Action.DOWN)
            self._btn_left.when_pressed = lambda: self._enqueue_action(Action.LEFT)
            self._btn_right.when_pressed = lambda: self._enqueue_action(Action.RIGHT)

            self._buttons = [self._btn_up, self._btn_down, self._btn_left, self._btn_right]
            self._gpio_enabled = True
            logger.info("GPIO Input Manager successfully initialized on pins 27, 22, 23, 24.")
        except Exception as e:
            logger.error(f"Failed to initialize GPIO pins ({e}). Falling back to Keyboard-only mode.")
            self._gpio_enabled = False
            self.cleanup()

    def _enqueue_action(self, action: Action) -> None:
        """Thread-safe callback to place an action into the input queue."""
        logger.debug(f"GPIO Action enqueued: {action}")
        self._action_queue.put(action)

    def process_pygame_event(self, event: pygame.event.Event) -> Optional[Action]:
        """
        Converts a Pygame KEYDOWN event into a normalized system Action.

        Args:
            event: Pygame Event object.

        Returns:
            Mapped Action enum or None if the event key is unmapped.
        """
        if event.type != pygame.KEYDOWN:
            return None

        action: Optional[Action] = None

        if event.key in (pygame.K_UP, pygame.K_w):
            action = Action.UP
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            action = Action.DOWN
        elif event.key in (pygame.K_LEFT, pygame.K_a):
            action = Action.LEFT
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            action = Action.RIGHT
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            action = Action.SELECT
        elif event.key in (pygame.K_ESCAPE, pygame.K_q):
            action = Action.BACK
        elif event.key == pygame.K_r:
            action = Action.RESTART

        return action

    def get_next_action(self) -> Optional[Action]:
        """
        Retrieves the next pending action from the queue, if available.

        Returns:
            Action enum if present, otherwise None.
        """
        try:
            return self._action_queue.get_nowait()
        except queue.Empty:
            return None

    @property
    def is_gpio_enabled(self) -> bool:
        """Returns True if physical GPIO buttons are active."""
        return self._gpio_enabled

    def cleanup(self) -> None:
        """Safely releases GPIO resources."""
        if self._buttons:
            for btn in self._buttons:
                try:
                    btn.close()
                except Exception as e:
                    logger.debug(f"Error closing button pin: {e}")
            self._buttons.clear()
        self._gpio_enabled = False
        logger.info("InputManager hardware resources cleaned up.")
