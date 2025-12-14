# Raspberry Pi 4B Setup Guide

Complete guide for setting up StoryBox IA on Raspberry Pi 4B.

## Hardware Requirements

- **Raspberry Pi 4B** (4GB or 8GB RAM recommended)
- **MicroSD Card** 64GB (Class 10 or better)
- **Power Supply** Official 5V/3A USB-C adapter
- **Cooling** Heatsink or fan (recommended for sustained LLM inference)
- **Audio Input** USB microphone or I2S MEMS mic (INMP441)
- **Audio Output** USB speaker/amplifier or I2S DAC HAT
- **Button** GPIO push button for hold-to-talk
- **LEDs** 2-3 LEDs for status indication

## OS Installation

### 1. Flash Raspberry Pi OS

Use Raspberry Pi Imager to flash **Raspberry Pi OS Lite (64-bit)** Bookworm:

```bash
# On Mac, download Raspberry Pi Imager
brew install --cask raspberry-pi-imager

# Flash: Raspberry Pi OS Lite (64-bit)
# Enable SSH in advanced options
# Set hostname, username, password
```

### 2. First Boot Setup

```bash
# SSH to Pi
ssh maxence@192.168.68.120

# Update system
sudo apt update && sudo apt full-upgrade -y

# Configure timezone, locale if needed
sudo raspi-config
```

## Initial Deployment from Mac

### 1. Deploy Code

From your Mac (in the storybox directory):

```bash
# Make deploy script executable
chmod +x scripts/deploy_init.sh

# Deploy to Pi
./scripts/deploy_init.sh
```

### 2. Transfer Models

Models are **NOT** included in Git. Transfer separately:

```bash
# Option A: rsync from Mac (recommended)
rsync -avz --progress \
  -e "ssh -i ~/.ssh/id_ed25519_storybox" \
  models/ maxence@192.168.68.120:~/models/

# Option B: Manual copy via USB drive
# Copy models/ to USB, then on Pi:
# cp -r /media/usb/models/* ~/models/
```

Verify models on Pi:

```bash
ssh maxence@192.168.68.120
ls -lh ~/models/*/
# Should show:
# ~/models/whisper/ggml-small.bin (465M)
# ~/models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf (1.9G)
# ~/models/piper/fr_FR-siwis-medium.onnx (61M)
# ~/models/piper/fr_FR-siwis-medium.onnx.json (5K)
```

## Installation on Raspberry Pi

### 1. Run Installation Script

SSH to Pi and run the installation script:

```bash
ssh maxence@192.168.68.120
cd ~/projects/storybox
bash scripts/install_pi.sh
```

This script will:
- Install system dependencies (cmake, ALSA, PortAudio, etc.)
- Create Python virtual environment
- Install Python packages
- Compile whisper.cpp (ARM64 optimized)
- Compile llama.cpp (ARM64 optimized)
- Install Piper TTS

**Duration:** ~10-15 minutes on Pi 4B

### 2. Configure Environment

```bash
cd ~/projects/storybox
cp .env.example .env
nano .env
```

Update `.env`:

```bash
# Model paths (verify these match)
WHISPER_MODEL_PATH=/home/maxence/models/whisper/ggml-small.bin
LLM_MODEL_PATH=/home/maxence/models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf
PIPER_MODEL_PATH=/home/maxence/models/piper/fr_FR-siwis-medium.onnx

# GPIO pins (adjust to your wiring)
BUTTON_PIN=17
LED_STATUS_PIN=22
LED_PROGRESS_1_PIN=23
LED_PROGRESS_2_PIN=24

# Audio devices
AUDIO_INPUT_DEVICE=default
AUDIO_OUTPUT_DEVICE=default

# Logging
LOG_LEVEL=INFO
```

### 3. Test Audio Devices

```bash
# List audio input devices
arecord -l

# List audio output devices
aplay -l

# Test microphone recording
arecord -f S16_LE -r 16000 -c 1 -d 3 test.wav
aplay test.wav

# Adjust ALSA volume if needed
alsamixer
```

### 4. Test Toolchains

```bash
source .venv/bin/activate

# Test Whisper
echo "Test" | ~/projects/storybox/bin/whisper-cli -m ~/models/whisper/ggml-small.bin

# Test Llama.cpp
~/projects/storybox/bin/llama-cli \
  -m ~/models/llm/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -n 50 \
  -p "Bonjour"

# Test Piper TTS
echo "Bonjour, ceci est un test." | \
  piper -m ~/models/piper/fr_FR-siwis-medium.onnx -f test_piper.wav
aplay test_piper.wav
```

## GPIO Wiring

### Button (Hold-to-Talk)

```
Button Pin 1 ─── GPIO 17 (Pin 11)
Button Pin 2 ─── GND (Pin 9)
```

Enable internal pull-up in code (default in configs/default.yaml).

### LEDs

```
LED Status Anode   ─── Resistor 220Ω ─── GPIO 22 (Pin 15)
LED Status Cathode ─── GND

LED Progress 1 Anode   ─── Resistor 220Ω ─── GPIO 23 (Pin 16)
LED Progress 1 Cathode ─── GND

LED Progress 2 Anode   ─── Resistor 220Ω ─── GPIO 24 (Pin 18)
LED Progress 2 Cathode ─── GND
```

## Systemd Service Setup

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/storybox.service
```

Content:

```ini
[Unit]
Description=StoryBox IA - AI Storytelling Device
After=network.target sound.target

[Service]
Type=simple
User=maxence
WorkingDirectory=/home/maxence/projects/storybox
EnvironmentFile=/home/maxence/projects/storybox/.env
ExecStart=/home/maxence/projects/storybox/.venv/bin/python -m app.main
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SupplementaryGroups=audio gpio

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable storybox

# Start service now
sudo systemctl start storybox

# Check status
sudo systemctl status storybox

# View logs
sudo journalctl -u storybox -f
```

## Performance Optimization

### 1. Thermal Management

Monitor temperature during LLM inference:

```bash
vcgencmd measure_temp
```

If temperature > 70°C, add heatsink or fan.

### 2. CPU Governor

Set performance mode for consistent speed:

```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

Make permanent by adding to `/etc/rc.local`.

### 3. Swap Configuration

Disable swap or use zram to reduce SD card writes:

```bash
# Disable swap
sudo dphys-swapfile swapoff
sudo systemctl disable dphys-swapfile

# Or use zram (lighter on SD card)
sudo apt install zram-tools
```

## Updates & Maintenance

### Code Updates

From Mac:

```bash
# Commit changes
git add .
git commit -m "Your changes"
git push

# On Pi (manual)
ssh maxence@192.168.68.120
cd ~/projects/storybox
git pull --rebase
sudo systemctl restart storybox

# Or automate with cron (optional)
# See workflow.md for timer setup
```

### Log Rotation

Logs auto-rotate at 50MB (configured in `configs/default.yaml`).

Manual cleanup:

```bash
rm ~/projects/storybox/logs/*.log.old
```

### Model Updates

To replace models:

```bash
# From Mac
rsync -avz --progress \
  -e "ssh -i ~/.ssh/id_ed25519_storybox" \
  models/new_model.gguf maxence@192.168.68.120:~/models/llm/

# On Pi, update config if needed
nano ~/projects/storybox/configs/default.yaml
sudo systemctl restart storybox
```

## Troubleshooting

### Audio Issues

```bash
# Check ALSA devices
arecord -l
aplay -l

# Test recording
arecord -f S16_LE -r 16000 -c 1 -d 3 test.wav

# Check volume
alsamixer

# Unmute if needed
amixer set Master unmute
amixer set Capture cap
```

### GPIO Permissions

```bash
# Add user to gpio group
sudo usermod -a -G gpio maxence

# Reboot or re-login for changes
```

### Out of Memory

```bash
# Check memory usage
free -h

# Check swap
swapon --show

# For 4GB Pi, consider:
# - Using smaller whisper model (base instead of small)
# - Reducing LLM context size in config
# - Enabling zram swap
```

### LLM Too Slow

Latency > 10s? Try:

```bash
# In configs/default.yaml:
llm:
  threads: 4  # Increase if you have 8GB Pi
  context_tokens: 1536  # Reduce from 2048

# Or use Q3 quantization (smaller model)
# Download Llama-3.2-3B-Instruct-Q3_K_M.gguf instead
```

## Benchmarks (Raspberry Pi 4B 8GB)

Expected performance:

- **Model Load Time**
  - Whisper small: ~2-3s
  - Llama 3B Q4_K_M: ~5-7s
  - Piper FR: <1s

- **Inference Speed**
  - STT: ~0.5x realtime (3s audio → 6s processing)
  - LLM: ~3-5 tokens/sec (plan generation ~20-30s)
  - TTS: ~2x realtime (very fast)

- **Total Latency** (button release → first audio): 8-12s

## Next Steps

After successful setup:

1. Test end-to-end pipeline (V0 MVP)
2. Fine-tune prompts for story quality
3. Adjust LED patterns and timing
4. Monitor thermal performance during long stories
5. Optimize thread counts and context size
6. Consider SSD for models (V2)

## Support

For issues, check:
- Service logs: `sudo journalctl -u storybox -f`
- Application logs: `~/projects/storybox/logs/storybox.log`
- System resources: `htop`, `free -h`, `vcgencmd measure_temp`

Report issues at: https://github.com/didux123/storybox/issues
