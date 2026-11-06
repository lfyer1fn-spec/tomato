import json
import math
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox

BASE = 340
TOMATO_R = 132
FACE_R = 104
RING_R = 78
HAND_R = 88

BG = "#fdf6f0"
GRAD_TOP = "#fff9f4"
GRAD_BOTTOM = "#f8e3d9"
TOMATO = "#e8503f"
TOMATO_RIM = "#c9382a"
TOMATO_LIGHT = "#ff8472"
TOMATO_GLOSS = "#ffb3a6"
LEAF = "#2fa35e"
LEAF_DARK = "#1f7d47"
INK = "#2c3e50"
MUTED = "#95a5a6"
TRACK = "#f0dcd4"
PLATE = "#ffffff"
TICK_MINOR = "#cbbab2"
TICK_MAJOR = "#8d7f78"
GREY = "#a4b0b3"

SETTINGS_NAME = "pomodoro_settings.json"
DEFAULT_LANG = "en"
DEFAULT_TIME = [0, 25, 0]

LANGUAGES = [("en", "English"), ("ru", "Русский"), ("zh", "中文")]

TEXTS = {
    "en": {
        "hours": "Hours", "minutes": "Minutes", "seconds": "Seconds",
        "start": "Start", "pause": "Pause", "resume": "Resume", "reset": "Reset",
        "focus": "FOCUS", "ready": "READY", "done": "Time's up!",
        "settings": "Settings", "language": "Language", "save": "Save",
        "settings_reset": "Reset",
    },
    "ru": {
        "hours": "Часы", "minutes": "Минуты", "seconds": "Секунды",
        "start": "Старт", "pause": "Пауза", "resume": "Продолжить", "reset": "Сбросить",
        "focus": "ФОКУС", "ready": "ГОТОВ", "done": "Время вышло!",
        "settings": "Настройки", "language": "Язык", "save": "Сохранить",
        "settings_reset": "Сбросить",
    },
    "zh": {
        "hours": "小时", "minutes": "分钟", "seconds": "秒",
        "start": "开始", "pause": "暂停", "resume": "继续", "reset": "重置",
        "focus": "专注", "ready": "准备", "done": "时间到！",
        "settings": "设置", "language": "语言", "save": "保存",
        "settings_reset": "重置",
    },
}


def _hex_to_rgb(color):
    base = color.lstrip("#")
    return [int(base[i:i + 2], 16) for i in (0, 2, 4)]


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in rgb)


def _shade(color, amount):
    rgb = _hex_to_rgb(color)
    if amount >= 0:
        rgb = [v + (255 - v) * amount for v in rgb]
    else:
        rgb = [v * (1 + amount) for v in rgb]
    return _rgb_to_hex(rgb)


def _mix(c1, c2, t):
    a, b = _hex_to_rgb(c1), _hex_to_rgb(c2)
    return _rgb_to_hex([x + (y - x) * t for x, y in zip(a, b)])


def _circle(c, cx, cy, r, **kw):
    return c.create_oval(cx - r, cy - r, cx + r, cy + r, **kw)


def _round_rect(c, x1, y1, x2, y2, r, **kw):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return c.create_polygon(points, smooth=True, **kw)


def _settings_dirs():
    dirs = []
    if getattr(sys, "frozen", False):
        dirs.append(os.path.dirname(sys.executable))
    dirs.append(os.path.dirname(os.path.abspath(__file__)))
    dirs.append(os.path.expanduser("~/.config/pomodoro"))
    unique = []
    for d in dirs:
        if d and d not in unique:
            unique.append(d)
    return unique


def _read_raw():
    for directory in _settings_dirs():
        try:
            with open(os.path.join(directory, SETTINGS_NAME), "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            return data
    return {}


def load_settings():
    data = _read_raw()
    lang = data.get("language")
    if lang not in TEXTS:
        lang = DEFAULT_LANG
    times = data.get("time")
    valid = (isinstance(times, list) and len(times) == 3
             and all(isinstance(v, int) and 0 <= v <= 99 for v in times))
    return lang, list(times) if valid else list(DEFAULT_TIME)


def save_settings(**updates):
    data = _read_raw()
    data.update(updates)
    for directory in _settings_dirs():
        try:
            os.makedirs(directory, exist_ok=True)
            with open(os.path.join(directory, SETTINGS_NAME), "w", encoding="utf-8") as handle:
                json.dump(data, handle)
            return
        except OSError:
            continue


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, color, bg=BG, fg="white",
                 width=118, height=40, radius=14, font=None,
                 outline="", text_color=None):
        super().__init__(parent, width=width, height=height, bg=bg,
                         highlightthickness=0, cursor="hand2")
        self.w = width
        self.h = height
        self.radius = radius
        self.color = color
        self.text = text
        self.command = command
        self.fg = text_color or fg
        self.font = font or ("Helvetica", 11, "bold")
        self.outline = outline
        self.hover = False
        self.pressed = False
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._paint()

    def set_text(self, text):
        self.text = text
        self._paint()

    def _on_enter(self, _event):
        self.hover = True
        self._paint()

    def _on_leave(self, _event):
        self.hover = False
        self.pressed = False
        self._paint()

    def _on_press(self, _event):
        self.pressed = True
        self._paint()

    def _on_release(self, _event):
        was_pressed = self.pressed
        self.pressed = False
        self._paint()
        if was_pressed and self.command:
            self.command()

    def _paint(self):
        self.delete("all")
        fill = self.color
        if self.pressed:
            fill = _shade(fill, -0.10)
        elif self.hover:
            fill = _shade(fill, 0.12)
        shadow = _shade(fill, -0.20)
        _round_rect(self, 1, 3, self.w - 1, self.h - 1, self.radius,
                    fill=shadow, outline="")
        _round_rect(self, 0, 0, self.w - 2, self.h - 3, self.radius,
                    fill=fill, outline=self.outline, width=1.5)
        self.create_text((self.w - 2) / 2, (self.h - 3) / 2, text=self.text,
                         font=self.font, fill=self.fg)


class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.lang, saved_time = load_settings()
        self.settings_window = None
        self.k = 1.0
        self.cx = BASE / 2
        self.cy = BASE / 2

        root.configure(bg=BG)
        root.title("Pomodoro")
        root.geometry("420x660")
        root.minsize(400, 600)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.running = False
        self.paused = False
        self.end_time = 0.0
        self.total = 0.0
        self.remaining = 0.0

        top_frame = tk.Frame(root, bg=BG)
        top_frame.pack(fill="x", padx=12, pady=(10, 0))
        self.gear_button = RoundedButton(
            top_frame, "⚙", self.open_settings, PLATE, bg=BG,
            width=46, height=42, radius=13,
            font=("Segoe UI Symbol", 17), text_color=TOMATO_RIM,
            outline=TRACK)
        self.gear_button.pack(side="right")

        button_frame = tk.Frame(root, bg=BG)
        button_frame.pack(side="bottom", pady=(6, 18))

        input_frame = tk.Frame(root, bg=BG)
        input_frame.pack(side="bottom")

        self.canvas = tk.Canvas(root, width=BASE, height=BASE,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(2, 4))
        self.canvas.bind("<Configure>", self._on_resize)

        vcmd = (root.register(self._validate), "%P")
        self.entries = []
        self.field_labels = []
        for i, default in enumerate(saved_time):
            label = tk.Label(input_frame, bg=BG, fg=MUTED,
                             font=("Helvetica", 9, "bold"))
            label.grid(row=0, column=i, padx=9)
            self.field_labels.append(label)
            entry = tk.Entry(input_frame, width=4, justify="center", relief="flat",
                             font=("Helvetica", 17, "bold"), fg=INK,
                             bg="white", highlightthickness=2,
                             highlightbackground=TRACK, highlightcolor=TOMATO,
                             validate="key", validatecommand=vcmd)
            entry.insert(0, str(default))
            entry.grid(row=1, column=i, padx=9, pady=(2, 0), ipady=5)
            self.entries.append(entry)

        self.start_button = RoundedButton(button_frame, "", self.start, TOMATO, bg=BG)
        self.start_button.pack(side="left", padx=4)
        self.pause_button = RoundedButton(button_frame, "", self.toggle_pause, "#f39c12", bg=BG)
        self.pause_button.pack(side="left", padx=4)
        self.reset_button = RoundedButton(button_frame, "", self.reset, GREY, bg=BG)
        self.reset_button.pack(side="left", padx=4)

        self.apply_language()
        self.reset()
        self._tick()

    def t(self, key):
        return TEXTS[self.lang][key]

    def apply_language(self):
        self.root.title("Pomodoro")
        for label, key in zip(self.field_labels, ("hours", "minutes", "seconds")):
            label.config(text=self.t(key).upper())
        self.start_button.set_text(self.t("start"))
        self.reset_button.set_text(self.t("reset"))
        self._update_pause_label()
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()
            self.settings_window = None
        self._draw()

    def _update_pause_label(self):
        self.pause_button.set_text(self.t("resume" if self.paused else "pause"))

    def open_settings(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title(self.t("settings"))
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self.root)
        self.settings_window = win

        var = tk.StringVar(master=win, value=self.lang)

        def save():
            self.lang = var.get()
            save_settings(language=self.lang)
            self.settings_window = None
            win.destroy()
            self.apply_language()

        def reset_to_default():
            var.set(DEFAULT_LANG)

        tk.Label(win, text=self.t("language"), bg=BG, fg=INK,
                 font=("Helvetica", 13, "bold")).pack(padx=30, pady=(20, 10))
        for code, name in LANGUAGES:
            tk.Radiobutton(win, text=name, value=code, variable=var, bg=BG, fg=INK,
                           activebackground=BG, activeforeground=INK,
                           selectcolor=PLATE, font=("Helvetica", 11),
                           anchor="w", relief="flat", bd=0,
                           highlightthickness=0,
                           cursor="hand2").pack(fill="x", padx=30, pady=3)

        buttons = tk.Frame(win, bg=BG)
        buttons.pack(pady=(18, 20))
        RoundedButton(buttons, self.t("save"), save, TOMATO, bg=BG,
                      width=124).pack(side="left", padx=5)
        RoundedButton(buttons, self.t("settings_reset"), reset_to_default,
                      GREY, bg=BG, width=124).pack(side="left", padx=5)

    @staticmethod
    def _validate(value):
        return value == "" or (value.isdigit() and len(value) <= 2)

    def _read_times(self):
        return [int(e.get() or 0) for e in self.entries]

    def _read_total(self):
        h, m, s = self._read_times()
        return h * 3600 + m * 60 + s

    def _remember_times(self):
        save_settings(time=self._read_times())

    def on_close(self):
        self._remember_times()
        self.root.destroy()

    def start(self):
        if self.running:
            return
        if not self.paused:
            total = self._read_total()
            if total <= 0:
                return
            self.total = total
            self.remaining = total
            self._remember_times()
        self.end_time = time.monotonic() + self.remaining
        self.running = True
        self.paused = False
        self._update_pause_label()

    def toggle_pause(self):
        if self.running:
            self.remaining = max(0.0, self.end_time - time.monotonic())
            self.running = False
            self.paused = True
            self._update_pause_label()
        elif self.paused:
            self.start()

    def reset(self):
        self.running = False
        self.paused = False
        self.total = self._read_total()
        self.remaining = self.total
        self._update_pause_label()
        self._draw()

    def _tick(self):
        if self.running:
            self.remaining = max(0.0, self.end_time - time.monotonic())
            if self.remaining <= 0:
                self.running = False
                self.paused = False
                self._update_pause_label()
                self._draw()
                messagebox.showinfo("Pomodoro", self.t("done"))
                self.root.after(50, self._tick)
                return
        self._draw()
        self.root.after(50, self._tick)

    def _on_resize(self, event):
        if event.width < 2 or event.height < 2:
            return
        self.k = max(0.25, min(event.width, event.height) / BASE)
        self.cx = event.width / 2
        self.cy = event.height / 2
        self._paint_backdrop(event.width, event.height)
        self._draw()

    def _paint_backdrop(self, width, height):
        c = self.canvas
        c.delete("bg")
        bands = 48
        step = height / bands
        for i in range(bands):
            color = _mix(GRAD_TOP, GRAD_BOTTOM, i / (bands - 1))
            c.create_rectangle(0, i * step, width, (i + 1) * step + 1,
                               fill=color, outline=color, tags="bg")
        c.tag_lower("bg")

    def _draw(self):
        c = self.canvas
        c.delete("clock")
        k, cx, cy = self.k, self.cx, self.cy

        def at(x, y):
            return cx + x * k, cy + y * k

        def circle(x, y, r, **kw):
            _circle(c, cx + x * k, cy + y * k, r * k, tags="clock", **kw)

        def width_px(w):
            return max(1, round(w * k))

        def poly(points, **kw):
            flat = [v for p in points for v in at(*p)]
            c.create_polygon(flat, tags="clock", **kw)

        def font(size, weight="bold"):
            return ("Helvetica", max(8, int(size * k)), weight)

        circle(4, 7, TOMATO_R, fill="#ead6cb", outline="")
        circle(0, 0, TOMATO_R, fill=TOMATO_RIM, outline="")
        circle(0, 0, TOMATO_R - 7, fill=TOMATO, outline="")
        circle(-34, -46, 30, fill=TOMATO_LIGHT, outline="")
        circle(-44, -54, 12, fill=TOMATO_GLOSS, outline="")

        circle(0, 0, FACE_R, fill="#ffffff", outline="")
        circle(0, 0, FACE_R - 1, fill="#fffdfb", outline=TRACK, width=width_px(1.5))

        for i in range(60):
            angle = math.radians(i * 6)
            major = i % 5 == 0
            inner = 85 if major else 90
            outer = 95
            x1, y1 = at(inner * math.sin(angle), -inner * math.cos(angle))
            x2, y2 = at(outer * math.sin(angle), -outer * math.cos(angle))
            c.create_line(x1, y1, x2, y2,
                          fill=TICK_MAJOR if major else TICK_MINOR,
                          width=width_px(2 if major else 1), tags="clock")

        elapsed = 1 - self.remaining / self.total if self.total > 0 else 0.0
        elapsed = min(max(elapsed, 0.0), 1.0)

        circle(0, 0, RING_R, outline=TRACK, width=width_px(6), fill="")
        if elapsed > 0:
            x1, y1 = at(-RING_R, -RING_R)
            x2, y2 = at(RING_R, RING_R)
            c.create_arc(x1, y1, x2, y2, start=90, extent=-360 * elapsed,
                         style="arc", outline=TOMATO, width=width_px(6), tags="clock")
            theta = math.radians(360 * elapsed)
            circle(RING_R * math.sin(theta), -RING_R * math.cos(theta), 5,
                   fill=TOMATO_RIM, outline="#ffffff", width=width_px(1.5))

        seconds = int(math.ceil(self.remaining))
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        text = "%02d:%02d:%02d" % (h, m, s) if h else "%02d:%02d" % (m, s)
        tx, ty = at(0, -8)
        c.create_text(tx, ty, text=text, font=font(27), fill=INK, tags="clock")

        status = self.t("focus") if self.running else self.t("ready")
        pill_color = TOMATO if self.running else "#efe5df"
        pill_text = "#ffffff" if self.running else MUTED
        pill_w = (96 if self.running else 78) * k
        px, py = at(0, 34)
        _round_rect(c, px - pill_w / 2, py - 12 * k, px + pill_w / 2, py + 12 * k,
                    11 * k, fill=pill_color, outline="", tags="clock")
        c.create_text(px, py, text=status, font=font(9), fill=pill_text, tags="clock")

        poly([(-15, -162), (15, -162), (0, -144)], fill=LEAF_DARK, outline="")
        poly([(0, -152), (-9, -164), (-26, -160), (-13, -148)], fill=LEAF, outline="", smooth=True)
        poly([(0, -152), (9, -164), (26, -160), (13, -148)], fill=LEAF_DARK, outline="", smooth=True)


if __name__ == "__main__":
    root = tk.Tk()
    PomodoroTimer(root)
    root.mainloop()
