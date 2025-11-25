import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
import numpy as np

# Sample data
t = np.linspace(0, 10, 500)
y = np.sin(t * 2) * 20  # pretend PID values

root = tk.Tk()
root.title("Chart with Scrubber")

# --- Create the Matplotlib Figure ---
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(t, y)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Value")

# A vertical line that we will move with the slider
cursor_line = ax.axvline(x=t[0], color='red', linewidth=2)

# --- Embed the figure in Tkinter ---
canvas = FigureCanvasTkAgg(fig, master=root)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill="both", expand=True)

# --- Slider callback ---
def on_scrub(value):
    # value comes in as string from Tkinter, so convert to float
    x = float(value)
    cursor_line.set_xdata([x, x])
    canvas.draw_idle()

# --- Slider widget (pure Tkinter) ---
slider = tk.Scale(
    root,
    from_=t.min(),
    to=t.max(),
    resolution=(t.max() - t.min()) / len(t),
    orient="horizontal",
    length=500,
    command=on_scrub,
    label="Scrub Through Time"
)
slider.pack(pady=10)

root.mainloop()
