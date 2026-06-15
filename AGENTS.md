# Agent Notes

## Project Context

This is a web dashboard for managing a playlist displayed on a **cascaded MAX7219 LED matrix connected to a Raspberry Pi**. The physical display is **32 pixels wide by 8 pixels tall** (4 cascaded 8x8 modules).

Always keep this 32x8 constraint in mind when modifying display code:

- Only 8 rows of pixels are available (y coordinates 0-7).
- Horizontal space is very limited; text/fonts must be chosen carefully.
- The display driver is `luma.led_matrix` using `luma.core.legacy` fonts.

## Key Files

- `app.py` — Flask web server and dashboard API.
- `display_engine.py` — Display loop and rendering logic for the LED matrix.
- `config.py` — Display dimensions (`WIDTH = 32`, `HEIGHT = 8`) and hardware config.
- `models.py` — Data models and persistence.
- `README.md` — Human-facing setup and usage docs.
