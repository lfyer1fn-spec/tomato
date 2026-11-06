import math
import time
import tkinter as tk
from tkinter import messagebox

CANVAS_SIZE = 320
CENTER = CANVAS_SIZE / 2
TOMATO_R = 135
FACE_R = 110
HAND_R = 92

BG = "#fdf6f0"
TOMATO_DARK = "#c0392b"
TOMATO = "#e74c3c"
TOMATO_LIGHT = "#ff7b6b"
LEAF = "#27ae60"
LEAF_DARK = "#1e8449"
INK = "#2c3e50"
TRACK = "#f5d5cf"


def _circle(c, cx, cy, r, **kw):
    return c.create_oval(cx - r, cy - r, cx + r, cy + r, **kw)


class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        root.title("Pomodoro Timer")
        root.configure(bg=BG)
        root.resizable(False, False)

        self.running = False
        self.paused = False
        self.end_time = 0.0
        self.total = 0.0
        self.remaining = 0.0

        self.canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(pady=(14, 6))

        input_frame = tk.Frame(root, bg=BG)
        input_frame.pack()
        vcmd = (root.register(self._validate), "%P")
        self.entries = []
        for i, (label, default) in enumerate([("Часы", 0), ("Минуты", 25), ("Секунды", 0)]):
            tk.Label(input_frame, text=label, bg=BG, fg=INK,
                     font=("Helvetica", 10)).grid(row=0, column=i, padx=8)
            entry = tk.Entry(input_frame, width=5, justify="center", relief="flat",
                             font=("Helvetica", 14, "bold"), fg=INK,
                             bg="white", highlightthickness=2,
                             highlightbackground=TRACK, highlightcolor=TOMATO,
                             validate="key", validatecommand=vcmd)
            entry.insert(0, str(default))
            entry.grid(row=1, column=i, padx=8, pady=4, ipady=4)
            self.entries.append(entry)

        button_frame = tk.Frame(root, bg=BG)
        button_frame.pack(pady=(10, 16))
        self.start_button = self._make_button(button_frame, "Старт", TOMATO, self.start)
        self.pause_button = self._make_button(button_frame, "Пауза", "#f39c12", self.toggle_pause)
        self._make_button(button_frame, "Сбросить", "#7f8c8d", self.reset)

        self.reset()
        self._tick()

    def _make_button(self, parent, text, color, command):
        button = tk.Button(parent, text=text, command=command, width=9,
                           bg=color, fg="white", activebackground=color,
                           activeforeground="white", relief="flat", bd=0,
                           font=("Helvetica", 11, "bold"), cursor="hand2",
                           padx=6, pady=6)
        button.pack(side="left", padx=5)
        return button

    @staticmethod
    def _validate(value):
        return value == "" or (value.isdigit() and len(value) <= 2)

    def _read_total(self):
        h, m, s = (int(e.get() or 0) for e in self.entries)
        return h * 3600 + m * 60 + s

    def start(self):
        if self.running:
            return
        if not self.paused:
            total = self._read_total()
            if total <= 0:
                return
            self.total = total
            self.remaining = total
        self.end_time = time.monotonic() + self.remaining
        self.running = True
        self.paused = False
        self.pause_button.config(text="Пауза")

    def toggle_pause(self):
        if self.running:
            self.remaining = max(0.0, self.end_time - time.monotonic())
            self.running = False
            self.paused = True
            self.pause_button.config(text="Продолжить")
        elif self.paused:
            self.start()

    def reset(self):
        self.running = False
        self.paused = False
        self.total = self._read_total()
        self.remaining = self.total
        self.pause_button.config(text="Пауза")
        self._draw()

    def _tick(self):
        if self.running:
            self.remaining = max(0.0, self.end_time - time.monotonic())
            if self.remaining <= 0:
                self.running = False
                self.pause_button.config(text="Пауза")
                self._draw()
                messagebox.showinfo("Pomodoro", "Время вышло!")
                self.root.after(50, self._tick)
                return
        self._draw()
        self.root.after(50, self._tick)

    def _draw(self):
        c = self.canvas
        c.delete("all")

        _circle(c, CENTER + 5, CENTER + 8, TOMATO_R, fill="#eadcd5", outline="")

        _circle(c, CENTER, CENTER, TOMATO_R, fill=TOMATO_DARK, outline="")
        _circle(c, CENTER, CENTER, TOMATO_R - 6, fill=TOMATO, outline="")
        _circle(c, CENTER - 40, CENTER - 45, 26, fill=TOMATO_LIGHT, outline="")

        _circle(c, CENTER, CENTER, FACE_R, fill="white", outline="")
        _circle(c, CENTER, CENTER, FACE_R - 1, fill="#fffdfb", outline=TRACK, width=2)

        ring_r = FACE_R - 9
        _circle(c, CENTER, CENTER, ring_r, outline=TRACK, width=8, fill="")
        elapsed = 1 - self.remaining / self.total if self.total > 0 else 0.0
        elapsed = min(max(elapsed, 0.0), 1.0)
        if elapsed > 0:
            c.create_arc(CENTER - ring_r, CENTER - ring_r,
                         CENTER + ring_r, CENTER + ring_r,
                         start=90, extent=-360 * elapsed,
                         style="arc", outline=TOMATO, width=8)

        for i in range(60):
            angle = math.radians(i * 6)
            outer = FACE_R - 16
            inner = outer - (7 if i % 5 == 0 else 3)
            c.create_line(CENTER + inner * math.sin(angle), CENTER - inner * math.cos(angle),
                          CENTER + outer * math.sin(angle), CENTER - outer * math.cos(angle),
                          fill=INK if i % 5 == 0 else "#bdc3c7",
                          width=2 if i % 5 == 0 else 1)

        theta = math.radians(360 * elapsed)
        hand_x = CENTER + HAND_R * math.sin(theta)
        hand_y = CENTER - HAND_R * math.cos(theta)
        c.create_line(CENTER, CENTER, hand_x, hand_y,
                      fill=TOMATO_DARK, width=3, capstyle="round")
        _circle(c, CENTER, CENTER, 6, fill=INK, outline="")

        c.create_polygon(CENTER - 16, 18, CENTER + 16, 18, CENTER, 32,
                         fill=TOMATO_DARK, outline="")

        c.create_polygon(CENTER, 14, CENTER - 8, 4, CENTER - 22, 10, CENTER - 12, 18,
                         fill=LEAF, outline="", smooth=True)
        c.create_polygon(CENTER, 14, CENTER + 8, 4, CENTER + 22, 10, CENTER + 12, 18,
                         fill=LEAF_DARK, outline="", smooth=True)

        seconds = int(math.ceil(self.remaining))
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        text = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        c.create_text(CENTER, CENTER + 46, text=text,
                      font=("Helvetica", 20, "bold"), fill=INK)
        c.create_text(CENTER, CENTER + 70, text="ФОКУС" if self.running else "ГОТОВ",
                      font=("Helvetica", 9, "bold"),
                      fill=TOMATO if self.running else "#95a5a6")


if __name__ == "__main__":
    root = tk.Tk()
    PomodoroTimer(root)
    root.mainloop()
