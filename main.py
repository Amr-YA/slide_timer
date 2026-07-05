import tkinter as tk
from slide_timer_app import SlideTimerApp
import base64

# BUILD
# pyinstaller --onefile --windowed --icon=./assets/timer.ico main.py

# TODO make screenshot not register unless it's on screen for 2 consecutive seconds
# TODO make footer screen selectable
# TODO Fix Debug mode not saving screenshots after pyinstaller build

DEBUG = False

# Icon PNG to Base64
# run the following command to convert a PNG to Base64:
# python -c "import base64; print(base64.b64encode(open('./assets/timer32.png','rb').read()).decode())"

ICON_B64 = """
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
"""

if __name__ == "__main__":
    root = tk.Tk()

    root.title("Slide Timer")
    root.geometry("380x200")
    
    icon_data = base64.b64decode(ICON_B64)
    img = tk.PhotoImage(data=icon_data)
    root.iconphoto(True, img)

    app = SlideTimerApp(root)
    app.debug_mode = DEBUG
    root.mainloop()
