import ctypes
from ctypes import wintypes
import tkinter as tk

user32 = ctypes.WinDLL("user32", use_last_error=True)

# =========================
# CONSTANTS
# =========================

WM_POINTERUPDATE = 0x0245
PT_TOUCHPAD = 0x00000005
GWL_WNDPROC = -4


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
root.title("TrackPadDrums - Touchpad Probe")
root.geometry("600x300")

label = tk.Label(
    root,
    text="Put TWO fingers on the trackpad and move them",
    font=("Arial", 18),
    justify="center"
)
label.pack(expand=True)

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

                    output = (
                        f"TOUCHPAD\n"
                        f"ID: {pointer_id}\n"
                        f"X: {x}\n"
                        f"Y: {y}"
                    )

                    print(output)

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
