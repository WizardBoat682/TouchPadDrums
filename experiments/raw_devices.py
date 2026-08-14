import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIM_TYPEHID = 2


class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [
        ("hDevice", wintypes.HANDLE),
        ("dwType", wintypes.DWORD)
    ]


GetRawInputDeviceList = user32.GetRawInputDeviceList
GetRawInputDeviceList.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(wintypes.UINT),
    wintypes.UINT
]
GetRawInputDeviceList.restype = wintypes.UINT


# First ask Windows: "How many devices?"
count = wintypes.UINT(0)

result = GetRawInputDeviceList(
    None,
    ctypes.byref(count),
    ctypes.sizeof(RAWINPUTDEVICELIST)
)

if result == 0xFFFFFFFF:
    raise ctypes.WinError(ctypes.get_last_error())


# Create space for them
devices = (RAWINPUTDEVICELIST * count.value)()


# Ask Windows to fill the list
result = GetRawInputDeviceList(
    devices,
    ctypes.byref(count),
    ctypes.sizeof(RAWINPUTDEVICELIST)
)

if result == 0xFFFFFFFF:
    raise ctypes.WinError(ctypes.get_last_error())


type_names = {
    RIM_TYPEMOUSE: "MOUSE",
    RIM_TYPEKEYBOARD: "KEYBOARD",
    RIM_TYPEHID: "HID"
}


print(f"\nFound {result} raw input devices:\n")

for i in range(result):
    device = devices[i]

    print(
        f"Device {i}: "
        f"handle={device.hDevice} | "
        f"type={type_names.get(device.dwType, 'UNKNOWN')}"
    )
