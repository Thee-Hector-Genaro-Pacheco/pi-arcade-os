"""
Main entry point for Pi Arcade OS.

Parses command line arguments, initializes hardware subsystems (InputManager, DisplayManager, AudioManager),
configures GameRegistry with playable games (Snake, Pong, Tetris) and coming-soon previews (Breakout),
initializes Launcher state machine, and runs the primary 60 FPS update and render loop.
Supports Python 3.9+ typing.
"""

import argparse
import logging
import sys
from typing import Optional
import pygame

from src.config import FPS, SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE, Action
from src.save_manager import SaveManager
from src.settings_manager import SettingsManager
from src.game_registry import GameRegistry, GameMetadata
from src.games.snake_game import SnakeGame
from src.games.pong_game import PongGame
from src.games.tetris_game import TetrisGame
from src.hardware.input_manager import InputManager
from src.hardware.display import DisplayManager
from src.hardware.audio import AudioManager
from src.hardware.diagnostics import SystemDiagnostics
from src.launcher import Launcher, LauncherState

# Configure application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parses command line flags."""
    parser = argparse.ArgumentParser(
        description="Pi Arcade OS - Embedded Arcade Platform for Raspberry Pi 5"
    )
    parser.add_argument(
        "--gpio",
        action="store_true",
        help="Enable Raspberry Pi GPIO button inputs (BCM 27, 22, 23, 24)",
    )
    parser.add_argument(
        "--no-lcd",
        action="store_true",
        help="Disable physical 16x2 I2C LCD character display output",
    )
    parser.add_argument(
        "--no-audio",
        action="store_true",
        help="Disable audio engine (Pygame mixer and passive buzzer)",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Generate and print hardware subsystem diagnostics report and exit",
    )
    return parser.parse_args()


def main() -> None:
    """Primary application entry point and 60 FPS game loop."""
    args = parse_args()

    logger.info("Initializing Pi Arcade OS...")
    logger.info(f"Hardware Flags: GPIO={args.gpio}, LCD={not args.no_lcd}, Audio={not args.no_audio}")

    # 1. Initialize Pygame Video Subsystem
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    # 2. Initialize Central Save & Settings Managers
    save_manager = SaveManager()
    settings_manager = SettingsManager(save_manager=save_manager)

    # 3. Initialize Hardware Abstractions
    input_manager = InputManager(enable_gpio=args.gpio)
    display_manager = DisplayManager(enable_lcd=not args.no_lcd)
    audio_manager = AudioManager(
        enable_audio=not args.no_audio,
        volume=settings_manager.master_volume,
    )

    # Register volume listener with SettingsManager
    def on_settings_changed(sm: SettingsManager) -> None:
        audio_manager.set_channel_volumes(master=sm.master_volume, effects=sm.effects_volume, music=sm.music_volume)

    settings_manager.add_listener(on_settings_changed)

    # Apply initial channel volumes from settings
    audio_manager.set_channel_volumes(
        master=settings_manager.master_volume,
        effects=settings_manager.effects_volume,
        music=settings_manager.music_volume,
    )

    # 4. Initialize GameRegistry and Register Games
    registry = GameRegistry()

    # 1. Snake Game (Playable)
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

    # 3. Tetris Game (Playable Sprint 5)
    registry.register(
        "tetris",
        TetrisGame,
        metadata=GameMetadata(
            id="tetris",
            name="Tetris",
            description="Classic falling-block puzzle game with rotation, line clearing, level progression, and GPIO support.",
            version="1.0.0",
            author="Hector Pacheco",
            icon="🧱",
            supports_gpio=True,
            supports_keyboard=True,
            supports_audio=True,
            supports_lcd=True,
            is_coming_soon=False,
        ),
    )

    # 4. Breakout Game (Coming Soon)
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
            estimated_release="Sprint 6",
        )
    )

    # Handle Diagnostics Mode CLI Flag
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
        pygame.quit()
        sys.exit(0)

    # 5. Initialize Launcher Controller
    launcher = Launcher(
        registry=registry,
        display_manager=display_manager,
        audio_manager=audio_manager,
        settings_manager=settings_manager,
        save_manager=save_manager,
    )

    running = True

    # Main 60 FPS Event Loop
    try:
        while running:
            delta_time = clock.tick(FPS) / 1000.0  # Convert ms to seconds

            # Process Pygame Event Queue
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

            # Process Asynchronous GPIO Queue Events
            while True:
                gpio_action = input_manager.get_next_action()
                if not gpio_action:
                    break
                launcher.handle_action(gpio_action)

            # Check if launcher transitioned to EXITING state
            if launcher.state == LauncherState.EXITING:
                running = False
                break

            # Update launcher/active game state
            launcher.update(delta_time)

            # Render active frame
            launcher.draw(screen)
            pygame.display.flip()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt detected. Exiting Pi Arcade OS...")
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
