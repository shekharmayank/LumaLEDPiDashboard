# LED Matrix Dashboard

Web dashboard for managing a playlist of things to display on a cascaded MAX7219 LED matrix connected to a Raspberry Pi.

## Prerequisites

- Raspberry Pi (any model with SPI)
- MAX7219 LED matrix (4 cascaded 8x8 modules, configured as 32x8)
- SPI interface enabled (`sudo raspi-config` → Interface Options → SPI)
- [uv](https://docs.astral.sh/uv/) installed

## System Dependencies

```bash
sudo usermod -a -G spi,gpio pi
sudo apt install build-essential python3-dev python3-pip libfreetype6-dev libjpeg-dev libopenjp2-7 libtiff5
```

## Setup

```bash
uv sync
```

This creates a virtual environment and installs all dependencies (Flask, luma.core, luma.led-matrix, Pillow, etc.).

## Run

```bash
uv run dashboard
```

Or directly:

```bash
uv run python app.py
```

The web server starts on `http://0.0.0.0:5000`. Open `http://raspberrypi.local:5000` from any device on the network.

## Usage

1. **Add items** to the playlist — choose from Time, Date, Animation, Message, or Todo List
2. **Set duration** (in seconds) for how long each item displays before cycling to the next
3. **Reorder** items by dragging
4. **Manage todos** on the Todos page — pending items scroll across the matrix automatically
5. The display loop updates instantly when you change the playlist

## Todo List

When a Todo List item is in the playlist, all pending (undone) todos scroll across the matrix one by one. Duration is calculated automatically — no manual duration needed.

## References

- [luma.led-matrix documentation](https://luma-led-matrix.readthedocs.io/en/latest/intro.html)
- [luma.led-matrix GitHub (upstream)](https://github.com/rm-hull/luma.led_matrix)
- [luma.led-matrix GitHub (fork)](https://github.com/shekharmayank/luma.led_matrix)
