# Troubleshooting & Problem Resolution Guide

Diagnostic strategies and common issue resolutions for **Pi Arcade OS**.

---

## 1. I2C LCD Display Issues

### Issue: LCD does not light up or display text (`OSError: [Errno 121] Remote I/O error`)

**Cause**: I2C bus disabled, incorrect bus address, or loose wiring.

**Resolution Steps**:
1. Verify physical wiring: VCC to Pin 2 (5V), GND to Pin 6, SDA to Pin 3, SCL to Pin 5.
2. Scan the I2C bus to confirm address:
   ```bash
   sudo i2cdetect -y 1
   ```
3. If no devices appear, re-enable I2C via `sudo raspi-config` -> **Interface Options** -> **I2C**.
4. Adjust the blue contrast potentiometer on the back of the PCF8574 I2C backpack using a small screwdriver if text appears blank.

---

## 2. GPIO Button Issues

### Issue: Buttons do not respond or trigger multiple unwanted inputs

**Cause**: Pin permission restrictions or missing contact debouncing.

**Resolution Steps**:
1. Ensure the user running the application is in the `gpio` and `input` groups:
   ```bash
   sudo usermod -aG gpio,input $USER
   ```
2. In [`src/hardware/input_manager.py`](file:///Users/hectorpacheco/.gemini/antigravity-ide/scratch/pi-arcade-os/src/hardware/input_manager.py), debouncing is enforced with `bounce_time=0.05` (50ms). If tactile switches are noisy, increase `bounce_time=0.08`.

---

## 3. Audio / Buzzer Issues

### Issue: No audio sound emitted from passive buzzer or ALSA warnings appear in console

**Cause**: System audio driver warnings or pin factory permission issues.

**Resolution Steps**:
1. Run `--diagnostics` mode to inspect audio status:
   ```bash
   python3 -m src.main --diagnostics
   ```
2. Disable Pygame mixer warnings by setting environment variable before launching:
   ```bash
   export SDL_AUDIODRIVER=dummy
   python3 -m src.main --gpio
   ```

---

## 4. Headless CI / macOS Execution

### Issue: `pygame.error: No available video device`

**Cause**: Running automated unit tests on a server without an active X11/Wayland display desktop environment.

**Resolution Steps**:
1. Ensure unit tests import headless environment variables prior to initializing Pygame:
   ```python
   import os
   os.environ["SDL_VIDEODRIVER"] = "dummy"
   os.environ["SDL_AUDIODRIVER"] = "dummy"
   ```
2. Execute tests via python unittest discovery:
   ```bash
   python3 -m unittest discover -s tests -p "test_*.py" -v
   ```
