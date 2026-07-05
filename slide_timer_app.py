import os
import tkinter as tk
from tkinter import font
from slide_timer_core import image_hash, grab_footer, fmt_time, get_dir


# ── HUD ───────────────────────────────────────────────────────────────────────
HUD_BG = "#333333"
HUD_FG = "#00FF00"
HUD_FONT = ("Consolas", 14, "bold")
HUD_TEMPLATE = """
    Slide 99: 99:99
    \n
    Total  : 00:00"""


class HUD(tk.Toplevel):
    """Two-line fixed-width HUD, dark grey background, bright green text."""

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
            justify="left",
            padx=4,
            pady=2,
            width=max(len(line) for line in HUD_TEMPLATE.splitlines()),
        )
        self._label.pack()

        self._label.bind("<ButtonPress-1>", self._drag_start)
        self._label.bind("<B1-Motion>", self._drag_move)
        self._label.bind("<ButtonRelease-1>", self._on_button_release)

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
        self._dragged = True
        x = self.winfo_x() + event.x - self._dx
        y = self.winfo_y() + event.y - self._dy
        self.geometry(f"+{x}+{y}")

    def show_countdown(self, n):
        self._label.config(text=f"Starting in {n}...")

    def _on_button_release(self, event=None):
        if getattr(self, "_dragged", False):
            self._dragged = False
            return
        self._restore_main()

    def _restore_main(self, event=None):
        if self.master is not None:
            self.master.deiconify()
            self.lift()

    def update_hud(self, slide_num, slide_seconds, total_seconds):
        self._label.config(
            text=f"Slide {slide_num}: {fmt_time(slide_seconds)}\nTotal  : {fmt_time(total_seconds)}"
        )


# ── Main app ──────────────────────────────────────────────────────────────────
COUNTDOWN_SECS = 3


class SlideTimerApp:
    def __init__(self, root):
        self.root = root

        self.current_hash = None
        self.hash_counts = {}
        self.hash_order = {}
        self.slide_counter = 0
        self.running = False
        self.hud = None
        self._countdown_remaining = 0
        self.debug_mode = True
        self.debug_folder = None

        self.status_var = tk.StringVar(value="Press Start to begin.")
        self.top_var = tk.StringVar(value="Captured durations will appear here.")
        self.countdown_var = tk.IntVar(value=COUNTDOWN_SECS)
        self.debug_var = tk.StringVar(value="")

        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, textvariable=self.status_var, anchor="w").pack(fill=tk.X)

        # Countdown control
        count_frame = tk.Frame(frame)
        count_frame.pack(fill=tk.X, pady=(6, 4))
        tk.Label(count_frame, text="Countdown (s):", anchor="w").pack(side=tk.LEFT)
        self.countdown_spin = tk.Spinbox(
            count_frame, from_=0, to=60, width=5, textvariable=self.countdown_var
        )
        self.countdown_spin.pack(side=tk.LEFT, padx=(6, 0))

        # bind F9 to toggle debug mode when app is not running
        try:
            self.root.bind("<F9>", self._on_f9)
        except Exception:
            pass

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

        # separate debug message line at bottom (does not overwrite status)
        tk.Label(frame, textvariable=self.debug_var, anchor="w", fg="#FFAA00").pack(
            fill=tk.X, pady=(6, 0)
        )

    def start_capture(self):
        self.current_hash = None
        self.hash_counts.clear()
        self.hash_order.clear()
        self.slide_counter = 0
        self.running = True

        self.top_var.set("Captured durations will appear here.")
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        # disable countdown while running
        try:
            self.countdown_spin.config(state=tk.DISABLED)
        except Exception:
            pass

        self.root.iconify()
        if self.debug_mode:
            self.debug_folder = os.path.join(
                get_dir(), "debug_screenshots"
            )
            os.makedirs(self.debug_folder, exist_ok=True)

        if self.hud is None or not self.hud.winfo_exists():
            self.hud = HUD(self.root)
        else:
            self.hud.deiconify()
            self.hud.after(50, self.hud._snap_top_right)

        try:
            secs = int(self.countdown_var.get())
        except Exception:
            secs = COUNTDOWN_SECS
        self._countdown_remaining = max(0, secs)
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
        # re-enable countdown when stopped
        try:
            self.countdown_spin.config(state=tk.NORMAL)
        except Exception:
            pass
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

    def _save_debug_screenshot(self, image, slide_number):
        if self.debug_folder is None:
            self.debug_folder = os.path.join(
                get_dir(), "debug_screenshots"
            )
            os.makedirs(self.debug_folder, exist_ok=True)

        path = os.path.join(self.debug_folder, f"slide-{slide_number:02d}.jpg")
        image.convert("RGB").save(path, "JPEG", quality=85)

    def capture_loop(self):
        if not self.running:
            return

        footer = grab_footer()
        screenshot_hash = image_hash(footer)
        is_new_slide = screenshot_hash not in self.hash_order
        self.get_slide_number(screenshot_hash)

        if self.debug_mode and is_new_slide:
            self._save_debug_screenshot(
                footer, self.hash_order[screenshot_hash]
            )

        self.hash_counts[screenshot_hash] = self.hash_counts.get(screenshot_hash, 0) + 1
        self.current_hash = screenshot_hash

        self.update_top_display()

        if self.hud and self.hud.winfo_exists():
            self.hud.update_hud(
                self.hash_order.get(self.current_hash, "—"),
                self.hash_counts.get(self.current_hash, 0),
                sum(self.hash_counts.values()),
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
        total_seconds = sum(self.hash_counts.values())
        lines.append(f"Total: {fmt_time(total_seconds)}")
        self.top_var.set("\n".join(lines))

    def _on_f9(self, event=None):
        # Only allow toggling debug mode when not running
        if getattr(self, "running", False):
            return

        # Toggle debug flag
        self.debug_mode = not getattr(self, "debug_mode", False)
        # If debug was turned on, display message on separate debug line; otherwise clear it
        try:
            if self.debug_mode:
                self.debug_var.set("DEBUG: ON")
            else:
                self.debug_var.set("")
        except Exception:
            pass
        