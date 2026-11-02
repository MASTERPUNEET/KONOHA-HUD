
#!/usr/bin/env python3
"""KONOHA HUD - Desktop system monitor for Linux."""

import os
import time
import platform
import tkinter as tk

import psutil
from PIL import Image, ImageTk, ImageEnhance, ImageFilter, ImageOps

W, H = 520, 380
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Optional images: place your own files beside this script.
BG_PATH = os.path.join(APP_DIR, "background.png")
AVATAR_PATH = os.path.join(APP_DIR, "portrait.png")

ORANGE = "#ff9d28"
CYAN = "#56cfff"
CYAN2 = "#1e9bd5"
WHITE = "#f3f7ff"
MUTED = "#b9cde0"
PANEL = "#0a2038"

root = tk.Tk()
root.title("KONOHA HUD")
root.geometry(f"{W}x{H}+480+80")
root.resizable(False, False)
root.overrideredirect(False)
root.attributes("-topmost", False)

canvas = tk.Canvas(
    root, width=W, height=H,
    highlightthickness=0, bd=0, bg="#071525"
)
canvas.pack(fill="both", expand=True)

# Optional background image.
try:
    source = Image.open(BG_PATH).convert("RGB")
    cover = ImageOps.fit(
        source, (W, H), method=Image.Resampling.LANCZOS
    )
    blurred = cover.filter(ImageFilter.GaussianBlur(10))
    blurred = ImageEnhance.Brightness(blurred).enhance(0.48)

    sharp_h = H
    sharp_w = max(1, int(source.width * sharp_h / source.height))
    sharp = source.resize(
        (sharp_w, sharp_h), Image.Resampling.LANCZOS
    )
    sharp = ImageEnhance.Brightness(sharp).enhance(0.82)

    x = (W - sharp_w) // 2
    blurred.paste(sharp, (x, 0))

    bg_photo = ImageTk.PhotoImage(blurred)
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")
except (FileNotFoundError, OSError):
    pass

# Dark tint.
canvas.create_rectangle(
    0, 0, W, H, fill="#020914",
    stipple="", outline=""
)

# Drag with left mouse; right-click closes.
def drag_start(event):
    root._dx = event.x_root - root.winfo_x()
    root._dy = event.y_root - root.winfo_y()


def drag_move(event):
    root.geometry(
        f"+{event.x_root-root._dx}+{event.y_root-root._dy}"
    )


canvas.bind("<Button-1>", drag_start)
canvas.bind("<B1-Motion>", drag_move)
canvas.bind("<Button-3>", lambda _event: root.destroy())


def panel(x1, y1, x2, y2, fill=PANEL):
    points = [
        x1+7, y1, x2-12, y1, x2, y1+9, x2, y2-8,
        x2-9, y2, x1+10, y2, x1, y2-9, x1, y1+9
    ]
    canvas.create_polygon(
        points, fill=fill, stipple="",
        outline=CYAN, width=1.8
    )
    canvas.create_line(
        x1+13, y1+3, x2-22, y1+3,
        fill="#b9eaff", width=1.5
    )
    canvas.create_line(
        x1+8, y2-4, x2-14, y2-4,
        fill="#258fc0", width=1.3
    )


def text(x, y, value, size=9, color=WHITE,
         bold=False, anchor="nw"):
    return canvas.create_text(
        x, y, text=value, fill=color,
        font=("DejaVu Sans", size,
              "bold" if bold else "normal"),
        anchor=anchor
    )


def progress(x, y, width, pct, color=CYAN, height=7):
    canvas.create_rectangle(
        x, y, x+width, y+height,
        outline="#d9edff", width=1
    )
    amount = max(0, min(width-2, (width-2)*pct/100))
    canvas.create_rectangle(
        x+1, y+1, x+1+amount, y+height-1,
        fill=color, outline=""
    )


# Header.
panel(8, 7, 342, 48)
text(19, 13, "🍃 KONOHA HUD", 17, ORANGE, True)
text(322, 15, "///", 15, CYAN, True, "ne")

# System status.
panel(8, 55, 342, 112)
text(18, 61, "SYSTEM STATUS", 10, ORANGE, True)
time_id = text(18, 79, "Time: --:--:--", 9)
date_id = text(18, 95, "Date: --", 9)

# Shikamaru identity panel.
panel(350, 7, 512, 112)

try:
    avatar = Image.open(AVATAR_PATH).convert("RGBA")
    avatar.thumbnail((66, 88), Image.Resampling.LANCZOS)
    avatar = ImageEnhance.Brightness(avatar).enhance(1.35)
    avatar = ImageEnhance.Contrast(avatar).enhance(1.12)

    avatar_photo = ImageTk.PhotoImage(avatar)
    x = 359 + (66-avatar.width)//2
    y = 15 + (88-avatar.height)//2
    canvas.create_image(x, y, image=avatar_photo, anchor="nw")
except (FileNotFoundError, OSError):
    text(361, 25, "KONOHA", 10, WHITE, True)

text(466, 27, "SHIKAMARU", 8, ORANGE, True, "center")
canvas.create_line(430, 48, 501, 48, fill=CYAN, width=1)
text(466, 59, "Think...", 9, WHITE, False, "center")
text(466, 78, "奈良シカマル", 7, MUTED, False, "center")

# CPU panel.
panel(8, 119, 257, 222)
text(18, 125, "CPU", 11, ORANGE, True)
cpu_value = text(47, 180, "0%", 12, WHITE, True, "center")
canvas.create_oval(
    21, 148, 75, 202, outline="#d9efff", width=1.5
)
cpu_arc = canvas.create_arc(
    21, 148, 75, 202, start=90, extent=0,
    style="arc", outline=CYAN, width=4
)
cpu_hist = [0.0] * 30
cpu_graph_tag = "cpu_graph"

# Memory panel.
panel(8, 229, 257, 303)
text(18, 235, "MEMORY", 11, ORANGE, True)
ram_value = text(18, 253, "RAM: -- / --", 8)
ram_pct = text(18, 274, "--%", 10, WHITE, True)
progress(64, 278, 177, 0, CYAN, 7)
ram_fill = canvas.create_rectangle(
    65, 279, 65, 284, fill=CYAN, outline=""
)

# Storage panel.
panel(265, 119, 512, 202)
text(276, 125, "STORAGE", 11, ORANGE, True)
disk_value = text(276, 145, "Root: -- / --", 8)
disk_pct = text(276, 166, "--%", 10, WHITE, True)
progress(315, 171, 181, 0, "#67f2a2", 7)
disk_fill = canvas.create_rectangle(
    316, 172, 316, 177, fill="#67f2a2", outline=""
)

# Network panel.
panel(265, 210, 512, 303)
text(276, 216, "NETWORK", 11, ORANGE, True)
down_value = text(276, 236, "Down: --", 8)
up_value = text(276, 253, "Up: --", 8)
network_history = [0.0] * 32

# Uptime panel.
panel(8, 310, 257, 372)
text(18, 316, "UPTIME", 11, ORANGE, True)
uptime_value = text(18, 338, "--", 15, WHITE, True)

# Operating system panel.
panel(265, 310, 512, 372)
text(276, 316, "OS", 11, ORANGE, True)

try:
    os_name = platform.freedesktop_os_release().get(
        "PRETTY_NAME", "Linux"
    )
except (AttributeError, OSError):
    os_name = platform.system()

text(276, 340, "◉  " + os_name, 10, WHITE, True)


def fmt_bytes(value):
    value = float(value)
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024


def uptime_string():
    with open("/proc/uptime", "r", encoding="utf-8") as file:
        seconds = int(float(file.read().split()[0]))

    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)

    if days:
        return f"{days}d {hours}h {minutes}m"
    return f"{hours}h {minutes}m {secs}s"


previous_net = psutil.net_io_counters()
previous_time = time.time()
psutil.cpu_percent(interval=None)


def draw_graph(tag, values, x1, y1, x2, y2, color):
    canvas.delete(tag)
    maximum = max(10.0, max(values)*1.15)
    coords = []

    for i, val in enumerate(values):
        x = x1 + i*(x2-x1)/(len(values)-1)
        y = y2 - min(1.0, val/maximum)*(y2-y1)
        coords.extend((x, y))

    canvas.create_line(
        *coords, fill=color, width=2.2,
        smooth=True, tags=tag
    )


def update():
    global previous_net, previous_time

    now = time.time()
    cpu = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    elapsed = max(0.1, now-previous_time)
    down = max(
        0, (net.bytes_recv-previous_net.bytes_recv)/elapsed
    )
    up = max(
        0, (net.bytes_sent-previous_net.bytes_sent)/elapsed
    )

    previous_net = net
    previous_time = now

    canvas.itemconfigure(
        time_id, text="Time: " + time.strftime("%H:%M:%S")
    )
    canvas.itemconfigure(
        date_id, text="Date: " + time.strftime("%d-%m-%Y")
    )

    # CPU.
    canvas.itemconfigure(cpu_value, text=f"{cpu:.0f}%")
    canvas.itemconfigure(cpu_arc, extent=-3.6*cpu)
    cpu_hist.append(cpu)
    del cpu_hist[0]

    draw_graph(
        cpu_graph_tag, cpu_hist,
        91, 159, 244, 204, CYAN
    )

    # RAM.
    canvas.itemconfigure(
        ram_value,
        text=f"RAM: {fmt_bytes(memory.used)} / "
             f"{fmt_bytes(memory.total)}"
    )
    canvas.itemconfigure(ram_pct, text=f"{memory.percent:.0f}%")
    canvas.coords(
        ram_fill, 65, 279,
        65+175*memory.percent/100, 284
    )

    # Storage.
    canvas.itemconfigure(
        disk_value,
        text=f"Root: {fmt_bytes(disk.used)} / "
             f"{fmt_bytes(disk.total)}"
    )
    canvas.itemconfigure(disk_pct, text=f"{disk.percent:.0f}%")
    canvas.coords(
        disk_fill, 316, 172,
        316+179*disk.percent/100, 177
    )

    # Network.
    canvas.itemconfigure(
        down_value,
        text="Down: " + fmt_bytes(down) + "/s"
    )
    canvas.itemconfigure(
        up_value,
        text="Up: " + fmt_bytes(up) + "/s"
    )

    network_history.append(down+up)
    del network_history[0]

    draw_graph(
        "network_graph", network_history,
        365, 267, 498, 291, CYAN
    )

    # Uptime.
    canvas.itemconfigure(
        uptime_value, text=uptime_string()
    )

    root.after(150, update)


update()
root.mainloop()
