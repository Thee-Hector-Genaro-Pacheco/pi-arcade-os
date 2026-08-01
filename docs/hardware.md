# Hardware Wiring & Pinout Guide - Raspberry Pi 5

Detailed hardware reference and schematic pin mapping for **Pi Arcade OS**.

---

## Raspberry Pi 5 Header Overview

Pi Arcade OS utilizes standard BCM pin numbering for button inputs, I2C display communication, and PWM passive buzzer audio output.

```
       3.3V (1)  (2)  5V Power [LCD VCC]
  SDA1 [LCD] (3)  (4)  5V Power
  SCL1 [LCD] (5)  (6)  Ground [LCD GND]
      GPIO 4 (7)  (8)  GPIO 14
      Ground (9)  (10) GPIO 15
     GPIO 17 (11) (12) GPIO 18
 UP [GPIO27] (13) (14) Ground [Buttons Common GND]
DN  [GPIO22] (15) (16) GPIO 23 [LEFT]
     3.3V    (17) (18) GPIO 24 [RIGHT]
     ...
     GPIO 12 (32) (34) Ground [Buzzer GND]
             [Buzzer PWM]
```

---

## Component Pinout Table

### 1. Control Buttons (4-Button Arcade Scheme)
All buttons use internal software pull-up resistors (`pull_up=True` in `gpiozero`). Connect one terminal of each button to the designated BCM pin, and connect the opposite terminals to Common Ground (Pin 14).

| Action | BCM Pin | Physical Header Pin | Wire Color | Active State |
| :--- | :--- | :--- | :--- | :--- |
| **UP / Menu Up** | `GPIO27` | Pin 13 | Orange | LOW (0V on press) |
| **DOWN / Menu Down** | `GPIO22` | Pin 15 | Yellow | LOW (0V on press) |
| **LEFT / Back** | `GPIO23` | Pin 16 | Blue | LOW (0V on press) |
| **RIGHT / Select** | `GPIO24` | Pin 18 | Green | LOW (0V on press) |
| **Common Ground** | Ground | Pin 14 | Black | Ground Reference |

---

### 2. 16x2 I2C Character LCD Display
Uses standard PCF8574 I2C backpack interface operating at 5V logic.

| LCD Pin | Function | Physical Header Pin | BCM Equivalent |
| :--- | :--- | :--- | :--- |
| **VCC** | +5V Power | Pin 2 | 5V Power Rail |
| **GND** | Ground | Pin 6 | Ground Rail |
| **SDA** | I2C Data Line | Pin 3 | `GPIO02` (I2C1 SDA) |
| **SCL** | I2C Clock Line | Pin 5 | `GPIO03` (I2C1 SCL) |

*Default I2C Bus Address:* `0x27`

---

### 3. Passive Piezo Buzzer
Outputs square-wave PWM frequencies to generate non-blocking sound tones.

| Buzzer Pin | Function | Physical Header Pin | BCM Equivalent |
| :--- | :--- | :--- | :--- |
| **Signal (+)** | PWM Frequency Input | Pin 32 | `GPIO12` (PWM0) |
| **Ground (-)** | Ground Reference | Pin 34 | Ground Rail |
