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

## Sprint 5: Tetris & 7-Bag Randomizer Engine (Completed)
- [x] Add `TetrisGame` implementation adhering to `ArcadeGame` contract (`ID: tetris`, `v1.0.0`).
- [x] 10x20 visible grid playfield with centered board rendering.
- [x] Standard 7-bag randomizer piece generation system (`I`, `O`, `T`, `S`, `Z`, `J`, `L`).
- [x] Clockwise & counterclockwise rotation with SRS-inspired wall kick tests.
- [x] Active piece movement, soft drop, hard drop, lock delay, and ghost piece projection.
- [x] Line clearing flash animations, 4-line Tetris clears, scoring table, and level progression.
- [x] SaveManager schema extensions for high scores, lines cleared, highest level, and tetrises count.
- [x] Real-time 16x2 I2C LCD lines (`Score: X`, `L:Y Lv:Z`, `Tetris Paused`, `Game Over`).
- [x] 9 new sound synthesis events.

---

## Sprint 5 (OS Upgrade): Arcade Operating System Experience (Completed)
- [x] Animated CRT Terminal Boot Sequence (`BootSequence`) with checkmark diagnostics (`✓`).
- [x] Persistent Achievement System (`AchievementManager`) with 8 unlockable badges saved in `save_data.json`.
- [x] Toast Notification System (`NotificationManager`) with auto-fading popups, progress slides, and custom icon badges.
- [x] Standalone System & Gameplay Statistics Screen (`SHOWING_STATS`, `T` key shortcut).
- [x] Version Manager (`version.py`) storing version, build ID, author, and release info.
- [x] 30 PCM synthesized sound events across Pygame mixer and GPIO passive buzzer.
- [x] Test suite expansion to 76 passing unit tests.

---

## Sprint 6: Breakout & Brick-Buster Engine
- [ ] Add `BreakoutGame` implementation adhering to `ArcadeGame` contract.
- [ ] Paddle control, ball reflection physics, brick grid destruction, power-ups, and level clear transitions.
- [ ] High score and bricks destroyed statistics in `SaveManager`.

---

## Sprint 7: Raspberry Pi Autostart & Kiosk Mode
- [ ] Systemd service file definition (`pi-arcade.service`).
- [ ] Custom Plymouth boot splash screen for Raspberry Pi OS.
- [ ] Read-only root filesystem configuration for power-cut safety.
- [ ] Hardware shutdown / reboot menu entry.
