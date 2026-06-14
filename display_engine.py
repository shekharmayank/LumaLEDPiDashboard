import math
import random
import time
from datetime import datetime
from threading import Thread, Event

from luma.core.render import canvas
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, TINY_FONT

from config import WIDTH, HEIGHT, TODO_SCROLL_SPEED, TODO_PAUSE_BETWEEN, ANIMATIONS
from models import get_items, get_pending_todos


class DisplayEngine(Thread):
    def __init__(self, device):
        super().__init__(daemon=True)
        self.device = device
        self.reload = Event()
        self.stop = Event()
        self._shown_animations = set()

    def run(self):
        while not self.stop.is_set():
            items = get_items()
            if items:
                for item in items:
                    if self.stop.is_set():
                        return
                    if self.reload.is_set():
                        self.reload.clear()
                        self._shown_animations.clear()
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
                if name == "random_unseen":
                    pool = [a for a in ANIMATIONS if a != "random_unseen"]
                    available = [a for a in pool if a not in self._shown_animations]
                    if not available:
                        self._shown_animations.clear()
                        available = list(pool)
                    name = random.choice(available)
                    self._shown_animations.add(name)
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


def _brightness_curve(v):
    return max(0.0, min(1.0, v))


# =====================================================================
# ENHANCED EXISTING ANIMATIONS
# =====================================================================


def plasma_swirl(device, duration=14, reload_ev=None, stop_ev=None):
    """Vortex plasma: rotating spiral arms with multi-octave noise and bright core."""
    t = 0.0
    n, delay = _frame_range(duration, 30)
    cx, cy = (WIDTH - 1) / 2.0, (HEIGHT - 1) / 2.0
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.16
        with canvas(device) as draw:
            draw.point((int(cx), int(cy)), fill="white")
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    dx, dy = x - cx, y - cy
                    r = math.hypot(dx, dy)
                    theta = math.atan2(dy, dx)
                    v = (
                        math.sin(r * 0.7 - t * 1.6) * 0.7
                        + math.sin(theta * 3 + t * 0.9) * 0.6
                        + math.sin((x + y) * 0.22 + t * 0.7) * 0.4
                        + math.sin((x - y) * 0.18 + t * 1.1) * 0.4
                        + math.sin(math.hypot(x - 16, y - 4) * 0.45 + t * 0.5) * 0.3
                    )
                    if v > 0.45:
                        draw.point((x, y), fill="white")
                    elif v > 0.15 and (int(t * 8 + x * 2 + y * 2) & 3) == 0:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


def sine_worm(device, duration=14, reload_ev=None, stop_ev=None):
    """Multi-segment sine worm with body and trailing wisps."""
    t = 0.0
    n, delay = _frame_range(duration, 28)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.22
        with canvas(device) as draw:
            for x in range(WIDTH):
                base = HEIGHT / 2 + math.sin(x * 0.55 + t) * 2.6
                y0 = int(round(base))
                if 0 <= y0 < HEIGHT:
                    draw.point((x, y0), fill="white")
                for i in range(1, 5):
                    off = math.sin(x * 0.55 + t - i * 0.4) * 1.5
                    yi = int(round(base + off))
                    if 0 <= yi < HEIGHT and random.random() > 0.18 * i:
                        draw.point((x, yi), fill="white")
        time.sleep(delay)


def pendulum_wave(device, duration=14, reload_ev=None, stop_ev=None):
    """A wave of pendulums swinging with phase offset along x."""
    t = 0.0
    n, delay = _frame_range(duration, 28)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.06
        with canvas(device) as draw:
            for x in range(WIDTH):
                phase = x * 0.32
                y = int(HEIGHT / 2 + math.sin(t * 1.6 + phase) * 3.2)
                if 0 <= y < HEIGHT:
                    draw.point((x, y), fill="white")
                    if 0 <= y + 1 < HEIGHT:
                        draw.point((x, y + 1), fill="white")
                    if 0 <= y - 1 < HEIGHT:
                        draw.point((x, y - 1), fill="white")
        time.sleep(delay)


def aurora_wave(device, duration=14, reload_ev=None, stop_ev=None):
    """Layered aurora curtains with twinkling stars overhead."""
    t = 0.0
    n, delay = _frame_range(duration, 28)
    stars = [(random.randint(0, WIDTH - 1), random.randint(0, 1), random.random())
             for _ in range(10)]
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.09
        with canvas(device) as draw:
            for sx, sy, ph in stars:
                if (math.sin(t * 3 + ph * 6.28) + 1) > 1.2:
                    draw.point((sx, sy), fill="white")
            for x in range(WIDTH):
                v1 = math.sin(x * 0.25 + t * 0.8)
                v2 = math.sin(x * 0.4 + t * 1.4) * 0.6
                v3 = math.sin(x * 0.15 + t * 2.1) * 0.3
                base_y = HEIGHT / 2 + (v1 + v2 + v3) * 1.1
                for y in range(2, HEIGHT):
                    dy = abs(y - base_y)
                    if dy < 0.9 and random.random() > 0.3:
                        draw.point((x, y), fill="white")
                    elif dy < 2.0 and random.random() > 0.85:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


def galaxy_spiral(device, duration=14, reload_ev=None, stop_ev=None):
    """Two-arm spiral galaxy with glowing core, dust lanes and orbiting stars."""
    stars = []
    for _ in range(80):
        stars.append({
            "angle": random.uniform(0, 2 * math.pi),
            "radius": random.uniform(0.2, 6.5),
            "speed": random.uniform(0.25, 1.0),
            "drift": random.uniform(-0.02, 0.02),
            "arm": random.choice([0, 1]),
        })
    n, delay = _frame_range(duration, 26)
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            cx, cy = WIDTH // 2, HEIGHT // 2
            for dx, dy in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                if 0 <= cx + dx < WIDTH and 0 <= cy + dy < HEIGHT:
                    draw.point((cx + dx, cy + dy), fill="white")
            for s in stars:
                s["angle"] += 0.05 * s["speed"]
                s["radius"] += s["drift"]
                if s["radius"] < 0.2 or s["radius"] > 6.5:
                    s["radius"] = random.uniform(0.2, 6.5)
                    s["angle"] = random.uniform(0, 2 * math.pi)
                    s["drift"] = random.uniform(-0.02, 0.02)
                arm_offset = s["arm"] * math.pi
                arm_angle = s["angle"] + s["radius"] * 0.45 + arm_offset
                px = int(round(cx + math.cos(arm_angle) * s["radius"]))
                py = int(round(cy + math.sin(arm_angle) * s["radius"] * 0.55))
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    if random.random() > 0.1:
                        draw.point((px, py), fill="white")
        time.sleep(delay)


def matrix_rain_v2(device, duration=14, reload_ev=None, stop_ev=None):
    """Dramatic matrix rain with bright heads, fading trails, and sparkles."""
    drops = []
    for _ in range(WIDTH * 2):
        drops.append({
            "x": random.randint(0, WIDTH - 1),
            "y": random.uniform(-10, 0),
            "len": random.randint(3, 7),
            "speed": random.uniform(0.4, 1.1),
        })
    n, delay = _frame_range(duration, 28)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            for d in drops:
                head_y = int(d["y"])
                if 0 <= head_y < HEIGHT:
                    draw.point((d["x"], head_y), fill="white")
                    if head_y > 0:
                        draw.point((d["x"], head_y - 1), fill="white")
                for i in range(1, d["len"]):
                    y = int(d["y"]) - i
                    if 0 <= y < HEIGHT:
                        if i == 1 and random.random() > 0.2:
                            draw.point((d["x"], y), fill="white")
                        elif i < 3 and random.random() > 0.3:
                            draw.point((d["x"], y), fill="white")
                        elif random.random() > 0.55 + i * 0.07:
                            draw.point((d["x"], y), fill="white")
                d["y"] += d["speed"]
                if d["y"] > HEIGHT + d["len"]:
                    d["x"] = random.randint(0, WIDTH - 1)
                    d["y"] = random.uniform(-10, -2)
                    d["len"] = random.randint(3, 7)
                    d["speed"] = random.uniform(0.4, 1.1)
        time.sleep(delay)


def meteor_shower_v2(device, duration=14, reload_ev=None, stop_ev=None):
    """Meteor shower over a static starfield with bright meteor heads."""
    stars = [(random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1),
              random.random()) for _ in range(14)]
    meteors = []
    for _ in range(5):
        meteors.append({
            "x": random.randint(0, WIDTH - 1),
            "y": -random.randint(0, 5),
            "dx": random.uniform(-0.5, 0.5),
            "dy": random.uniform(0.7, 1.5),
            "len": random.randint(6, 11),
        })
    n, delay = _frame_range(duration, 30)
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            for sx, sy, ph in stars:
                if (math.sin(f * 0.4 + ph * 6.28) + 1) > 1.4:
                    draw.point((sx, sy), fill="white")
            for m in meteors:
                hx, hy = int(m["x"]), int(m["y"])
                if 0 <= hx < WIDTH and 0 <= hy < HEIGHT:
                    draw.point((hx, hy), fill="white")
                    if 0 <= hx - int(m["dx"]) < WIDTH and 0 <= hy - int(m["dy"]) < HEIGHT:
                        draw.point((hx - int(m["dx"]), hy - int(m["dy"])), fill="white")
                for i in range(1, m["len"]):
                    px = int(m["x"] - m["dx"] * i)
                    py = int(m["y"] - m["dy"] * i)
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT and random.random() > i * 0.08:
                        draw.point((px, py), fill="white")
                m["x"] += m["dx"]
                m["y"] += m["dy"]
                if m["y"] > HEIGHT + 2 or m["x"] < -2 or m["x"] > WIDTH + 2:
                    m["x"] = random.randint(0, WIDTH - 1)
                    m["y"] = -random.randint(0, 5)
                    m["dy"] = random.uniform(0.7, 1.5)
                    m["dx"] = random.uniform(-0.5, 0.5)
                    m["len"] = random.randint(6, 11)
        time.sleep(delay)


def firework_sparks(device, duration=14, reload_ev=None, stop_ev=None):
    """Launched rockets that burst into fading sparks with secondary pops."""
    n, delay = _frame_range(duration, 30)
    bursts = []
    for i in range(7):
        bursts.append({
            "cx": random.randint(5, WIDTH - 6),
            "cy": random.randint(2, HEIGHT - 2),
            "pts": [(random.uniform(-1, 1), random.uniform(-1, 1)) for _ in range(14)],
            "start": random.randint(0, int(n * 0.6)),
            "color_seed": random.random(),
        })
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            for b in bursts:
                elapsed = f - b["start"]
                if elapsed < 0:
                    if elapsed > -10:
                        tx = b["cx"]
                        ty = HEIGHT - 1
                        ax = b["cx"]
                        ay = 0
                        prog = (elapsed + 10) / 10.0
                        px = int(tx + (ax - tx) * prog)
                        py = int(ty + (ay - ty) * prog)
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            draw.point((px, py), fill="white")
                    continue
                rate = 0.32
                r = elapsed * rate
                if elapsed < 18:
                    for dx, dy in b["pts"]:
                        px = int(round(b["cx"] + dx * r * 3.2))
                        py = int(round(b["cy"] + dy * r * 3.2))
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            draw.point((px, py), fill="white")
                elif elapsed < 36:
                    for dx, dy in b["pts"]:
                        px = int(round(b["cx"] + dx * r * 3.2))
                        py = int(round(b["cy"] + dy * r * 3.2 + (elapsed - 18) * 0.18))
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT and random.random() > (elapsed - 18) * 0.05:
                            draw.point((px, py), fill="white")
        time.sleep(delay)


def breathe(device, duration=12, reload_ev=None, stop_ev=None):
    """Breathing circle that pulses with double-beat rhythm and halo glow."""
    t = 0.0
    cx, cy = WIDTH // 2, HEIGHT // 2
    n, delay = _frame_range(duration, 22)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.05
        beat = math.sin(t * 1.3)
        beat = beat * abs(beat)
        r = 1.6 + beat * 2.6
        with canvas(device) as draw:
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    d = math.hypot(x - cx, y - cy)
                    if abs(d - r) < 0.7:
                        draw.point((x, y), fill="white")
                    elif abs(d - r) < 1.4 and random.random() > 0.65:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


# =====================================================================
# NEW: SCENERY ANIMATIONS
# =====================================================================


def beach_boat(device, duration=14, reload_ev=None, stop_ev=None):
    """Tropical beach: sun, drifting cloud, sailboat on rolling waves, palm tree."""
    n, delay = _frame_range(duration, 24)
    cloud_x = 0
    boat_x = -4.0
    t = 0.0
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        cloud_x = (cloud_x + 0.15) % (WIDTH + 6)
        boat_x += 0.35
        if boat_x > WIDTH + 4:
            boat_x = -6
        t = f * 0.12
        with canvas(device) as draw:
            sun_x, sun_y = 24, 1
            for dx, dy in [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]:
                px, py = sun_x + dx, sun_y + dy
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    draw.point((px, py), fill="white")

            cx_int = int(cloud_x)
            if 0 <= cx_int - 1 < WIDTH:
                draw.point((cx_int - 1, 0), fill="white")
            if 0 <= cx_int < WIDTH:
                draw.point((cx_int, 0), fill="white")
                draw.point((cx_int + 1, 0), fill="white")
                draw.point((cx_int, 1), fill="white")

            bx = int(round(boat_x))
            if 0 <= bx < WIDTH:
                draw.point((bx, 4), fill="white")
                draw.point((bx + 1, 4), fill="white")
                if 0 <= bx + 2 < WIDTH:
                    draw.point((bx + 2, 4), fill="white")
                draw.point((bx + 1, 3), fill="white")
                if 0 <= bx < WIDTH and 0 <= 2 < HEIGHT:
                    draw.point((bx, 2), fill="white")
                    draw.point((bx + 1, 2), fill="white")
                if 0 <= bx + 1 < WIDTH and 0 <= 1 < HEIGHT:
                    draw.point((bx + 1, 1), fill="white")

            for x in range(WIDTH):
                v = math.sin(x * 0.45 + t) * 0.7 + math.sin(x * 0.22 + t * 1.4) * 0.4
                y = 5 + int(round(v))
                if 0 <= y < HEIGHT:
                    draw.point((x, y), fill="white")
                if (x + f) % 6 == 0 and y + 1 < HEIGHT:
                    draw.point((x, y + 1), fill="white")

            for x in range(WIDTH):
                if (x * 7 + f * 3) % 11 == 0:
                    draw.point((x, 6), fill="white")
                if (x * 3 + f * 5) % 13 == 0:
                    draw.point((x, 7), fill="white")
                if (x * 5 + f) % 17 == 0:
                    draw.point((x, 6), fill="white")
                    draw.point((x, 7), fill="white")
        time.sleep(delay)


def ocean_horizon(device, duration=14, reload_ev=None, stop_ev=None):
    """Night ocean: moon, twinkling stars, three layers of rolling waves."""
    n, delay = _frame_range(duration, 24)
    stars = [(random.randint(0, WIDTH - 1), random.randint(0, 2), random.random())
             for _ in range(14)]
    moon_x, moon_y = 6, 1
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t = f * 0.1
        with canvas(device) as draw:
            for dx, dy in [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]:
                px, py = moon_x + dx, moon_y + dy
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    draw.point((px, py), fill="white")
            for sx, sy, ph in stars:
                if (math.sin(f * 0.5 + ph * 6.28) + 1) > 1.5:
                    draw.point((sx, sy), fill="white")
            reflection = (f // 4) % 3
            for dy in range(-2, 1):
                if (dy + f // 2) % 3 == reflection and 0 <= moon_y + dy + 1 < HEIGHT:
                    if 0 <= moon_x < WIDTH:
                        draw.point((moon_x, moon_y + dy + 1), fill="white")

            for x in range(WIDTH):
                y = 3 + int(round(math.sin(x * 0.5 + t) * 0.7 + math.sin(x * 0.22 + t * 1.6) * 0.3))
                if 0 <= y < HEIGHT:
                    draw.point((x, y), fill="white")
                    if (x + f) % 5 == 0 and y + 1 < HEIGHT:
                        draw.point((x, y + 1), fill="white")

            for x in range(WIDTH):
                y = 5 + int(round(math.sin(x * 0.35 + t * 1.3) * 1.0))
                if 0 <= y < HEIGHT:
                    draw.point((x, y), fill="white")
                if (x + f * 2) % 4 == 0 and y + 1 < HEIGHT:
                    draw.point((x, y + 1), fill="white")

            for x in range(WIDTH):
                y = 7 + int(round(math.sin(x * 0.25 + t * 1.8) * 0.7))
                y = min(7, max(0, y))
                draw.point((x, y), fill="white")
        time.sleep(delay)


def mountains_sunset(device, duration=14, reload_ev=None, stop_ev=None):
    """Layered mountain silhouettes with a setting sun, birds and a distant tree line."""
    n, delay = _frame_range(duration, 22)
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t = f * 0.05
        sun_y = max(0, min(HEIGHT - 2, 3 - int(abs(math.sin(t)))))
        sun_x = 24
        with canvas(device) as draw:
            for dx, dy in [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]:
                px, py = sun_x + dx, sun_y + dy
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    draw.point((px, py), fill="white")
            for x in range(WIDTH):
                back_peak = 1 + int(1.5 * math.sin(x * 0.22 + 1.2))
                back_top = max(1, min(5, back_peak))
                for y in range(back_top, HEIGHT):
                    draw.point((x, y), fill="white")
            for x in range(WIDTH):
                p1 = 3 + int(1.2 * math.sin(x * 0.32 + 2.6))
                p2 = 3 + int(1.0 * math.sin(x * 0.55 + 0.3))
                front_top = max(3, min(6, max(p1, p2)))
                for y in range(front_top, HEIGHT):
                    draw.point((x, y), fill="white")
            bird_x = (f * 1.5) % (WIDTH + 8) - 4
            bi = int(round(bird_x))
            for bx in (bi, bi + 1, bi - 1, bi + 2, bi - 2):
                if 0 <= bx < WIDTH and 0 <= 1 < HEIGHT:
                    draw.point((bx, 1), fill="white")
        time.sleep(delay)


def campfire(device, duration=14, reload_ev=None, stop_ev=None):
    """Flickering campfire with flames, logs, and rising embers."""
    n, delay = _frame_range(duration, 28)
    embers = []
    for _ in range(6):
        embers.append({
            "x": 14 + random.uniform(-3, 3),
            "y": HEIGHT - 2,
            "vy": random.uniform(-0.5, -0.1),
            "life": random.randint(0, 30),
        })
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        flicker = 0.6 + 0.4 * math.sin(f * 0.7) + 0.3 * math.sin(f * 1.7)
        with canvas(device) as draw:
            draw.point((13, 7), fill="white")
            draw.point((14, 7), fill="white")
            draw.point((15, 7), fill="white")
            draw.point((16, 7), fill="white")
            draw.point((17, 7), fill="white")
            draw.point((12, 6), fill="white")
            draw.point((13, 6), fill="white")
            draw.point((14, 6), fill="white")
            draw.point((15, 6), fill="white")
            draw.point((16, 6), fill="white")
            draw.point((17, 6), fill="white")
            draw.point((18, 6), fill="white")

            flame_h = int(round(2 + flicker * 2.5))
            cx = 15
            for i in range(flame_h):
                w = max(0, 3 - i) // 1
                y = 5 - i
                if 0 <= y < HEIGHT:
                    for dx in range(-w, w + 1):
                        if random.random() > 0.18 + i * 0.05:
                            px = cx + dx + int(round(math.sin(f * 0.6 + i) * 0.6))
                            if 0 <= px < WIDTH:
                                draw.point((px, y), fill="white")

            for e in embers:
                e["y"] += e["vy"]
                e["x"] += math.sin(f * 0.5 + e["life"]) * 0.15
                e["life"] += 1
                ix, iy = int(round(e["x"])), int(round(e["y"]))
                if 0 <= ix < WIDTH and 0 <= iy < HEIGHT and e["life"] < 25:
                    if random.random() > e["life"] * 0.04:
                        draw.point((ix, iy), fill="white")
                if e["life"] > 30 or iy < 0:
                    e["x"] = 15 + random.uniform(-2, 2)
                    e["y"] = HEIGHT - 2
                    e["vy"] = random.uniform(-0.5, -0.15)
                    e["life"] = 0
        time.sleep(delay)


def rainy_window(device, duration=14, reload_ev=None, stop_ev=None):
    """Streaks of rain on a window with drops sliding and splashing."""
    n, delay = _frame_range(duration, 28)
    drops = []
    for _ in range(14):
        drops.append({
            "x": random.randint(0, WIDTH - 1),
            "y": random.uniform(-8, HEIGHT - 1),
            "speed": random.uniform(0.5, 1.4),
            "len": random.randint(2, 4),
        })
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            for d in drops:
                for i in range(d["len"]):
                    y = int(d["y"]) - i
                    if 0 <= y < HEIGHT and random.random() > i * 0.15:
                        if 0 <= d["x"] < WIDTH:
                            draw.point((d["x"], y), fill="white")
                d["y"] += d["speed"]
                if d["y"] > HEIGHT + d["len"]:
                    if 0 <= d["x"] < WIDTH and HEIGHT - 1 >= 0 and random.random() > 0.4:
                        draw.point((d["x"], HEIGHT - 1), fill="white")
                    d["x"] = random.randint(0, WIDTH - 1)
                    d["y"] = random.uniform(-6, -1)
                    d["speed"] = random.uniform(0.5, 1.4)
                    d["len"] = random.randint(2, 4)
        time.sleep(delay)


def city_skyline(device, duration=14, reload_ev=None, stop_ev=None):
    """City skyline silhouette with twinkling windows and slow scrolling moon."""
    heights = [3, 5, 2, 6, 4, 7, 3, 5, 4, 6, 2, 5, 3, 7, 4, 5,
               3, 6, 4, 2, 5, 7, 3, 4, 5, 6, 2, 4, 3, 5, 6, 4]
    n, delay = _frame_range(duration, 22)
    moon_x = 0
    windows = {}
    for x in range(WIDTH):
        for y in range(HEIGHT - heights[x], HEIGHT - 1):
            if random.random() > 0.45:
                windows[(x, y)] = random.random()
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        moon_x = (f * 0.2) % (WIDTH + 6) - 3
        with canvas(device) as draw:
            mxi = int(round(moon_x))
            for dx, dy in [(0, 0), (-1, 0), (1, 0), (0, -1)]:
                px, py = mxi + dx, 0 + dy
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    draw.point((px, py), fill="white")
            for x in range(WIDTH):
                h = heights[x]
                for y in range(HEIGHT - h, HEIGHT):
                    draw.point((x, y), fill="white")
            for (x, y), ph in list(windows.items()):
                if (x, y) >= (0, HEIGHT - heights[x]) and (x, y) < (WIDTH, HEIGHT - 1):
                    twinkle = math.sin(f * 0.3 + ph * 12.0)
                    if twinkle > 0.3 or (f + int(ph * 10)) % 17 == 0:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


def cherry_blossom(device, duration=14, reload_ev=None, stop_ev=None):
    """Falling cherry blossom petals swaying in the wind."""
    n, delay = _frame_range(duration, 24)
    petals = []
    for _ in range(10):
        petals.append({
            "x": random.uniform(0, WIDTH - 1),
            "y": random.uniform(-6, HEIGHT - 1),
            "vy": random.uniform(0.15, 0.45),
            "sway_amp": random.uniform(0.3, 0.8),
            "sway_speed": random.uniform(0.04, 0.12),
            "phase": random.uniform(0, 6.28),
        })
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            for x in range(WIDTH):
                if f % 60 < 2 and x in (5, 14, 26):
                    draw.point((x, 0), fill="white")
            for p in petals:
                sway = math.sin(f * p["sway_speed"] + p["phase"]) * p["sway_amp"]
                p["y"] += p["vy"]
                p["x"] += sway * 0.1
                ix, iy = int(round(p["x"])), int(round(p["y"]))
                if 0 <= ix < WIDTH and 0 <= iy < HEIGHT:
                    draw.point((ix, iy), fill="white")
                    if 0 <= ix + 1 < WIDTH and random.random() > 0.5:
                        draw.point((ix + 1, iy), fill="white")
                    if 0 <= iy + 1 < HEIGHT and random.random() > 0.5:
                        draw.point((ix, iy + 1), fill="white")
                if p["y"] > HEIGHT + 1:
                    p["x"] = random.uniform(0, WIDTH - 1)
                    p["y"] = random.uniform(-4, 0)
                    p["vy"] = random.uniform(0.15, 0.45)
        time.sleep(delay)


def lightning_storm(device, duration=14, reload_ev=None, stop_ev=None):
    """Dark clouds with periodic lightning flashes and falling rain."""
    n, delay = _frame_range(duration, 28)
    rain = []
    for _ in range(20):
        rain.append({
            "x": random.randint(0, WIDTH - 1),
            "y": random.uniform(-5, HEIGHT - 1),
            "speed": random.uniform(0.6, 1.2),
        })
    next_flash = 30
    flash_frames = 0
    bolt_path = []
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        if f >= next_flash:
            flash_frames = 4
            next_flash = f + random.randint(35, 80)
            bolt_path = []
            bx = random.randint(4, WIDTH - 5)
            by = 1
            bolt_path.append((bx, by))
            while by < HEIGHT - 1:
                by += 1
                bx += random.choice([-1, 0, 1])
                bx = max(0, min(WIDTH - 1, bx))
                bolt_path.append((bx, by))
                if random.random() > 0.7:
                    bx += random.choice([-1, 1])
                    bx = max(0, min(WIDTH - 1, bx))
                    bolt_path.append((bx, by))
        flash = flash_frames > 0
        flash_frames = max(0, flash_frames - 1)
        with canvas(device) as draw:
            for x in range(WIDTH):
                if x % 4 in (0, 1) or random.random() > 0.7:
                    draw.point((x, 0), fill="white")
            if flash:
                for bx, by in bolt_path:
                    draw.point((bx, by), fill="white")
                for x in range(WIDTH):
                    for y in range(0, 2):
                        draw.point((x, y), fill="white")
            else:
                for r in rain:
                    if 0 <= int(r["x"]) < WIDTH and 0 <= int(r["y"]) < HEIGHT:
                        draw.point((int(r["x"]), int(r["y"])), fill="white")
                    r["y"] += r["speed"]
                    if r["y"] > HEIGHT:
                        r["x"] = random.randint(0, WIDTH - 1)
                        r["y"] = random.uniform(-3, 0)
        time.sleep(delay)


# =====================================================================
# NEW: CHARACTER / ARCADE ANIMATIONS
# =====================================================================


def pacman_chase(device, duration=14, reload_ev=None, stop_ev=None):
    """Pacman chomping across the screen eating dots, then resetting."""
    n, delay = _frame_range(duration, 22)
    period = max(30, n // 2)
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        progress = ((f + 3) % period) / float(period)
        px = int(progress * (WIDTH + 6)) - 3
        chomp = abs(math.sin(f * 0.5))
        with canvas(device) as draw:
            for dot_x in range(0, WIDTH):
                if dot_x > px + 2 and (dot_x + (f // 2)) % 4 != 0:
                    draw.point((dot_x, 4), fill="white")
            if 0 <= px < WIDTH:
                mouth_open = int(round(chomp * 2))
                pac_x, pac_y = px, 4
                if mouth_open == 0:
                    pac = [(-1, -1), (0, -1), (1, -1),
                           (-1, 0), (0, 0), (1, 0),
                           (-1, 1), (0, 1), (1, 1)]
                elif mouth_open == 1:
                    pac = [(-1, -1), (0, -1),
                           (-1, 0), (0, 0),
                           (-1, 1), (0, 1),
                           (1, 0)]
                else:
                    pac = [(-1, -1), (0, -1),
                           (-1, 0),
                           (-1, 1), (0, 1),
                           (1, 0)]
                for dx, dy in pac:
                    px2, py2 = pac_x + dx, pac_y + dy
                    if 0 <= px2 < WIDTH and 0 <= py2 < HEIGHT:
                        draw.point((px2, py2), fill="white")
        time.sleep(delay)


def walking_man(device, duration=14, reload_ev=None, stop_ev=None):
    """Stick figure walking across the screen with leg/arm swing, looping."""
    n, delay = _frame_range(duration, 24)
    WALK = [
        [
            "..X..",
            "..X..",
            "X.X.X",
            ".X.X.",
            "X...X",
        ],
        [
            "..X..",
            "..X..",
            "X.X.X",
            ".X.X.",
            ".X.X.",
        ],
        [
            "..X..",
            "..X..",
            "X.X.X",
            ".X.X.",
            "X...X",
        ],
        [
            "..X..",
            "..X..",
            "X.X.X",
            ".X.X.",
            ".X.X.",
        ],
    ]
    sprite = WALK
    sprite_w = 5
    sprite_h = 5
    cycle = WIDTH + sprite_w
    loops = 3
    speed = (cycle * loops) / max(1, n)
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        frame = (f // 3) % 4
        s = sprite[frame]
        ox = int((f * speed) % cycle) - sprite_w // 2
        with canvas(device) as draw:
            for ry, row in enumerate(s):
                for rx, ch in enumerate(row):
                    if ch == "X":
                        px = ox + rx
                        py = HEIGHT - sprite_h - 1 + ry
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            draw.point((px, py), fill="white")
            for x in range(WIDTH):
                if (x + f) % 6 < 2:
                    draw.point((x, HEIGHT - 1), fill="white")
        time.sleep(delay)


def bouncing_ball(device, duration=14, reload_ev=None, stop_ev=None):
    """A 3x3 ball that bounces with realistic gravity, squash on landing, and a scaling shadow."""
    n, delay = _frame_range(duration, 30)
    g = 0.22
    x = 6.0
    y = 0.0
    vy = 0.4
    vx = 0.7
    bounce = 0
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        vy += g
        x += vx
        y += vy
        if y >= HEIGHT - 2:
            y = HEIGHT - 2
            vy = -abs(vy) * 0.78
            vx *= 0.97
            bounce += 1
            if abs(vy) < 0.3 or bounce > 8:
                y = 0.0
                x = 6.0
                vy = 0.4
                vx = 0.7
                bounce = 0
        ix, iy = int(round(x)), int(round(y))
        on_ground = iy >= HEIGHT - 2
        with canvas(device) as draw:
            height_above_ground = max(0.0, (HEIGHT - 2) - y)
            shadow_w = max(1, int(round(2.5 - height_above_ground * 0.35)))
            if 0 <= ix < WIDTH:
                for sx_off in range(-shadow_w, shadow_w + 1):
                    px = ix + sx_off
                    if 0 <= px < WIDTH and 0 <= HEIGHT - 1 < HEIGHT:
                        if random.random() > 0.25:
                            draw.point((px, HEIGHT - 1), fill="white")
            ball = [
                (-1, -1), (0, -1), (1, -1),
                (-1, 0), (0, 0), (1, 0),
                (-1, 1), (0, 1), (1, 1),
            ]
            if on_ground:
                ball = [
                    (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
                    (-1, -1), (0, -1), (1, -1),
                ]
            for dx, dy in ball:
                px, py = ix + dx, iy + dy
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    draw.point((px, py), fill="white")
        time.sleep(delay)


def space_invader(device, duration=14, reload_ev=None, stop_ev=None):
    """Classic space invader marching back and forth, with bomb drops."""
    n, delay = _frame_range(duration, 24)
    SPRITE_A = [
        "..X...X..",
        ".........X",
        "..XXXXX..",
        ".X.XXX.X.",
        "XXXXXXXXX",
        "X.XXXXX.X",
        "X.X...X.X",
    ]
    SPRITE_B = [
        "..X...X..",
        "X.......X",
        "..XXXXX..",
        "..XXXXX..",
        "XXXXXXXXX",
        "X.XXXXX.X",
        "X.X...X.X",
    ]
    bombs = []
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        cycle = f // 6
        sprite = SPRITE_A if cycle % 2 == 0 else SPRITE_B
        step = (f // 8) % (WIDTH // 2)
        direction = 1 if (f // (WIDTH * 4)) % 2 == 0 else -1
        ox = (step * 2 * direction) % (WIDTH + 12) - 6
        if random.random() > 0.85:
            bombs.append({
                "x": ox + 4,
                "y": 3,
            })
        with canvas(device) as draw:
            for ry, row in enumerate(sprite):
                for rx, ch in enumerate(row):
                    if ch == "X":
                        px = ox + rx
                        py = ry
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            draw.point((px, py), fill="white")
            for b in bombs[:]:
                if 0 <= int(b["x"]) < WIDTH and 0 <= int(b["y"]) < HEIGHT:
                    draw.point((int(b["x"]), int(b["y"])), fill="white")
                b["y"] += 0.5
                if b["y"] > HEIGHT + 1:
                    bombs.remove(b)
            for x in range(WIDTH):
                for y in range(HEIGHT - 1, HEIGHT):
                    if (x + f) % 7 == 0:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


def dancing_skeleton(device, duration=14, reload_ev=None, stop_ev=None):
    """Stick figure dancing through 4 dance poses with a pulsing ground line."""
    n, delay = _frame_range(duration, 22)
    frames = [
        [
            "..X..",
            ".X.X.",
            "X.X.X",
            ".X.X.",
            "X...X",
        ],
        [
            "..X..",
            "X.X.X",
            ".X.X.",
            "X.X.X",
            ".X.X.",
        ],
        [
            "..X..",
            ".XXX.",
            "X.X.X",
            ".X.X.",
            "X.X.X",
        ],
        [
            "..X..",
            "X.X.X",
            ".X.X.",
            "X.X.X",
            ".X.X.",
        ],
    ]
    sprite_h = 5
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        frame = frames[(f // 4) % 4]
        ox = WIDTH // 2 - 2
        with canvas(device) as draw:
            beat = (f % 8) < 4
            for x in range(WIDTH):
                if (x + f) % 5 < (2 if beat else 3):
                    draw.point((x, HEIGHT - 1), fill="white")
            for ry, row in enumerate(frame):
                for rx, ch in enumerate(row):
                    if ch == "X":
                        px = ox + rx
                        py = HEIGHT - 1 - sprite_h + ry
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            draw.point((px, py), fill="white")
        time.sleep(delay)


def snake_game(device, duration=14, reload_ev=None, stop_ev=None):
    """Self-playing snake game with growing body and food pellets."""
    n, delay = _frame_range(duration, 22)
    snake = [(5, 4), (4, 4), (3, 4)]
    direction = (1, 0)
    food = (20, 4)
    grow = 0
    move_every = 4
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        if f % move_every == 0 and f > 0:
            head = snake[0]
            new_head = (head[0] + direction[0], head[1] + direction[1])
            if (new_head[0] < 0 or new_head[0] >= WIDTH
                    or new_head[1] < 0 or new_head[1] >= HEIGHT
                    or new_head in snake):
                snake = [(5, 4), (4, 4), (3, 4)]
                direction = (1, 0)
                food = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))
                grow = 0
            else:
                snake.insert(0, new_head)
                if new_head == food:
                    grow += 3
                    food = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))
                if grow > 0:
                    grow -= 1
                else:
                    snake.pop()
            if abs(snake[0][0] - food[0]) > abs(snake[0][1] - food[1]):
                direction = (1 if food[0] > snake[0][0] else -1, 0)
            else:
                direction = (0, 1 if food[1] > snake[0][1] else -1)
        with canvas(device) as draw:
            if 0 <= food[0] < WIDTH and 0 <= food[1] < HEIGHT:
                draw.point((food[0], food[1]), fill="white")
                if 0 <= food[0] + 1 < WIDTH and (f // 3) % 2 == 0:
                    draw.point((food[0] + 1, food[1]), fill="white")
            for i, (sx, sy) in enumerate(snake):
                if 0 <= sx < WIDTH and 0 <= sy < HEIGHT:
                    draw.point((sx, sy), fill="white")
                    if i == 0 and 0 <= sx + direction[0] < WIDTH and 0 <= sy + direction[1] < HEIGHT:
                        draw.point((sx + direction[0], sy + direction[1]), fill="white")
        time.sleep(delay)


# =====================================================================
# NEW: ABSTRACT COOL ANIMATIONS
# =====================================================================


def dna_helix(device, duration=14, reload_ev=None, stop_ev=None):
    """Rotating DNA double helix with shimmering base pairs."""
    n, delay = _frame_range(duration, 24)
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t = f * 0.12
        with canvas(device) as draw:
            for x in range(WIDTH):
                phase1 = (x * 0.55 + t) % (2 * math.pi)
                phase2 = phase1 + math.pi
                y1 = (HEIGHT - 1) / 2 + math.sin(phase1) * 2.6
                y2 = (HEIGHT - 1) / 2 + math.sin(phase2) * 2.6
                iy1, iy2 = int(round(y1)), int(round(y2))
                if 0 <= iy1 < HEIGHT:
                    draw.point((x, iy1), fill="white")
                if 0 <= iy2 < HEIGHT:
                    draw.point((x, iy2), fill="white")
                if x % 2 == 0 and 0 <= iy1 < HEIGHT and 0 <= iy2 < HEIGHT:
                    mid = (iy1 + iy2) // 2
                    for yy in (min(iy1, iy2), mid, max(iy1, iy2)):
                        if 0 <= yy < HEIGHT and abs(iy1 - iy2) < 4:
                            draw.point((x, yy), fill="white")
        time.sleep(delay)


def fire_3d(device, duration=14, reload_ev=None, stop_ev=None):
    """A wall of flame rising from the bottom with random flickering heat."""
    n, delay = _frame_range(duration, 30)
    heat = [[0.0] * HEIGHT for _ in range(WIDTH)]
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        for x in range(WIDTH):
            new_v = 1.0 if random.random() > 0.4 else 0.6
            heat[x][HEIGHT - 1] = new_v
            for y in range(HEIGHT - 2, -1, -1):
                cool = heat[x][y + 1] - random.uniform(0.05, 0.18)
                if x > 0:
                    cool += heat[x - 1][y + 1] * 0.15
                if x < WIDTH - 1:
                    cool += heat[x + 1][y + 1] * 0.15
                cool *= 0.7
                heat[x][y] = max(0.0, cool)
        with canvas(device) as draw:
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    if heat[x][y] > 0.55:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


def fish_tank(device, duration=14, reload_ev=None, stop_ev=None):
    """Two fish swimming with tail wag and rising bubbles in an aquarium."""
    n, delay = _frame_range(duration, 22)
    bubbles = []
    for _ in range(4):
        bubbles.append({
            "x": random.uniform(2, WIDTH - 3),
            "y": random.uniform(HEIGHT - 1, HEIGHT - 1),
            "speed": random.uniform(0.1, 0.3),
        })
    fishes = [
        {"x": 4.0, "y": 4.0, "dir": 1, "speed": 0.3, "phase": 0.0},
        {"x": 18.0, "y": 2.0, "dir": -1, "speed": 0.25, "phase": 3.14},
    ]
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        with canvas(device) as draw:
            for y in (0, HEIGHT - 1):
                for x in range(WIDTH):
                    if (x + f) % 5 < 2:
                        draw.point((x, y), fill="white")
            for fish in fishes:
                fish["x"] += fish["dir"] * fish["speed"]
                fish["phase"] += 0.5
                if fish["x"] > WIDTH + 2:
                    fish["x"] = -3
                elif fish["x"] < -3:
                    fish["x"] = WIDTH + 2
                fx, fy = int(round(fish["x"])), int(round(fish["y"]))
                d = fish["dir"]
                tail = int(round(math.sin(fish["phase"]) * 1.2))
                if 0 <= fx < WIDTH and 0 <= fy < HEIGHT:
                    draw.point((fx, fy), fill="white")
                    if 0 <= fx + d < WIDTH and 0 <= fy < HEIGHT:
                        draw.point((fx + d, fy), fill="white")
                    if 0 <= fx - d < WIDTH and 0 <= fy < HEIGHT:
                        draw.point((fx - d, fy), fill="white")
                    if 0 <= fy - 1 < HEIGHT:
                        draw.point((fx, fy - 1), fill="white")
                    if 0 <= fy + 1 < HEIGHT:
                        draw.point((fx, fy + 1), fill="white")
                    tx, ty = fx - 2 * d, fy + tail
                    if 0 <= tx < WIDTH and 0 <= ty < HEIGHT:
                        draw.point((tx, ty), fill="white")
                    if d == 1 and 0 <= fx + 1 < WIDTH and 0 <= fy - 1 < HEIGHT:
                        draw.point((fx + 1, fy - 1), fill="white")
                    if d == -1 and 0 <= fx - 1 < WIDTH and 0 <= fy - 1 < HEIGHT:
                        draw.point((fx - 1, fy - 1), fill="white")
            for b in bubbles:
                b["y"] -= b["speed"]
                ix, iy = int(round(b["x"])), int(round(b["y"]))
                if 0 <= ix < WIDTH and 0 <= iy < HEIGHT:
                    draw.point((ix, iy), fill="white")
                if b["y"] < 0:
                    b["x"] = random.uniform(2, WIDTH - 3)
                    b["y"] = HEIGHT - 1
                    b["speed"] = random.uniform(0.1, 0.3)
        time.sleep(delay)


def tunnel_zoom(device, duration=14, reload_ev=None, stop_ev=None):
    """Infinite 3D wireframe tunnel zooming inward toward the viewer."""
    n, delay = _frame_range(duration, 28)
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t = f * 0.18
        with canvas(device) as draw:
            cx, cy = WIDTH / 2, HEIGHT / 2
            for layer in range(5, 0, -1):
                prog = (t + layer * 0.35) % 1.0
                size_x = (WIDTH * 0.5) * prog + 0.5
                size_y = (HEIGHT * 0.5) * prog + 0.5
                x0 = int(round(cx - size_x))
                y0 = int(round(cy - size_y))
                x1 = int(round(cx + size_x))
                y1 = int(round(cy + size_y))
                if x0 == x1 or y0 == y1:
                    continue
                draw.rectangle([(x0, y0), (x1, y1)], outline="white")
                if prog > 0.7:
                    for k in range(1, 3):
                        ix = int(round(cx - size_x + (2 * size_x) * k / 3))
                        iy = int(round(cy - size_y + (2 * size_y) * k / 3))
                        if 0 <= ix < WIDTH and 0 <= iy < HEIGHT:
                            draw.point((ix, iy), fill="white")
        time.sleep(delay)


def domino_cascade(device, duration=14, reload_ev=None, stop_ev=None):
    """A wave of dominoes toppling across the screen."""
    n, delay = _frame_range(duration, 28)
    spacing = 3
    dominoes = []
    for x in range(0, WIDTH + 6, spacing):
        dominoes.append({"x": float(x - 6), "fall": -100.0})
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t = f * 0.5
        with canvas(device) as draw:
            for d in dominoes:
                d["fall"] = max(d["fall"], t - d["x"] * 0.4)
                ix = int(round(d["x"]))
                if d["fall"] < 0:
                    for y in range(HEIGHT - 4, HEIGHT):
                        if 0 <= ix < WIDTH and 0 <= y < HEIGHT:
                            draw.point((ix, y), fill="white")
                else:
                    tilt = min(1.0, d["fall"] / 1.5)
                    top_x = ix - int(round(tilt * 2))
                    for y in range(HEIGHT - 4, HEIGHT):
                        for off in range(-int(round(tilt * 2)), 1):
                            if 0 <= top_x + off < WIDTH and 0 <= y < HEIGHT:
                                draw.point((top_x + off, y), fill="white")
        time.sleep(delay)


# =====================================================================
# NEW: ICONIC / WOW-FACTOR ANIMATIONS
# =====================================================================


def heart_beat(device, duration=14, reload_ev=None, stop_ev=None):
    """A heart that beats with a lub-dub rhythm and ECG line below."""
    n, delay = _frame_range(duration, 24)
    HEART_BIG = [
        ".XXX.XX.",
        "XXXXXXX.",
        "XXXXXXX.",
        ".XXXXX..",
        "..XXX...",
        "...X....",
    ]
    HEART_SMALL = [
        "..XX.XX.",
        ".XXXXXX.",
        ".XXXXXX.",
        "..XXXX..",
        "...XX...",
        "....X...",
    ]
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        cycle = f % 16
        big = cycle in (1, 2, 3, 7, 8)
        sprite = HEART_BIG if big else HEART_SMALL
        ox = (WIDTH - len(HEART_BIG[0])) // 2
        oy = 0
        with canvas(device) as draw:
            for ry, row in enumerate(sprite):
                for rx, ch in enumerate(row):
                    if ch == "X":
                        px, py = ox + rx, oy + ry
                        if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                            draw.point((px, py), fill="white")
            for x in range(WIDTH):
                if 0 <= HEIGHT - 1 < HEIGHT:
                    beat = cycle in (2, 7)
                    if beat and 14 <= x <= 17:
                        draw.point((x, HEIGHT - 1), fill="white")
                    elif (x + f) % 6 < 2:
                        draw.point((x, HEIGHT - 1), fill="white")
        time.sleep(delay)


def conway_life(device, duration=14, reload_ev=None, stop_ev=None):
    """Conway's Game of Life evolving on a 32x8 toroidal grid with random reseeding."""
    n, delay = _frame_range(duration, 8)
    grid = [[1 if random.random() > 0.7 else 0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        new_grid = [[0] * WIDTH for _ in range(HEIGHT)]
        for y in range(HEIGHT):
            for x in range(WIDTH):
                neighbors = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nx = (x + dx) % WIDTH
                        ny = (y + dy) % HEIGHT
                        neighbors += grid[ny][nx]
                if grid[y][x] == 1 and neighbors in (2, 3):
                    new_grid[y][x] = 1
                elif grid[y][x] == 0 and neighbors == 3:
                    new_grid[y][x] = 1
        grid = new_grid
        alive = sum(sum(row) for row in grid)
        if alive < 6 or f % 30 == 29:
            grid = [[1 if random.random() > 0.7 else 0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
        with canvas(device) as draw:
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    if grid[y][x]:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


def dvd_bounce(device, duration=14, reload_ev=None, stop_ev=None):
    """A small logo box bouncing around the screen, changing color on each wall hit."""
    n, delay = _frame_range(duration, 26)
    LOGO_W, LOGO_H = 4, 3
    x = 2.0
    y = 1.0
    dx, dy = 0.6, 0.4
    logo_seed = 0
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        x += dx
        y += dy
        hit = False
        if x <= 0:
            x = 0
            dx = abs(dx)
            hit = True
        elif x + LOGO_W >= WIDTH:
            x = WIDTH - LOGO_W
            dx = -abs(dx)
            hit = True
        if y <= 0:
            y = 0
            dy = abs(dy)
            hit = True
        elif y + LOGO_H >= HEIGHT:
            y = HEIGHT - LOGO_H
            dy = -abs(dy)
            hit = True
        if hit:
            logo_seed = (logo_seed + 1) % 4
        ix, iy = int(round(x)), int(round(y))
        with canvas(device) as draw:
            for dy_off in range(LOGO_H):
                for dx_off in range(LOGO_W):
                    px, py = ix + dx_off, iy + dy_off
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        if (px + py + f) % (3 + logo_seed) == 0:
                            draw.point((px, py), fill="white")
            for dx_off in range(LOGO_W):
                if 0 <= ix + dx_off < WIDTH and 0 <= iy < HEIGHT:
                    draw.point((ix + dx_off, iy), fill="white")
                if 0 <= ix + dx_off < WIDTH and 0 <= iy + LOGO_H - 1 < HEIGHT:
                    draw.point((ix + dx_off, iy + LOGO_H - 1), fill="white")
            for dy_off in range(LOGO_H):
                if 0 <= ix < WIDTH and 0 <= iy + dy_off < HEIGHT:
                    draw.point((ix, iy + dy_off), fill="white")
                if 0 <= ix + LOGO_W - 1 < WIDTH and 0 <= iy + dy_off < HEIGHT:
                    draw.point((ix + LOGO_W - 1, iy + dy_off), fill="white")
        time.sleep(delay)


def clock_watch(device, duration=14, reload_ev=None, stop_ev=None):
    """An analog clock face with rotating hour, minute and second hands."""
    n, delay = _frame_range(duration, 8)
    cx, cy = (WIDTH - 1) / 2.0, (HEIGHT - 1) / 2.0
    start = time.time()
    for f in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        elapsed = time.time() - start
        now = datetime.now()
        sec_angle = (now.second + now.microsecond / 1e6) * (2 * math.pi / 60) - math.pi / 2
        min_angle = (now.minute + now.second / 60.0) * (2 * math.pi / 60) - math.pi / 2
        hour_angle = ((now.hour % 12) + now.minute / 60.0) * (2 * math.pi / 12) - math.pi / 2
        with canvas(device) as draw:
            for ang in range(12):
                a = ang * (2 * math.pi / 12) - math.pi / 2
                px, py = int(round(cx + math.cos(a) * 3.3)), int(round(cy + math.sin(a) * 2.5))
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    draw.point((px, py), fill="white")
            for ang in (0, 3, 6, 9):
                a = ang * (2 * math.pi / 12) - math.pi / 2
                for r in (3.0, 3.3):
                    px, py = int(round(cx + math.cos(a) * r)), int(round(cy + math.sin(a) * r * 0.75))
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        draw.point((px, py), fill="white")
            for length, angle in [(1.8, hour_angle), (2.4, min_angle), (2.8, sec_angle)]:
                for r in range(0, int(length * 3)):
                    rad = r / 3.0
                    px, py = int(round(cx + math.cos(angle) * rad)), int(round(cy + math.sin(angle) * rad * 0.85))
                    if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                        draw.point((px, py), fill="white")
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
    "beach_boat": beach_boat,
    "ocean_horizon": ocean_horizon,
    "mountains_sunset": mountains_sunset,
    "campfire": campfire,
    "rainy_window": rainy_window,
    "city_skyline": city_skyline,
    "cherry_blossom": cherry_blossom,
    "lightning_storm": lightning_storm,
    "pacman_chase": pacman_chase,
    "walking_man": walking_man,
    "bouncing_ball": bouncing_ball,
    "space_invader": space_invader,
    "dancing_skeleton": dancing_skeleton,
    "snake_game": snake_game,
    "dna_helix": dna_helix,
    "fire_3d": fire_3d,
    "fish_tank": fish_tank,
    "tunnel_zoom": tunnel_zoom,
    "domino_cascade": domino_cascade,
    "heart_beat": heart_beat,
    "conway_life": conway_life,
    "dvd_bounce": dvd_bounce,
    "clock_watch": clock_watch,
}
