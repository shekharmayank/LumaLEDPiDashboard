import math
import random
import time
import json
from datetime import datetime
from threading import Thread, Event

from luma.core.render import canvas
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT

from config import WIDTH, HEIGHT, TODO_SCROLL_SPEED, TODO_PAUSE_BETWEEN
from models import get_items, get_pending_todos


class DisplayEngine(Thread):
    def __init__(self, device):
        super().__init__(daemon=True)
        self.device = device
        self.reload = Event()
        self.stop = Event()

    def run(self):
        while not self.stop.is_set():
            items = get_items()
            if items:
                for item in items:
                    if self.stop.is_set():
                        return
                    if self.reload.is_set():
                        self.reload.clear()
                        break
                    self._display_item(item)
            else:
                show_message(
                    self.device,
                    "Add items...",
                    fill="white",
                    font=proportional(CP437_FONT),
                )
                if self.stop.wait(5):
                    return
                if self.reload.is_set():
                    self.reload.clear()

    def _should_stop(self):
        return self.stop.is_set()

    def _should_reload(self):
        return self.reload.is_set()

    def _display_item(self, item):
        try:
            t = item["type"]
            if t == "time":
                self._show_time(item["duration"] or 10)
            elif t == "date":
                self._show_date()
            elif t == "animation":
                name = item["config"].get("name", "plasma_swirl")
                duration = item["duration"] or 14
                anim = ANIM_FUNCS.get(name)
                if anim:
                    anim(self.device, duration, self.reload, self.stop)
            elif t == "message":
                text_str = item["config"].get("text", "")
                show_message(
                    self.device,
                    text_str,
                    fill="white",
                    font=proportional(CP437_FONT),
                )
            elif t == "todo":
                self._show_todos()
        except Exception:
            pass

    def _show_time(self, duration):
        end = time.time() + duration
        toggle = False
        while time.time() < end:
            if self._should_reload() or self._should_stop():
                return
            toggle = not toggle
            now = datetime.now()
            with canvas(self.device) as draw:
                h, m = now.strftime("%H"), now.strftime("%M")
                text(draw, (0, 1), h, fill="white", font=proportional(CP437_FONT))
                col = ":" if toggle else " "
                text(draw, (15, 1), col, fill="white", font=proportional(TINY_FONT))
                text(draw, (17, 1), m, fill="white", font=proportional(CP437_FONT))
                for _ in range(3):
                    draw.point(
                        (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)),
                        fill="white",
                    )
            time.sleep(0.5)

    def _show_date(self):
        now = datetime.now()
        date_str = now.strftime("%d %b %Y %a")
        show_message(
            self.device,
            date_str,
            fill="white",
            font=proportional(CP437_FONT),
        )

    def _show_todos(self):
        todos = get_pending_todos()
        if not todos:
            show_message(
                self.device,
                "No todos!",
                fill="white",
                font=proportional(CP437_FONT),
            )
            return
        for todo in todos:
            if self._should_reload() or self._should_stop():
                return
            show_message(
                self.device,
                todo["text"],
                fill="white",
                font=proportional(CP437_FONT),
            )
            if self.stop.wait(TODO_PAUSE_BETWEEN):
                return


def _frame_range(duration, fps):
    n = int(duration * fps)
    delay = 1.0 / fps
    return n, delay


def _check_events(reload_ev, stop_ev):
    if stop_ev and stop_ev.is_set():
        return True
    if reload_ev and reload_ev.is_set():
        return True
    return False


def plasma_swirl(device, duration=14, reload_ev=None, stop_ev=None):
    t = 0.0
    n, delay = _frame_range(duration, 25)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.18
        with canvas(device) as draw:
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    v = (
                        math.sin(x * 0.35 + t)
                        + math.sin(y * 0.25 + t * 0.7)
                        + math.sin((x + y) * 0.18 + t * 1.3)
                        + math.sin(math.hypot(x - 15, y - 4) * 0.45 + t * 0.6)
                    )
                    if v > 0.6:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


def sine_worm(device, duration=14, reload_ev=None, stop_ev=None):
    t = 0.0
    n, delay = _frame_range(duration, 25)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.22
        with canvas(device) as draw:
            for x in range(WIDTH):
                base = HEIGHT // 2 + math.sin(x * 0.55 + t) * 2.8
                y0 = int(base)
                if 0 <= y0 < HEIGHT:
                    draw.point((x, y0), fill="white")
                for i in range(1, 4):
                    gy = int(base + math.sin(x * 0.55 + t + i * 0.35) * 1.2)
                    if 0 <= gy < HEIGHT and random.random() > 0.25 * i:
                        draw.point((x, gy), fill="white")
        time.sleep(delay)


def pendulum_wave(device, duration=14, reload_ev=None, stop_ev=None):
    t = 0.0
    n, delay = _frame_range(duration, 25)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.055
        with canvas(device) as draw:
            for x in range(WIDTH):
                phase = x * 0.35
                y = int(HEIGHT // 2 + math.sin(t * 1.6 + phase) * 3)
                if 0 <= y < HEIGHT:
                    draw.point((x, y), fill="white")
                    if y < HEIGHT - 1:
                        draw.point((x, y + 1), fill="white")
        time.sleep(delay)


def aurora_wave(device, duration=14, reload_ev=None, stop_ev=None):
    t = 0.0
    n, delay = _frame_range(duration, 28)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.09
        with canvas(device) as draw:
            for x in range(WIDTH):
                val = (
                    math.sin(x * 0.25 + t * 0.8)
                    + math.sin(x * 0.4 + t * 1.4) * 0.6
                    + math.sin(x * 0.15 + t * 2.1) * 0.3
                )
                base_y = HEIGHT // 2 + val * 1.2
                for y in range(HEIGHT):
                    dy = abs(y - base_y)
                    if dy < 1.5 and random.random() > 0.45:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


def galaxy_spiral(device, duration=14, reload_ev=None, stop_ev=None):
    stars = []
    for _ in range(40):
        stars.append({
            "angle": random.uniform(0, 2 * math.pi),
            "radius": random.uniform(0.5, 5.5),
            "speed": random.uniform(0.3, 1.0),
            "drift": random.uniform(-0.02, 0.02),
        })
    n, delay = _frame_range(duration, 22)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            cx, cy = WIDTH // 2, HEIGHT // 2
            for s in stars:
                s["angle"] += 0.06 * s["speed"]
                s["radius"] += s["drift"]
                if s["radius"] < 0.3 or s["radius"] > 5.8:
                    s["radius"] = random.uniform(0.5, 5.5)
                    s["angle"] = random.uniform(0, 2 * math.pi)
                    s["drift"] = random.uniform(-0.02, 0.02)
                arm_angle = s["angle"] + s["radius"] * 0.5
                px = int(cx + math.cos(arm_angle) * s["radius"])
                py = int(cy + math.sin(arm_angle) * s["radius"])
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    draw.point((px, py), fill="white")
        time.sleep(delay)


def matrix_rain_v2(device, duration=14, reload_ev=None, stop_ev=None):
    drops = []
    for _ in range(WIDTH * 2):
        drops.append({
            "x": random.randint(0, WIDTH - 1),
            "y": random.uniform(-8, 0),
            "len": random.randint(3, 7),
            "speed": random.uniform(0.4, 1.0),
        })
    n, delay = _frame_range(duration, 25)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            for d in drops:
                for i in range(1, d["len"]):
                    y = int(d["y"] - i)
                    if 0 <= y < HEIGHT and random.random() > i * 0.1:
                        draw.point((d["x"], y), fill="white")
                yh = int(d["y"])
                if 0 <= yh < HEIGHT:
                    draw.point((d["x"], yh), fill="white")
                    if yh > 0:
                        draw.point((d["x"], yh - 1), fill="white")
                d["y"] += d["speed"]
                if d["y"] > HEIGHT + d["len"]:
                    d["x"] = random.randint(0, WIDTH - 1)
                    d["y"] = random.uniform(-8, -2)
                    d["len"] = random.randint(3, 7)
                    d["speed"] = random.uniform(0.4, 1.0)
        time.sleep(delay)


def meteor_shower_v2(device, duration=14, reload_ev=None, stop_ev=None):
    meteors = []
    for _ in range(6):
        meteors.append({
            "x": random.randint(0, WIDTH - 1),
            "y": -random.randint(0, 5),
            "dx": random.uniform(-0.6, 0.6),
            "dy": random.uniform(0.8, 1.6),
            "len": random.randint(5, 10),
        })
    n, delay = _frame_range(duration, 28)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            for m in meteors:
                for i in range(1, m["len"]):
                    px = int(m["x"] - m["dx"] * i)
                    py = int(m["y"] - m["dy"] * i)
                    if (
                        0 <= px < WIDTH
                        and 0 <= py < HEIGHT
                        and random.random() > i * 0.07
                    ):
                        draw.point((px, py), fill="white")
                hx, hy = int(m["x"]), int(m["y"])
                if 0 <= hx < WIDTH and 0 <= hy < HEIGHT:
                    draw.point((hx, hy), fill="white")
                m["x"] += m["dx"]
                m["y"] += m["dy"]
                if m["y"] > HEIGHT + 2 or m["x"] < -2 or m["x"] > WIDTH + 2:
                    m["x"] = random.randint(0, WIDTH - 1)
                    m["y"] = -random.randint(0, 5)
                    m["dy"] = random.uniform(0.8, 1.6)
                    m["dx"] = random.uniform(-0.6, 0.6)
                    m["len"] = random.randint(5, 10)
        time.sleep(delay)


def firework_sparks(device, duration=14, reload_ev=None, stop_ev=None):
    n, delay = _frame_range(duration, 28)
    bursts = []
    for _ in range(8):
        cx = random.randint(6, WIDTH - 6)
        cy = random.randint(2, HEIGHT - 2)
        pts = [(random.uniform(-1, 1), random.uniform(-1, 1)) for _ in range(12)]
        bursts.append({
            "cx": cx,
            "cy": cy,
            "pts": pts,
            "start_frame": random.randint(0, int(n * 0.6)),
        })
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            for b in bursts:
                elapsed = f - b["start_frame"]
                if elapsed < 0:
                    continue
                rate = 0.3
                r = elapsed * rate
                if elapsed < 14:
                    for dx, dy in b["pts"]:
                        px = int(b["cx"] + dx * r * 3)
                        py = int(b["cy"] + dy * r * 3)
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            draw.point((px, py), fill="white")
                elif elapsed < 28:
                    for dx, dy in b["pts"]:
                        px = int(b["cx"] + dx * r * 3)
                        py = int(b["cy"] + dy * r * 3 + (elapsed - 14) * 0.12)
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            draw.point((px, py), fill="white")
        time.sleep(delay)


def breathe(device, duration=12, reload_ev=None, stop_ev=None):
    t = 0.0
    cx, cy = WIDTH // 2, HEIGHT // 2
    n, delay = _frame_range(duration, 20)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.045
        r = 2.5 + math.sin(t * 1.3) * 2
        with canvas(device) as draw:
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    d = math.hypot(x - cx, y - cy)
                    if abs(d - r) < 0.7:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


ANIM_FUNCS = {
    "plasma_swirl": plasma_swirl,
    "sine_worm": sine_worm,
    "pendulum_wave": pendulum_wave,
    "aurora_wave": aurora_wave,
    "galaxy_spiral": galaxy_spiral,
    "matrix_rain_v2": matrix_rain_v2,
    "meteor_shower_v2": meteor_shower_v2,
    "firework_sparks": firework_sparks,
    "breathe": breathe,
}
