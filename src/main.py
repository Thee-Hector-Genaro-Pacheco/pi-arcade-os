"""
Main entry point for Pi Arcade OS.

Parses command line flags, initializes Pygame, SaveManager, SettingsManager, and hardware abstractions,
registers games, runs the main execution loop, and cleans up resources on exit.
Supports Python 3.9+ typing.

Usage:
    python3 -m src.main
    python3 -m src.main --gpio
    python3 -m src.main --diagnostics
    python3 -m src.main --no-lcd --no-audio
"""

import argparse
import logging
import sys
from typing import Optional, List
import pygame

from src.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WINDOW_TITLE
from src.save_manager import SaveManager
from src.settings_manager import SettingsManager
from src.game_registry import GameRegistry, GameMetadata
from src.games.snake_game import SnakeGame
from src.games.pong_game import PongGame
from src.hardware.input_manager import InputManager
from src.hardware.display import DisplayManager
from src.hardware.audio import AudioManager
from src.hardware.diagnostics import SystemDiagnostics
from src.launcher import Launcher, LauncherState

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses command-line arguments for Pi Arcade OS."""
    parser = argparse.ArgumentParser(description="Pi Arcade OS - Embedded Arcade Platform for Raspberry Pi 5")
    parser.add_argument(
        "--gpio",
        action="store_true",
        help="Enable Raspberry Pi GPIO button hardware input (BCM 27, 22, 23, 24)",
    )
    parser.add_argument(
        "--no-lcd",
        action="store_true",
        help="Disable 16x2 physical I2C LCD display output",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Disable passive GPIO buzzer audio feedback",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Print system diagnostics report and exit",
    )
    return parser.parse_args(args)


def main() -> None:
    """Main application execution sequence."""
    args = parse_args()

    logger.info("Initializing Pi Arcade OS...")
    logger.info(f"Hardware Flags: GPIO={args.gpio}, LCD={not args.no_lcd}, Audio={not args.no_audio}")

    # Initialize Unified Save Subsystem & Settings Manager
    save_manager = SaveManager()
    settings_manager = SettingsManager(save_manager=save_manager)

    # Initialize Hardware Managers
    input_manager = InputManager(enable_gpio=args.gpio)
    display_manager = DisplayManager(enable_lcd=not args.no_lcd)
    audio_manager = AudioManager(enable_audio=not args.no_audio)

    # Sync audio volume channels with loaded settings
    audio_manager.set_channel_volumes(
        master=settings_manager.master_volume,
        effects=settings_manager.effects_volume,
        music=settings_manager.music_volume,
    )

    # Register listener for live audio volume updates
    settings_manager.register_listener(
        lambda sm: audio_manager.set_channel_volumes(sm.master_volume, sm.effects_volume, sm.music_volume)
    )

    # Initialize Game Registry and register playable + coming-soon games
    registry = GameRegistry()

    # 1. Snake Game
    registry.register(
        "snake",
        SnakeGame,
        metadata=GameMetadata(
            id="snake",
            name="Snake",
            description="Classic arcade snake game. Eat food, grow, and avoid walls!",
            version="1.3.0",
            author="Hector Pacheco",
            icon="🐍",
            supports_gpio=True,
            supports_keyboard=True,
            supports_audio=True,
            supports_lcd=True,
            is_coming_soon=False,
        ),
    )

    # 2. Pong Game (Playable Sprint 3)
    registry.register(
        "pong",
        PongGame,
        metadata=GameMetadata(
            id="pong",
            name="Pong",
            description="Classic paddle game with local multiplayer and GPIO single-player mode.",
            version="1.0.0",
            author="Hector Pacheco",
            icon="🏓",
            supports_gpio=True,
            supports_keyboard=True,
            supports_audio=True,
            supports_lcd=True,
            is_coming_soon=False,
        ),
    )

    # Register preview coming-soon games for Sprint 3/4 infrastructure
    registry.register_coming_soon(
        GameMetadata(
            id="tetris",
            name="Tetris",
            description="Classic block-stacking puzzle game.",
            version="0.1.0-preview",
            author="Hector Pacheco",
            icon="🧱",
            supports_gpio=True,
            supports_keyboard=True,
            supports_audio=True,
            supports_lcd=True,
            is_coming_soon=True,
            estimated_release="Sprint 4",
        )
    )
    registry.register_coming_soon(
        GameMetadata(
            id="breakout",
            name="Breakout",
            description="Brick-busting arcade challenge.",
            version="0.1.0-preview",
            author="Hector Pacheco",
            icon="🧱",
            supports_gpio=True,
            supports_keyboard=True,
            supports_audio=True,
            supports_lcd=True,
            is_coming_soon=True,
            estimated_release="Sprint 4",
        )
    )

    # Handle CLI diagnostics request
    if args.diagnostics:
        diagnostics = SystemDiagnostics(
            registry=registry,
            input_manager=input_manager,
            display_manager=display_manager,
            audio_manager=audio_manager,
        )
        print(diagnostics.generate_report())
        input_manager.cleanup()
        display_manager.cleanup()
        audio_manager.cleanup()
        return

    # Initialize Pygame engine
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    # Create Launcher Controller
    launcher = Launcher(
        registry=registry,
        display_manager=display_manager,
        audio_manager=audio_manager,
        settings_manager=settings_manager,
        save_manager=save_manager,
    )

    running = True
    try:
        while running and launcher.state != LauncherState.EXITING:
            delta_time = clock.tick(FPS) / 1000.0  # Seconds per frame

            # 1. Process Pygame Window Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                # Handle S key shortcut for Settings view
                if event.type == pygame.KEYDOWN and event.key == pygame.K_s and launcher.state == LauncherState.MENU:
                    launcher.open_settings_view()
                    continue

                # Pass keyboard events through input manager
                action = input_manager.process_pygame_event(event)
                if action:
                    launcher.handle_action(action)
                else:
                    launcher.handle_pygame_event(event)

            # 2. Process pending GPIO actions from thread-safe queue
            while True:
                gpio_action = input_manager.get_next_action()
                if not gpio_action:
                    break
                launcher.handle_action(gpio_action)

            # 3. Update active state & render frame
            launcher.update(delta_time)
            launcher.draw(screen)
            pygame.display.flip()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected. Exiting Pi Arcade OS...")
    except Exception as e:
        logger.exception(f"Unhandled exception in main loop: {e}")
    finally:
        logger.info("Cleaning up resources...")
        launcher.cleanup()
        input_manager.cleanup()
        display_manager.cleanup()
        audio_manager.cleanup()
        pygame.quit()
        logger.info("Pi Arcade OS shut down cleanly.")


if __name__ == "__main__":
    main()
