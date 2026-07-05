import tkinter as tk
from slide_timer_app import SlideTimerApp


DEBUG = False


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Slide Timer")
    root.geometry("380x200")
    img = tk.PhotoImage(file="./assets/timer32.png")
    root.iconphoto(True, img)
    
    app = SlideTimerApp(root)
    app.debug_mode = DEBUG
    root.mainloop()
