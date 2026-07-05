import tkinter as tk
from slide_timer_app import SlideTimerApp


DEBUG = False


if __name__ == "__main__":
    root = tk.Tk()
    app = SlideTimerApp(root)
    app.debug_mode = DEBUG
    root.mainloop()
