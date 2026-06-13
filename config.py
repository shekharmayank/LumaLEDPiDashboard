import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "dashboard.db")

WIDTH = 32
HEIGHT = 8

DEVICE_CONFIG = {
    "cascaded": 4,
    "block_orientation": -90,
    "blocks_arranged_in_reverse_order": False,
    "contrast": 16,
}

SPI_CONFIG = {
    "port": 0,
    "device": 0,
}

ANIMATIONS = [
    "plasma_swirl",
    "sine_worm",
    "pendulum_wave",
    "aurora_wave",
    "galaxy_spiral",
    "matrix_rain_v2",
    "meteor_shower_v2",
    "firework_sparks",
    "breathe",
]

TODO_SCROLL_SPEED = 4
TODO_PAUSE_BETWEEN = 2
