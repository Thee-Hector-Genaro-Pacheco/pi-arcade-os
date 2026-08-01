# System Architecture - Pi Arcade OS

## Technical Architecture Overview

**Pi Arcade OS** is structured around clean separation of concerns, decoupling physical hardware I/O management from top-level application orchestration, system service managers, and game logic execution.

---

## Core Components Breakdown

### 1. Main Entry Point & Versioning (`src/`)
- **`src/main.py`**: Parses CLI flags (`--gpio`, `--no-lcd`, `--no-audio`, `--no-boot`, `--diagnostics`), runs `BootSequence` animation, initializes hardware subsystems and managers, and executes the primary 60 FPS update and render loop.
- **`src/version.py`**: Stores centralized version metadata (`VERSION = "1.0.0"`, `BUILD = "2026.08.01-RC1"`, `AUTHOR = "Hector Pacheco"`).

### 2. Operating System & Subsystem Managers (`src/`)
- **`BootSequence` (`src/boot_sequence.py`)**: Manages retro CRT terminal boot rendering displaying subsystem diagnostics checkmarks (`✓`), installed games catalog scanning, boot sound synthesis, and smooth alpha fade-out transition.
- **`AchievementManager` (`src/achievement_manager.py`)**: Manages 8 persistent arcade achievements (`First Launch`, `First Snake Game`, `First Pong Win`, `First Tetris Line`, `Score 100 in Snake`, `Play 10 Games`, `Play 100 Games`, `Arcade Veteran`). Persists state in `save_data.json` via `SaveManager` and fires fanfare sounds and notification toasts upon unlock.
- **`NotificationManager` (`src/notification_manager.py`)**: Manages smooth popup toast notifications in top-right screen space with custom badges, progress indicators, auto-fade timers, and audio triggers.
- **`SaveManager` (`src/save_manager.py`)**: Central atomic JSON save manager storing high scores, wins, losses, total lines cleared, highest level, tetrises count, achievements, best survival times, total play time, and aggregate statistics. Uses temporary file creation and `os.replace` for power-interruption safety, and automatically recovers from backup files (`save_data.json.bak`).
- **`SettingsManager` (`src/settings_manager.py`)**: Manages master, music, and effects volume, LCD brightness, theme palette selection, difficulty level, and control mappings. Dispatches live listener callbacks.

### 3. Hardware Abstraction Layer (`src/hardware/`)
- **`InputManager`**: Normalizes keyboard keypresses and physical Raspberry Pi GPIO button presses into unified `Action` enums (`UP`, `DOWN`, `LEFT`, `RIGHT`, `SELECT`, `BACK`, `RESTART`, `QUIT`). Button callbacks push events to a thread-safe `queue.Queue`.
- **`DisplayManager`**: Encapsulates Pygame screen rendering alongside real-time updates to a physical 16x2 I2C LCD character display (`0x27`). Try-except isolated to prevent LCD hardware failures from crashing the system.
- **`AudioManager`**: Synthesizes non-blocking sound waves for desktop Pygame mixer audio and passive GPIO buzzer tones (BCM 12) across 30 distinct sound effect events, including boot jingle, notification, achievement fanfare, menu move/back, Snake, Pong, and Tetris events.
- **`SystemDiagnostics`**: Gathers hardware subsystem status, platform details, Python/Pygame versions, screen specs, and registered game statistics into formatted reports.

### 4. Engine & Game Registry (`src/`)
- **`ArcadeGame` Interface (`src/game_interface.py`)**: Abstract base class enforcing properties (`name`, `description`, `is_finished`, metadata getters) and lifecycle methods (`start()`, `handle_event()`, `update()`, `draw()`, `reset()`, `cleanup()`).
- **`GameRegistry` (`src/game_registry.py`)**: Central registry managing `GameMetadata` dataclass instances and `ArcadeGame` classes. Supports previewing coming-soon titles safely without instantiating unwritten code.
- **`Launcher` (`src/launcher.py`)**: Top-level state machine (`MENU`, `PLAYING`, `SHOWING_NOTICE`, `SHOWING_SETTINGS`, `SHOWING_STATS`, `EXITING`). Renders animated menu cursor (`>`), glowing title banner, particle background, selection cards, hardware badges, modal overlays, Statistics Screen (`T`), and toast notifications.
