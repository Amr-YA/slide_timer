import tkinter as tk
from slide_timer_core import image_hash, grab_footer, fmt_time


# ── HUD ───────────────────────────────────────────────────────────────────────
HUD_BG = "#333333"
HUD_FG = "#00FF00"
HUD_FONT = ("Helvetica", 14, "bold")
HUD_TEMPLATE = "Slide 99: 99:99"


class HUD(tk.Toplevel):
    """Single-line fixed-width HUD, dark grey background, bright green text."""

    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.8)
        self.configure(bg=HUD_BG)

        self._label = tk.Label(
            self,
            text=HUD_TEMPLATE,
            font=HUD_FONT,
            fg=HUD_FG,
            bg=HUD_BG,
            anchor="w",
            padx=4,
            pady=2,
            width=len(HUD_TEMPLATE),
        )
        self._label.pack()

        self._label.bind("<ButtonPress-1>", self._drag_start)
        self._label.bind("<B1-Motion>", self._drag_move)

        self.after(50, self._snap_top_right)

    def _snap_top_right(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        w = self.winfo_width()
        self.geometry(f"+{sw - w - 10}+10")

    def _drag_start(self, event):
        self._dx = event.x
        self._dy = event.y

    def _drag_move(self, event):
        x = self.winfo_x() + event.x - self._dx
        y = self.winfo_y() + event.y - self._dy
        self.geometry(f"+{x}+{y}")

    def show_countdown(self, n):
        self._label.config(text=f"Starting in {n}")

    def update_hud(self, slide_num, total_seconds):
        self._label.config(text=f"Slide {slide_num}: {fmt_time(total_seconds)}")


# ── Main app ──────────────────────────────────────────────────────────────────
COUNTDOWN_SECS = 3


class SlideTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Slide Timer")
        self.root.geometry("420x260")

        self.current_hash = None
        self.hash_counts = {}
        self.hash_order = {}
        self.slide_counter = 0
        self.running = False
        self.hud = None
        self._countdown_remaining = 0

        self.status_var = tk.StringVar(value="Press Start to begin.")
        self.top_var = tk.StringVar(value="Captured durations will appear here.")

        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, textvariable=self.status_var, anchor="w").pack(fill=tk.X)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(8, 10))

        self.start_button = tk.Button(
            btn_frame, text="Start", command=self.start_capture
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 8))
        self.stop_button = tk.Button(
            btn_frame, text="Stop", command=self.stop_capture, state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT)

        tk.Label(frame, text="Captured slide durations:", anchor="w").pack(fill=tk.X)
        tk.Label(
            frame,
            textvariable=self.top_var,
            anchor="w",
            justify=tk.LEFT,
            wraplength=380,
        ).pack(fill=tk.X)

    def start_capture(self):
        self.current_hash = None
        self.hash_counts.clear()
        self.hash_order.clear()
        self.slide_counter = 0
        self.running = True

        self.top_var.set("Captured durations will appear here.")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.root.iconify()
        if self.hud is None or not self.hud.winfo_exists():
            self.hud = HUD(self.root)
        else:
            self.hud.deiconify()
            self.hud.after(50, self.hud._snap_top_right)

        self._countdown_remaining = COUNTDOWN_SECS
        self._tick_countdown()

    def _tick_countdown(self):
        if not self.running:
            return
        if self._countdown_remaining > 0:
            if self.hud and self.hud.winfo_exists():
                self.hud.show_countdown(self._countdown_remaining)
            self._countdown_remaining -= 1
            self.root.after(1000, self._tick_countdown)
        else:
            # First captured frame becomes Slide 1 automatically
            self.capture_loop()

    def stop_capture(self):
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Capture stopped. Press Start to begin a new session.")
        if self.current_hash is not None:
            self.hash_counts[self.current_hash] = (
                self.hash_counts.get(self.current_hash, 0) + 1
            )
        self.update_top_display()

        if self.hud and self.hud.winfo_exists():
            self.hud.withdraw()
        self.root.deiconify()

    def get_slide_number(self, h):
        if h not in self.hash_order:
            self.slide_counter += 1
            self.hash_order[h] = self.slide_counter
        return self.hash_order[h]

    def capture_loop(self):
        if not self.running:
            return

        footer = grab_footer()
        screenshot_hash = image_hash(footer)
        self.get_slide_number(screenshot_hash)

        self.hash_counts[screenshot_hash] = self.hash_counts.get(screenshot_hash, 0) + 1
        self.current_hash = screenshot_hash

        self.update_top_display()

        if self.hud and self.hud.winfo_exists():
            self.hud.update_hud(
                self.hash_order.get(self.current_hash, "—"),
                self.hash_counts.get(self.current_hash, 0),
            )

        self.root.after(1000, self.capture_loop)

    def update_top_display(self):
        if not self.hash_counts:
            self.top_var.set("No screenshots captured yet.")
            return

        top_items = sorted(
            self.hash_counts.items(), key=lambda item: self.hash_order.get(item[0], 0)
        )
        lines = [
            f"{self.hash_order.get(h, '?')}  {fmt_time(s)}" for h, s in top_items[:10]
        ]
        self.top_var.set("\n".join(lines))
