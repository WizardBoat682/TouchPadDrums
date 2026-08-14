import ctypes
import winsound
from ctypes import wintypes
import tkinter as tk
import threading
import os
import sys
import time
user32 = ctypes.WinDLL("user32", use_last_error=True)



# =========================
# CONSTANTS
# =========================

WM_POINTERUPDATE = 0x0245
WM_POINTERDOWN = 0x0246
WM_POINTERUP = 0x0247
PT_TOUCHPAD = 0x00000005
GWL_WNDPROC = -4

#=========================
#ValueTable
#=========================

X_MIN = 900
X_MAX = 10200
Y_MIN = 200
Y_MAX = 6900

X_MID = (X_MIN + X_MAX) / 2

Y_THIRD_1 = Y_MIN + (Y_MAX - Y_MIN) / 3
Y_THIRD_2 = Y_MIN + 2 * (Y_MAX - Y_MIN) / 3


def get_zone(x, y):

    # Your trackpad reports larger X values on the LEFT
    left = x > X_MID

    if y < Y_THIRD_1:
        return "HI-HAT" if left else "CRASH"

    elif y < Y_THIRD_2:
        return "SNARE" if left else "TOM"

    else:
        return "KICK" if left else "CLAP"

def play_drum(zone):
    sounds = {
        "HI-HAT": resource_path("sounds/hihat.wav"),
        "CRASH": resource_path("sounds/crash.wav"),
        "SNARE": resource_path("sounds/snare.wav"),
        "TOM": resource_path("sounds/tom.wav"),
        "KICK": resource_path("sounds/kick.wav"),
        "CLAP": resource_path("sounds/clap.wav"),
    }

    winsound.PlaySound(
        sounds[zone],
        winsound.SND_FILENAME | winsound.SND_ASYNC
    )

last_hit_time = 0
HIT_COOLDOWN = 0.1


def trigger_drum(zone):
    global last_hit_time

    now = time.perf_counter()

    if now - last_hit_time < HIT_COOLDOWN:
        return

    last_hit_time = now
    play_drum(zone)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# =========================
# WINDOWS STRUCTURES
# =========================

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long)
    ]


class POINTER_INFO(ctypes.Structure):
    _fields_ = [
        ("pointerType", ctypes.c_uint32),
        ("pointerId", ctypes.c_uint32),
        ("frameId", ctypes.c_uint32),
        ("pointerFlags", ctypes.c_int32),
        ("sourceDevice", wintypes.HANDLE),
        ("hwndTarget", wintypes.HWND),
        ("ptPixelLocation", POINT),
        ("ptHimetricLocation", POINT),
        ("ptPixelLocationRaw", POINT),
        ("ptHimetricLocationRaw", POINT),
        ("dwTime", ctypes.c_uint32),
        ("historyCount", ctypes.c_uint32),
        ("InputData", ctypes.c_int32),
        ("dwKeyStates", ctypes.c_uint32),
        ("PerformanceCount", ctypes.c_uint64),
        ("ButtonChangeType", ctypes.c_int32),
    ]


class POINTER_TOUCH_INFO(ctypes.Structure):
    _fields_ = [
        ("pointerInfo", POINTER_INFO),
        ("touchFlags", ctypes.c_uint32),
        ("touchMask", ctypes.c_uint32),
        ("rcContact", wintypes.RECT),
        ("rcContactRaw", wintypes.RECT),
        ("orientation", ctypes.c_uint32),
        ("pressure", ctypes.c_uint32),
    ]


# =========================
# API DEFINITIONS
# =========================

user32.RegisterTouchpadCapableWindow.argtypes = [
    wintypes.HWND,
    wintypes.BOOL
]
user32.RegisterTouchpadCapableWindow.restype = wintypes.BOOL


user32.GetPointerInfo.argtypes = [
    ctypes.c_uint32,
    ctypes.POINTER(POINTER_INFO)
]
user32.GetPointerInfo.restype = wintypes.BOOL


user32.GetPointerTouchpadInfo.argtypes = [
    ctypes.c_uint32,
    ctypes.POINTER(POINTER_TOUCH_INFO)
]
user32.GetPointerTouchpadInfo.restype = wintypes.BOOL


SetWindowLongPtrW = user32.SetWindowLongPtrW
SetWindowLongPtrW.argtypes = [
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_void_p
]
SetWindowLongPtrW.restype = ctypes.c_void_p


CallWindowProcW = user32.CallWindowProcW
CallWindowProcW.argtypes = [
    ctypes.c_void_p,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
]
CallWindowProcW.restype = ctypes.c_ssize_t


# =========================
# CREATE WINDOW
# =========================

root = tk.Tk()
root.title("WizardBoat - TrackPadDrums")
root.geometry("700x520")
root.configure(bg="#181818")
title = tk.Label(
    root,
    text="WIZARDBOAT'S TRACKPAD DRUMS",
    font=("Arial", 24, "bold"),
    fg="white",
    bg="#181818"
)
title.pack(pady=(20, 5))

label = tk.Label(
    root,
    text="Two fingers • Move across your touchpad to play",
    font=("Arial", 14),
    justify="center",
    fg="#aaaaaa",
    bg="#181818"
)
label.pack(expand=True)
pads_frame = tk.Frame(
    root,
    bg="#181818"
)

pads_frame.pack(
    fill="both",
    expand=True,
    padx=40,
    pady=10
)

canvas = tk.Canvas(
    pads_frame,
    bg="#181818",
    highlightthickness=0
)

canvas.place(
    relx=0,
    rely=0,
    relwidth=1,
    relheight=1
)


root.update()

hwnd = root.winfo_id()

print("HWND:", hwnd)

result = user32.RegisterTouchpadCapableWindow(hwnd, True)

print("Touchpad registration:", bool(result))

if not result:
    raise ctypes.WinError(ctypes.get_last_error())


# =========================
# WINDOW MESSAGE HANDLER
# =========================

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM
)


def get_pointer_id(wparam):
    return wparam & 0xFFFF


old_proc = None


@WNDPROC
def window_proc(hwnd, msg, wparam, lparam):

    if msg == WM_POINTERUPDATE:
        pointer_id = get_pointer_id(wparam)

        info = POINTER_INFO()

        if user32.GetPointerInfo(pointer_id, ctypes.byref(info)):

            if info.pointerType == PT_TOUCHPAD:

                touch = POINTER_TOUCH_INFO()

                success = user32.GetPointerTouchpadInfo(
                    pointer_id,
                    ctypes.byref(touch)
                )

                if success:

                    x = touch.pointerInfo.ptHimetricLocation.x
                    y = touch.pointerInfo.ptHimetricLocation.y
                    zone = get_zone(x, y)

                    output = (
                        f"ZONE: {zone}\n\n"
                        f"X: {x}\n"
                        f"Y: {y}"
                    )

                    print(f"{zone} | X={x}, Y={y}")
                    trigger_drum(zone)
                    label.config(text=output)

    return CallWindowProcW(
        old_proc,
        hwnd,
        msg,
        wparam,
        lparam
    )


# =========================
# REPLACE TKINTER'S
# WINDOW PROCEDURE
# =========================

old_proc = SetWindowLongPtrW(
    hwnd,
    GWL_WNDPROC,
    ctypes.cast(window_proc, ctypes.c_void_p)
)

if not old_proc:
    raise ctypes.WinError(ctypes.get_last_error())


print("Listening for Precision Touchpad input...")
print("Try moving TWO fingers on your trackpad.")

root.mainloop()
