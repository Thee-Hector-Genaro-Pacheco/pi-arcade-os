# Development Roadmap - Pi Arcade OS

Detailed multi-sprint timeline for evolving **Pi Arcade OS** into a portfolio retro arcade platform.

---

## Sprint 1: Launcher Engine & Snake Game (Completed)
- [x] Create core application structure (`src/`, `tests/`, `docs/`).
- [x] Implement abstract `ArcadeGame` base class contract.
- [x] Implement dynamic `GameRegistry` with string ID lookup and duplicate protection.
- [x] Implement `Launcher` state machine (`MENU`, `PLAYING`, `EXITING`) with menu wrapping.
- [x] Build hardware abstraction layers (`InputManager`, `DisplayManager`, `AudioManager`).
- [x] Port Snake into `ArcadeGame` format with score/high-score tracking and grid collisions.
- [x] Write hardware-isolated headless unit test suite with 100% test coverage.

---

## Sprint 2: Production Launcher & Portfolio Hardening (Completed)
- [x] Fix Python 3.9+ typing and compatibility issues.
- [x] Polish Launcher UI with header banner, animated pulsing cursor, particles, and coming-soon previews.
- [x] Expand `GameMetadata` dataclass infrastructure (author, version, hardware capabilities).
- [x] Build `SystemDiagnostics` subsystem (`--diagnostics`).
- [x] Expand documentation suite (`docs/architecture.md`, `docs/developer-guide.md`, `docs/adding-a-game.md`).

---

## Sprint 2.3: Settings Subsystem & Theme Engine (Completed)
- [x] Build `SettingsManager` with persistent JSON storage (`settings.json`).
- [x] Implement live RGB color theme palettes (`Slate Dark`, `Cyberpunk Gold`, `Retro Monokai`, `Neon Synthwave`).
- [x] Implement multi-channel volume scaling (Master, Music, Effects) and live audio callbacks.
- [x] Interactive in-menu Settings modal overlay (`S` key shortcut).

---

## Sprint 2.4: Persistent Save System (Completed)
- [x] Build central, crash-resilient `SaveManager` (`src/save_manager.py`).
- [x] Atomic file writes using temporary file creation and `os.replace` to prevent zero-byte corruptions.
- [x] Automatic backup recovery from `save_data.json.bak`.
- [x] Track high scores, games played, total play time, best survival times, recent game, and player profile.

---

## Sprint 3: Pong & Beatable AI Opponent (Completed)
- [x] Add `PongGame` implementation adhering to `ArcadeGame` interface (`ID: pong`, `v1.0.0`).
- [x] 2-Player Local Keyboard mode (`W`/`S` vs. `Up`/`Down`) and Single-Player GPIO Arcade mode.
- [x] Beatable AI opponent scaling with `Easy`, `Normal`, and `Hard` difficulty settings.
- [x] Dynamic ball physics, top/bottom wall bounces, and impact angle calculations.
- [x] Real-time score, pause, and victory rendering on 16x2 LCD display (`P1:X  P2:Y`).
- [x] 7 new sound synthesis events (`PADDLE_HIT`, `WALL_BOUNCE`, `POINT_SCORED`, `MATCH_START`, `PAUSE`, `VICTORY`, `DEFEAT`).
- [x] Full unit test suite in `tests/test_pong.py`.

---

## Sprint 4: Tetris & Puzzle Engine
- [ ] Add `TetrisGame` implementation adhering to `ArcadeGame` contract.
- [ ] Block rotation, line clearing, ghost piece, and level progression.
- [ ] High score and lines cleared tracking in `SaveManager`.

---

## Sprint 5: Raspberry Pi Autostart & Kiosk Mode
- [ ] Systemd service file definition (`pi-arcade.service`).
- [ ] Custom Plymouth boot splash screen for Raspberry Pi OS.
- [ ] Read-only root filesystem configuration for power-cut safety.
- [ ] Hardware shutdown / reboot menu entry.

---

## Sprint 6: Web Portfolio Demo & Emulation
- [ ] Pygbag / WebAssembly compilation of Pi Arcade OS.
- [ ] Interactive browser-based portfolio showcase on GitHub Pages.
- [ ] Virtual on-screen Raspberry Pi controller overlay.
