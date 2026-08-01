# Developer & Contributor Guide

Guidelines for contributing code, adding new arcade games, and maintaining engineering standards in **Pi Arcade OS**.

---

## Code Quality Standards

1. **Python Compatibility**: All code must compile and pass tests across Python 3.9 through Python 3.13.
2. **Type Annotations**: Annotate all function parameters and return types using standard `typing` primitives (`Optional`, `List`, `Dict`, `Tuple`, `Union`).
3. **Docstrings**: Include module, class, and method docstrings complying with PEP 257.
4. **Hardware Isolation**: Never import `gpiozero`, `RPLCD`, or hardware-access libraries at module top-level without wrapping in try-except fallback guards.
5. **Thread Safety**: Never mutate Pygame state directly inside background callbacks. Enqueue actions onto `InputManager`'s action queue.
6. **Atomic File Safety**: Persist configuration and stats through `SaveManager` to prevent zero-byte corruptions during sudden power cuts.

---

## Shared Platform Integration Standards

### 1. Save Subsystem (`SaveManager`)
All games must delegate score, wins, losses, total lines, levels, play time, and statistics recording to `SaveManager` (`src/save_manager.py`). Use helper methods such as `record_game_session()`, `record_pong_session()`, or `record_tetris_session()`.

### 2. Audio Engine (`AudioManager`)
Trigger non-blocking audio feedback by calling `audio_manager.play(SoundType.EVENT)`. Supported events include `SNAKE_EAT`, `PADDLE_HIT`, `TETRIS_ROTATE`, `TETRIS_LOCK`, `TETRIS_LINE_CLEAR`, `TETRIS_TETRIS_CLEAR`, `TETRIS_LEVEL_UP`, `PAUSE`, and `GAME_OVER`.

### 3. Display Integration (`DisplayManager`)
Update real-time 16x2 I2C LCD lines via `display_manager.show_tetris_score()`, `display_manager.show_pong_score()`, or `display_manager.write_lines()`. Display calls must fail gracefully without throwing uncaught exceptions.

### 4. Dynamic Theme Palettes (`SettingsManager`)
Sample surface and font colors from `settings_manager.get_theme_colors()` during `draw()` calls to support live theme palette switching (`Slate Dark`, `Cyberpunk Gold`, `Retro Monokai`, `Neon Synthwave`).

---

## Running Verification

Before submitting any changes, execute compilation and full unit tests:

```bash
# 1. Compile all source files
python3 -m compileall src tests

# 2. Run unit test suite
python3 -m unittest discover -s tests -p "test_*.py" -v
# or
pytest tests/ -v

# 3. Verify CLI diagnostics
python3 -m src.main --diagnostics

# 4. Verify runtime launch
python3 -m src.main
```
