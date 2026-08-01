# Pi Arcade OS

```
  ██████╗ ██╗     █████╗ ███╗   ██╗███████╗████████╗
  ██╔══██╗██║    ██╔══██╗████╗  ██║██╔════╝╚══██╔══╝
  ██████╔╝██║    ███████║██╔██╗ ██║█████╗     ██║   
  ██╔═══╝ ██║    ██╔══██║██║╚██╗██║██╔══╝     ██║   
  ██║     ██║    ██║  ██║██║ ╚████║███████╗   ██║   
  ╚═╝     ╚═╝    ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   
       E M B E D D E D   A R C A D E   O S          
```

**Embedded Arcade Operating System & Multi-Game Platform for Raspberry Pi 5**

Author: **Hector Pacheco**

---

## Portfolio Showcase & Executive Overview

**Pi Arcade OS** is an object-oriented, hardware-decoupled retro arcade operating system built in Python 3.9–3.13 and Pygame. Designed for embedded deployment on Raspberry Pi 5 with custom physical GPIO controls, a 16x2 I2C LCD character display, and passive buzzer audio output, the OS abstracts hardware interactions to provide a modular multi-game platform.

Featuring **Snake** and **Pong** as fully playable platform games, **SaveManager** with atomic JSON writes and corruption recovery, live color palette **Theme Engine**, and beatable single-player **AI Opponent**, the platform supports both 2-Player Local Keyboard mode and 4-button Raspberry Pi GPIO Arcade mode.

---

## 📄 Resume Bullet Point

> **Embedded Software Engineer / Python Developer**
> - Designed and developed **Pi Arcade OS**, a modular embedded arcade platform for Raspberry Pi 5 using Python 3.13, Pygame, and `gpiozero`. Implemented thread-safe input queuing (`queue.Queue`), hardware service abstractions for 16x2 I2C LCD displays and non-blocking buzzer tones, an extensible game registry pattern, beatable AI opponent algorithms, atomic JSON save file recovery, and a 100% hardware-isolated test suite.

---

## Key Technical Features

- **Decoupled Architecture**: Game logic (`ArcadeGame`) is completely isolated from hardware input reading, display drivers, and audio synthesis.
- **Playable Games Catalog**: Includes **Snake** (`v1.3.0`) and **Pong** (`v1.0.0`) with local 2-player keyboard mode and single-player GPIO AI mode.
- **Beatable AI Opponent**: Dynamic AI with difficulty levels (`Easy`, `Normal`, `Hard`), reaction delays, target error variation, and smooth paddle tracking.
- **Crash-Resilient SaveManager**: Atomic file writes via temporary files and `os.replace` prevent zero-byte corruptions. Automatic backup recovery (`save_data.json.bak`) restores state cleanly.
- **Interactive Settings & Live Themes**: Live theme palette switching (`Slate Dark`, `Cyberpunk Gold`, `Retro Monokai`, `Neon Synthwave`), multi-channel volume sliders, difficulty, and control schemes.
- **Thread-Safe Input Queuing**: Multi-threaded `gpiozero` physical button callbacks enqueue actions into a thread-safe `queue.Queue`, eliminating thread race conditions on Pygame's main loop.
- **Dual Display Output**: High-resolution desktop Pygame rendering synced with real-time score and navigation output on a physical 16x2 I2C character LCD (`0x27`).
- **Non-Blocking Tone Synthesis**: Asynchronous daemon threads trigger passive buzzer audio feedback without dropping frames from the 60 FPS rendering pipeline.
- **Graceful Hardware Degradation**: Runs seamlessly in silent keyboard-only mode on macOS development environments or headless CI runners.

---

## Hardware Pin Mapping (Raspberry Pi 5)

| Subsystem | Function | BCM GPIO | Physical Header Pin | Wiring / Color |
| :--- | :--- | :--- | :--- | :--- |
| **Control Button** | UP / P1 Paddle Up | `GPIO27` | Pin 13 | Orange wire |
| **Control Button** | DOWN / P1 Paddle Down | `GPIO22` | Pin 15 | Yellow wire |
| **Control Button** | LEFT / Pause | `GPIO23` | Pin 16 | Blue wire |
| **Control Button** | RIGHT / Select / Restart | `GPIO24` | Pin 18 | Green wire |
| **Buttons Common** | Ground | - | Pin 14 | Ground wire |
| **16x2 I2C LCD** | VCC (+5V Power) | - | Pin 2 | Power wire |
| **16x2 I2C LCD** | Ground | - | Pin 6 | Ground wire |
| **16x2 I2C LCD** | SDA (Data) | `GPIO02` | Pin 3 | Data Line |
| **16x2 I2C LCD** | SCL (Clock) | `GPIO03` | Pin 5 | Clock Line |
| **Passive Buzzer**| Audio Signal | `GPIO12` | Pin 32 | PWM Output |
| **Passive Buzzer**| Ground | - | Pin 34 | Ground wire |

*I2C Address:* `0x27`

---

## Directory Structure

```
pi-arcade-os/
├── README.md
├── requirements.txt
├── save_data.json
├── save_data.json.bak
├── settings.json
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── adding-a-game.md
│   └── developer-guide.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── launcher.py
│   ├── save_manager.py
│   ├── settings_manager.py
│   ├── game_registry.py
│   ├── game_interface.py
│   ├── games/
│   │   ├── __init__.py
│   │   ├── snake_game.py
│   │   └── pong_game.py
│   └── hardware/
│       ├── __init__.py
│       ├── input_manager.py
│       ├── display.py
│       ├── audio.py
│       └── diagnostics.py
└── tests/
    ├── __init__.py
    ├── test_audio.py
    ├── test_game_registry.py
    ├── test_launcher.py
    ├── test_save_manager.py
    ├── test_settings.py
    └── test_pong.py
```

---

## Quick Start & Commands

### 1. Run Desktop / macOS Keyboard Mode
```bash
python3 -m src.main
```

### 2. Run Raspberry Pi Hardware Mode
```bash
python3 -m src.main --gpio
```

### 3. Run System Diagnostics Report
```bash
python3 -m src.main --diagnostics
```

### 4. Run Test Suite
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
# or
pytest tests/ -v
```

---

## Controls Summary

| Mode / Game | Action | Keyboard Control | GPIO Button Control |
| :--- | :--- | :--- | :--- |
| **Launcher** | Navigate Menu | `Up` / `Down` or `W` / `S` | `GPIO27` / `GPIO22` |
| **Launcher** | Launch Selected | `Enter` / `Space` or `Right` | `GPIO24` |
| **Launcher** | Settings Menu | `S` Key | - |
| **Snake** | Change Direction | `Arrows` / `WASD` | `GPIO27`, `22`, `23`, `24` |
| **Pong (2P)** | Player 1 Paddle | `W` / `S` | `GPIO27` / `GPIO22` |
| **Pong (2P)** | Player 2 Paddle | `Up` / `Down` | (AI in GPIO mode) |
| **Pong** | Pause Match | `P` Key | `GPIO23` |
| **Pong** | Restart Match | `R` Key | `GPIO24` |
| **All Games** | Return to Menu | `ESC` Key | `GPIO23` (Hold/Back) |

---

## Roadmap

- [x] **Sprint 1**: Launcher Engine + Snake + Hardware Abstractions
- [x] **Sprint 2**: Production Launcher Polish + Registry Metadata + System Diagnostics
- [x] **Sprint 2.3**: Settings Subsystem & Theme Palette Engine
- [x] **Sprint 2.4**: Atomic Save System & Corruption Recovery
- [x] **Sprint 3**: Pong Game + AI Opponent + Sound & LCD Extensions
- [ ] **Sprint 4**: Tetris Game Implementation
- [ ] **Sprint 5**: Raspberry Pi Systemd Kiosk Autostart
