# Deployment Guide - Raspberry Pi 5

This guide provides step-by-step instructions for deploying **Pi Arcade OS** onto a physical Raspberry Pi 5.

---

## Hardware Prerequisites
- Raspberry Pi 5 (4GB or 8GB RAM)
- Raspberry Pi OS (64-bit, Debian Bookworm based)
- 4x Tactile Push Buttons wired to BCM GPIO 27, 22, 23, 24
- 16x2 Character LCD with PCF8574 I2C Backpack (address 0x27)
- 1x Passive Piezo Buzzer connected to BCM GPIO 12

---

## Step 1: System Package Installation

Update apt repositories and install python3 virtual environment, git, and I2C tools:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv git i2c-tools python3-pygame
```

---

## Step 2: Enable I2C Interface

1. Run the Raspberry Pi configuration utility:
   ```bash
   sudo raspi-config
   ```
2. Navigate to **Interface Options** -> **I2C** and select **Enable**.
3. Reboot the Raspberry Pi:
   ```bash
   sudo reboot
   ```
4. Verify the 16x2 LCD is detected at address `0x27`:
   ```bash
   sudo i2cdetect -y 1
   ```
   *Output should display `27` in the grid.*

---

## Step 3: Repository Setup & Virtual Environment

Clone the repository and set up a Python virtual environment with system site packages enabled (for gpiozero/lgpio):

```bash
cd ~
git clone https://github.com/hectorpacheco/pi-arcade-os.git
cd pi-arcade-os

python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Step 4: Systemd Kiosk Autostart Service

To automatically launch Pi Arcade OS on Raspberry Pi boot without requiring manual login, create a systemd service unit.

Create `/etc/systemd/system/pi-arcade.service`:

```ini
[Unit]
Description=Pi Arcade OS Kiosk Service
After=multi-user.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/pi-arcade-os
ExecStart=/home/pi/pi-arcade-os/.venv/bin/python3 -m src.main --gpio
Restart=always
RestartSec=3
Environment=DISPLAY=:0
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-arcade.service
sudo systemctl start pi-arcade.service
```

Check service status:

```bash
sudo systemctl status pi-arcade.service
```
