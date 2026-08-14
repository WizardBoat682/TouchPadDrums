import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)

RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIM_TYPEHID = 2

RIDI_DEVICENAME = 0x20000007
RIDI_DEVICEINFO = 0x2000000B


class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [
        ("hDevice", wintypes.HANDLE),
        ("dwType", wintypes.DWORD)
    ]


class RID_DEVICE_INFO_MOUSE(ctypes.Structure):
    _fields_ = [
        ("dwId", wintypes.DWORD),
        ("dwNumberOfButtons", wintypes.DWORD),
        ("dwSampleRate", wintypes.DWORD),
        ("fHasHorizontalWheel", wintypes.BOOL),
    ]


class RID_DEVICE_INFO_KEYBOARD(ctypes.Structure):
    _fields_ = [
        ("dwType", wintypes.DWORD),
        ("dwSubType", wintypes.DWORD),
        ("dwKeyboardMode", wintypes.DWORD),
        ("dwNumberOfFunctionKeys", wintypes.DWORD),
        ("dwNumberOfIndicators", wintypes.DWORD),
        ("dwNumberOfKeysTotal", wintypes.DWORD),
    ]


class RID_DEVICE_INFO_HID(ctypes.Structure):
    _fields_ = [
        ("dwVendorId", wintypes.DWORD),
        ("dwProductId", wintypes.DWORD),
        ("dwVersionNumber", wintypes.DWORD),
        ("usUsagePage", wintypes.WORD),
        ("usUsage", wintypes.WORD),
    ]


class RID_DEVICE_INFO_UNION(ctypes.Union):
    _fields_ = [
        ("mouse", RID_DEVICE_INFO_MOUSE),
        ("keyboard", RID_DEVICE_INFO_KEYBOARD),
        ("hid", RID_DEVICE_INFO_HID),
    ]


class RID_DEVICE_INFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("dwType", wintypes.DWORD),
        ("DUMMYUNIONNAME", RID_DEVICE_INFO_UNION),
    ]


# API definitions
GetRawInputDeviceList = user32.GetRawInputDeviceList
GetRawInputDeviceList.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(wintypes.UINT),
    wintypes.UINT
]
GetRawInputDeviceList.restype = wintypes.UINT


GetRawInputDeviceInfoW = user32.GetRawInputDeviceInfoW
GetRawInputDeviceInfoW.argtypes = [
    wintypes.HANDLE,
    wintypes.UINT,
    ctypes.c_void_p,
    ctypes.POINTER(wintypes.UINT)
]
GetRawInputDeviceInfoW.restype = wintypes.UINT


# Get device count
count = wintypes.UINT(0)

result = GetRawInputDeviceList(
    None,
    ctypes.byref(count),
    ctypes.sizeof(RAWINPUTDEVICELIST)
)

if result == 0xFFFFFFFF:
    raise ctypes.WinError(ctypes.get_last_error())


devices = (RAWINPUTDEVICELIST * count.value)()

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
    RIM_TYPEHID: "HID",
}


print("\nRAW INPUT DEVICE DETAILS:\n")

for i in range(result):
    device = devices[i]

    # Get name
    name_length = wintypes.UINT(0)

    GetRawInputDeviceInfoW(
        device.hDevice,
        RIDI_DEVICENAME,
        None,
        ctypes.byref(name_length)
    )

    name_buffer = ctypes.create_unicode_buffer(name_length.value)

    GetRawInputDeviceInfoW(
        device.hDevice,
        RIDI_DEVICENAME,
        name_buffer,
        ctypes.byref(name_length)
    )

    # Get device info
    info = RID_DEVICE_INFO()
    info.cbSize = ctypes.sizeof(RID_DEVICE_INFO)

    info_size = wintypes.UINT(ctypes.sizeof(RID_DEVICE_INFO))

    info_result = GetRawInputDeviceInfoW(
        device.hDevice,
        RIDI_DEVICEINFO,
        ctypes.byref(info),
        ctypes.byref(info_size)
    )

    print(f"DEVICE {i}")
    print("Type:", type_names.get(device.dwType, f"UNKNOWN ({device.dwType})"))
    print("Name:", name_buffer.value)

    if info_result != 0xFFFFFFFF:
        print("Info type:", type_names.get(info.dwType, f"UNKNOWN ({info.dwType})"))

        if info.dwType == RIM_TYPEHID:
            print("Vendor ID:", info.DUMMYUNIONNAME.hid.dwVendorId)
            print("Product ID:", info.DUMMYUNIONNAME.hid.dwProductId)
            print("Usage Page:", hex(info.DUMMYUNIONNAME.hid.usUsagePage))
            print("Usage:", hex(info.DUMMYUNIONNAME.hid.usUsage))

    print()
