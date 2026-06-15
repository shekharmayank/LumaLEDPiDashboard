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
                name = item["config"].get("name", "abstract_flow")
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

    def _show_animation_name(self, name):
        show_message(
            self.device,
            name,
            fill="white",
            font=proportional(CP437_FONT),
            scroll_delay=0.05,
        )
        time.sleep(1.5)

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
# ABSTRACT ANIMATION
# =====================================================================


def abstract_flow(device, duration=14, reload_ev=None, stop_ev=None):
    t = 0.0
    n, delay = _frame_range(duration, 30)
    cx, cy = (WIDTH - 1) / 2.0, (HEIGHT - 1) / 2.0
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.07
        with canvas(device) as draw:
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    dist = math.hypot(x - cx, y - cy)
                    angle = math.atan2(y - cy, x - cx)
                    v = (
                        math.sin(dist * 0.45 - t * 0.7) * 0.6
                        + math.sin(angle * 4 + t * 0.9) * 0.4
                        + math.sin((x * 0.5 + y * 0.3) + t * 0.6) * 0.3
                        + math.sin(dist * 0.22 + angle * 2 - t * 0.4) * 0.3
                        + math.sin((x - y) * 0.15 + t * 0.8) * 0.2
                    )
                    thresh = 0.1 * math.sin(t * 0.15) + 0.05 * math.sin(t * 0.25 + 1.0)
                    if v > thresh:
                        draw.point((x, y), fill="white")
        time.sleep(delay)


def serpentine(device, duration=14, reload_ev=None, stop_ev=None):
    trail = []
    head_x = 0.0
    t = 0.0
    n, delay = _frame_range(duration, 30)
    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return
        t += 0.06
        head_x += 0.35
        if head_x > WIDTH + 3:
            head_x = -3
        head_y = (HEIGHT - 1) / 2 + math.sin(head_x * 0.4 + t * 1.0) * 2.5 + math.sin(t * 0.5) * 0.5
        trail.insert(0, (head_x, head_y))
        if len(trail) > 14:
            trail.pop()
        with canvas(device) as draw:
            for i, (px, py) in enumerate(trail):
                ix, iy = int(round(px)), int(round(py))
                if 0 <= ix < WIDTH and 0 <= iy < HEIGHT:
                    fade = 1.0 - i / len(trail)
                    if fade > 0.6:
                        draw.point((ix, iy), fill="white")
                    if fade > 0.8:
                        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                            if 0 <= ix+dx < WIDTH and 0 <= iy+dy < HEIGHT:
                                draw.point((ix+dx, iy+dy), fill="white")
        time.sleep(delay)


# =====================================================================
# RADAR ANIMATION
# =====================================================================


def radar(device, duration=14, reload_ev=None, stop_ev=None):
    """
    Radar emulator.

    Random pixels represent ships. A thin sweep block moves quickly from
    left to right across the display. Ships light up for 1 second after
    the sweep passes over them, and the sweep repeats with a fresh scan.
    """
    num_ships = random.randint(4, 7)
    ships = set()
    while len(ships) < num_ships:
        ships.add((random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1)))
    ships = list(ships)

    lit = {}  # ship index -> timestamp when it should go dark
    n, delay = _frame_range(duration, 20)
    sweep_width = 2
    sweep_speed = 1.0  # pixels per frame
    sweep_x = -sweep_width

    for _ in range(n):
        if _check_events(reload_ev, stop_ev):
            return

        sweep_x += sweep_speed
        if sweep_x > WIDTH:
            sweep_x = -sweep_width
            lit.clear()

        now = time.time()
        right_edge = sweep_x + sweep_width
        for i, (sx, sy) in enumerate(ships):
            if sx <= right_edge and i not in lit:
                lit[i] = now + 1.0

        with canvas(device) as draw:
            # Draw lit ships
            for i, (sx, sy) in enumerate(ships):
                if lit.get(i, 0) > now:
                    draw.point((sx, sy), fill="white")

            # Draw sweep block
            start_x = int(sweep_x)
            end_x = int(sweep_x + sweep_width)
            for x in range(start_x, end_x + 1):
                if 0 <= x < WIDTH:
                    for y in range(HEIGHT):
                        draw.point((x, y), fill="white")

        time.sleep(delay)


ANIM_FUNCS = {
    "abstract_flow": abstract_flow,
    "serpentine": serpentine,
    "radar": radar,
}
