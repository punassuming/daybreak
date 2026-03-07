import logging
import os
import platform

from daybreak.cli.runtime import build_orchestrator
from daybreak.config import config

logger = logging.getLogger("daybreak")

WM_APP = 0x8000
TRAY_CALLBACK_MESSAGE = WM_APP + 1
ID_TOGGLE = 1001
ID_LIGHT = 1002
ID_DARK = 1003
ID_EXIT = 1004
ID_OPEN_CONFIG = 1005
ID_RUN_SETUP = 1006


def _configure_win32_api(user32, shell32, wintypes_module, wndclass_type, point_type, msg_type, notifyicon_type):
    import ctypes

    lresult_type = getattr(wintypes_module, "LRESULT", None)
    if lresult_type is None:
        lresult_type = ctypes.c_ssize_t

    uint_ptr_type = getattr(wintypes_module, "UINT_PTR", None)
    if uint_ptr_type is None:
        uint_ptr_type = ctypes.c_size_t

    atom_type = getattr(wintypes_module, "ATOM", wintypes_module.WORD)
    lpvoid_type = getattr(wintypes_module, "LPVOID", ctypes.c_void_p)
    hicon_type = getattr(wintypes_module, "HICON", wintypes_module.HANDLE)

    user32.RegisterClassW.argtypes = [wndclass_type]
    user32.RegisterClassW.restype = atom_type
    user32.CreateWindowExW.argtypes = [
        wintypes_module.DWORD,
        wintypes_module.LPCWSTR,
        wintypes_module.LPCWSTR,
        wintypes_module.DWORD,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes_module.HWND,
        wintypes_module.HMENU,
        wintypes_module.HINSTANCE,
        lpvoid_type,
    ]
    user32.CreateWindowExW.restype = wintypes_module.HWND
    user32.DefWindowProcW.argtypes = [
        wintypes_module.HWND,
        wintypes_module.UINT,
        wintypes_module.WPARAM,
        wintypes_module.LPARAM,
    ]
    user32.DefWindowProcW.restype = lresult_type
    user32.DestroyWindow.argtypes = [wintypes_module.HWND]
    user32.DestroyWindow.restype = wintypes_module.BOOL
    user32.LoadIconW.argtypes = [wintypes_module.HINSTANCE, wintypes_module.LPCWSTR]
    user32.LoadIconW.restype = hicon_type
    user32.LoadCursorW.argtypes = [wintypes_module.HINSTANCE, wintypes_module.LPCWSTR]
    user32.LoadCursorW.restype = wintypes_module.HCURSOR
    user32.CreatePopupMenu.restype = wintypes_module.HMENU
    user32.DestroyMenu.argtypes = [wintypes_module.HMENU]
    user32.DestroyMenu.restype = wintypes_module.BOOL
    user32.AppendMenuW.argtypes = [
        wintypes_module.HMENU,
        wintypes_module.UINT,
        uint_ptr_type,
        wintypes_module.LPCWSTR,
    ]
    user32.AppendMenuW.restype = wintypes_module.BOOL
    user32.GetCursorPos.argtypes = [point_type]
    user32.GetCursorPos.restype = wintypes_module.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes_module.HWND]
    user32.SetForegroundWindow.restype = wintypes_module.BOOL
    user32.TrackPopupMenu.argtypes = [
        wintypes_module.HMENU,
        wintypes_module.UINT,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes_module.HWND,
        lpvoid_type,
    ]
    user32.TrackPopupMenu.restype = uint_ptr_type
    user32.PostMessageW.argtypes = [
        wintypes_module.HWND,
        wintypes_module.UINT,
        wintypes_module.WPARAM,
        wintypes_module.LPARAM,
    ]
    user32.PostMessageW.restype = wintypes_module.BOOL
    user32.GetMessageW.argtypes = [msg_type, wintypes_module.HWND, wintypes_module.UINT, wintypes_module.UINT]
    user32.GetMessageW.restype = ctypes.c_int
    user32.TranslateMessage.argtypes = [msg_type]
    user32.TranslateMessage.restype = wintypes_module.BOOL
    user32.DispatchMessageW.argtypes = [msg_type]
    user32.DispatchMessageW.restype = lresult_type
    user32.PostQuitMessage.argtypes = [ctypes.c_int]
    user32.CreateIconIndirect.argtypes = [lpvoid_type]
    user32.CreateIconIndirect.restype = hicon_type
    user32.DestroyIcon.argtypes = [hicon_type]
    user32.DestroyIcon.restype = wintypes_module.BOOL
    shell32.Shell_NotifyIconW.argtypes = [wintypes_module.DWORD, notifyicon_type]
    shell32.Shell_NotifyIconW.restype = wintypes_module.BOOL


def _render_mode_icon_pixels(mode: str, size: int = 32) -> bytes:
    pixels = bytearray(size * size * 4)
    center = (size - 1) / 2.0
    sun_radius = size * 0.22
    ray_inner = size * 0.29
    ray_outer = size * 0.44
    moon_radius = size * 0.28
    moon_cutout = size * 0.24

    def set_pixel(x, y, red, green, blue, alpha=255):
        if not (0 <= x < size and 0 <= y < size):
            return
        offset = (y * size + x) * 4
        pixels[offset : offset + 4] = bytes((blue, green, red, alpha))

    def distance(x, y, cx, cy):
        return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5

    if mode == "light":
        for y in range(size):
            for x in range(size):
                px = x + 0.5
                py = y + 0.5
                d = distance(px, py, center, center)
                if d <= sun_radius:
                    set_pixel(x, y, 255, 198, 72)
                    continue

                dx = abs(px - center)
                dy = abs(py - center)
                on_vertical_ray = dx <= size * 0.06 and ray_inner <= d <= ray_outer
                on_horizontal_ray = dy <= size * 0.06 and ray_inner <= d <= ray_outer
                on_diag_a = abs((px - center) - (py - center)) <= size * 0.08 and ray_inner <= d <= ray_outer
                on_diag_b = abs((px - center) + (py - center)) <= size * 0.08 and ray_inner <= d <= ray_outer

                if on_vertical_ray or on_horizontal_ray or on_diag_a or on_diag_b:
                    set_pixel(x, y, 255, 224, 128, 235)
    else:
        moon_center_x = center + size * 0.02
        moon_center_y = center - size * 0.02
        cutout_center_x = center + size * 0.16
        cutout_center_y = center - size * 0.08

        for y in range(size):
            for x in range(size):
                px = x + 0.5
                py = y + 0.5
                outer = distance(px, py, moon_center_x, moon_center_y) <= moon_radius
                inner = distance(px, py, cutout_center_x, cutout_center_y) <= moon_cutout
                if outer and not inner:
                    set_pixel(x, y, 192, 222, 255)

        for star_x, star_y in ((9, 9), (22, 8), (24, 21)):
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                set_pixel(star_x + dx, star_y + dy, 255, 244, 202, 220)

    return bytes(pixels)


def _signed_word(value: int) -> int:
    word = value & 0xFFFF
    return word - 0x10000 if word & 0x8000 else word


def _menu_position_from_wparam(w_param: int):
    if not w_param:
        return None
    x_pos = _signed_word(int(w_param))
    y_pos = _signed_word(int(w_param) >> 16)
    if x_pos == -1 and y_pos == -1:
        return None
    return x_pos, y_pos


class TrayController:
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator or build_orchestrator()
        self.current_mode = self.orchestrator.get_current_mode()
        self.current_theme = config.get_mode_theme_name(self.current_mode)

    def tooltip_text(self) -> str:
        return f"Daybreak ({self.current_mode.title()}: {self.current_theme})"

    def status_text(self) -> str:
        return f"{self.current_mode.title()} mode - {self.current_theme}"

    def apply_mode(self, mode: str):
        theme_name = self.orchestrator.apply(mode)
        self.current_mode = mode
        self.current_theme = theme_name
        logger.info(f"Switched to {mode} mode using theme '{theme_name}'.")
        return theme_name

    def toggle_mode(self):
        mode, theme_name = self.orchestrator.apply_toggle()
        self.current_mode = mode
        self.current_theme = theme_name
        logger.info(f"Switched to {mode} mode using theme '{theme_name}'.")
        return mode, theme_name

    def open_config(self):
        config.save()
        os.startfile(str(config.config_file))

    def run_setup(self):
        from daybreak.shell_setup import install_shell_hook

        install_shell_hook()

    def handle_command(self, command_id: int) -> bool:
        if command_id == ID_TOGGLE:
            self.toggle_mode()
            return True
        if command_id == ID_LIGHT:
            self.apply_mode("light")
            return True
        if command_id == ID_DARK:
            self.apply_mode("dark")
            return True
        if command_id == ID_OPEN_CONFIG:
            self.open_config()
            return True
        if command_id == ID_RUN_SETUP:
            self.run_setup()
            return True
        if command_id == ID_EXIT:
            return False
        return True


def run_windows_tray():
    if platform.system() != "Windows":
        raise RuntimeError("Tray mode is only available on Windows.")

    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    hbitmap_type = getattr(wintypes, "HBITMAP", wintypes.HANDLE)

    WM_DESTROY = 0x0002
    WM_CONTEXTMENU = 0x007B
    WM_RBUTTONDOWN = 0x0204
    WM_RBUTTONUP = 0x0205
    WM_LBUTTONUP = 0x0202
    WM_LBUTTONDBLCLK = 0x0203
    WM_NULL = 0x0000
    WS_OVERLAPPED = 0x00000000
    CW_USEDEFAULT = 0x80000000
    NIM_ADD = 0x00000000
    NIM_MODIFY = 0x00000001
    NIM_DELETE = 0x00000002
    NIM_SETVERSION = 0x00000004
    NIF_MESSAGE = 0x00000001
    NIF_ICON = 0x00000002
    NIF_TIP = 0x00000004
    NOTIFYICON_VERSION_4 = 4
    MF_STRING = 0x00000000
    MF_GRAYED = 0x00000001
    MF_DISABLED = 0x00000002
    MF_SEPARATOR = 0x00000800
    MF_CHECKED = 0x00000008
    TPM_RIGHTBUTTON = 0x0002
    TPM_NONOTIFY = 0x0080
    TPM_RETURNCMD = 0x0100
    BI_BITFIELDS = 3
    DIB_RGB_COLORS = 0
    NIN_SELECT = 0x0400
    NIN_KEYSELECT = 0x0401
    IDI_APPLICATION = 32512
    IDC_ARROW = 32512
    lresult_type = getattr(wintypes, "LRESULT", ctypes.c_ssize_t)
    WNDPROC = ctypes.WINFUNCTYPE(lresult_type, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HCURSOR),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]

    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class MSG(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("message", wintypes.UINT),
            ("wParam", wintypes.WPARAM),
            ("lParam", wintypes.LPARAM),
            ("time", wintypes.DWORD),
            ("pt", POINT),
        ]

    class NOTIFYICONDATAW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("hWnd", wintypes.HWND),
            ("uID", wintypes.UINT),
            ("uFlags", wintypes.UINT),
            ("uCallbackMessage", wintypes.UINT),
            ("hIcon", wintypes.HICON),
            ("szTip", wintypes.WCHAR * 128),
            ("dwState", wintypes.DWORD),
            ("dwStateMask", wintypes.DWORD),
            ("szInfo", wintypes.WCHAR * 256),
            ("uTimeoutOrVersion", wintypes.UINT),
            ("szInfoTitle", wintypes.WCHAR * 64),
            ("dwInfoFlags", wintypes.DWORD),
            ("guidItem", ctypes.c_byte * 16),
            ("hBalloonIcon", wintypes.HICON),
        ]

    class BITMAPV5HEADER(ctypes.Structure):
        _fields_ = [
            ("bV5Size", wintypes.DWORD),
            ("bV5Width", ctypes.c_long),
            ("bV5Height", ctypes.c_long),
            ("bV5Planes", wintypes.WORD),
            ("bV5BitCount", wintypes.WORD),
            ("bV5Compression", wintypes.DWORD),
            ("bV5SizeImage", wintypes.DWORD),
            ("bV5XPelsPerMeter", ctypes.c_long),
            ("bV5YPelsPerMeter", ctypes.c_long),
            ("bV5ClrUsed", wintypes.DWORD),
            ("bV5ClrImportant", wintypes.DWORD),
            ("bV5RedMask", wintypes.DWORD),
            ("bV5GreenMask", wintypes.DWORD),
            ("bV5BlueMask", wintypes.DWORD),
            ("bV5AlphaMask", wintypes.DWORD),
            ("bV5CSType", wintypes.DWORD),
            ("bV5Endpoints", ctypes.c_byte * 36),
            ("bV5GammaRed", wintypes.DWORD),
            ("bV5GammaGreen", wintypes.DWORD),
            ("bV5GammaBlue", wintypes.DWORD),
            ("bV5Intent", wintypes.DWORD),
            ("bV5ProfileData", wintypes.DWORD),
            ("bV5ProfileSize", wintypes.DWORD),
            ("bV5Reserved", wintypes.DWORD),
        ]

    class ICONINFO(ctypes.Structure):
        _fields_ = [
            ("fIcon", wintypes.BOOL),
            ("xHotspot", wintypes.DWORD),
            ("yHotspot", wintypes.DWORD),
            ("hbmMask", hbitmap_type),
            ("hbmColor", hbitmap_type),
        ]

    shell32 = ctypes.windll.shell32
    gdi32 = ctypes.windll.gdi32
    _configure_win32_api(
        user32,
        shell32,
        wintypes,
        ctypes.POINTER(WNDCLASSW),
        ctypes.POINTER(POINT),
        ctypes.POINTER(MSG),
        ctypes.POINTER(NOTIFYICONDATAW),
    )
    hgdiobj_type = getattr(wintypes, "HGDIOBJ", wintypes.HANDLE)
    gdi32.CreateDIBSection.restype = hbitmap_type
    gdi32.CreateBitmap.restype = hbitmap_type
    gdi32.DeleteObject.argtypes = [hgdiobj_type]
    gdi32.DeleteObject.restype = wintypes.BOOL
    user32.CreateIconIndirect.argtypes = [ctypes.POINTER(ICONINFO)]

    controller = TrayController()
    window_class_name = "DaybreakTrayWindow"
    h_instance = kernel32.GetModuleHandleW(None)

    def make_int_resource(resource_id: int):
        return ctypes.cast(ctypes.c_void_p(resource_id), wintypes.LPCWSTR)

    def create_tray_icon(mode: str):
        pixels = _render_mode_icon_pixels(mode)
        header = BITMAPV5HEADER()
        header.bV5Size = ctypes.sizeof(BITMAPV5HEADER)
        header.bV5Width = 32
        header.bV5Height = -32
        header.bV5Planes = 1
        header.bV5BitCount = 32
        header.bV5Compression = BI_BITFIELDS
        header.bV5SizeImage = len(pixels)
        header.bV5RedMask = 0x00FF0000
        header.bV5GreenMask = 0x0000FF00
        header.bV5BlueMask = 0x000000FF
        header.bV5AlphaMask = 0xFF000000

        bits = ctypes.c_void_p()
        color_bitmap = gdi32.CreateDIBSection(None, ctypes.byref(header), DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
        if not color_bitmap or not bits.value:
            return None

        mask_bitmap = gdi32.CreateBitmap(32, 32, 1, 1, None)
        if not mask_bitmap:
            gdi32.DeleteObject(color_bitmap)
            return None

        ctypes.memmove(bits.value, pixels, len(pixels))

        icon_info = ICONINFO()
        icon_info.fIcon = True
        icon_info.hbmMask = mask_bitmap
        icon_info.hbmColor = color_bitmap
        icon = user32.CreateIconIndirect(ctypes.byref(icon_info))

        gdi32.DeleteObject(mask_bitmap)
        gdi32.DeleteObject(color_bitmap)

        return icon

    icon_handles = {
        "light": create_tray_icon("light"),
        "dark": create_tray_icon("dark"),
    }
    if not icon_handles["light"] or not icon_handles["dark"]:
        fallback_icon = user32.LoadIconW(None, make_int_resource(IDI_APPLICATION))
        icon_handles["light"] = icon_handles["light"] or fallback_icon
        icon_handles["dark"] = icon_handles["dark"] or fallback_icon

    cursor_handle = user32.LoadCursorW(None, make_int_resource(IDC_ARROW))
    hwnd = None

    def current_icon_handle():
        return icon_handles.get(controller.current_mode) or icon_handles["light"]

    def update_tray_icon():
        if hwnd is None:
            return
        notify_data = NOTIFYICONDATAW()
        notify_data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        notify_data.hWnd = hwnd
        notify_data.uID = 1
        notify_data.uFlags = NIF_TIP | NIF_ICON
        notify_data.hIcon = current_icon_handle()
        notify_data.szTip = controller.tooltip_text()
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(notify_data))

    def build_menu():
        menu_handle = user32.CreatePopupMenu()
        if not menu_handle:
            raise OSError("Failed to create Daybreak tray menu.")

        current_flags = MF_STRING | MF_DISABLED | MF_GRAYED
        light_flags = MF_STRING | (MF_CHECKED if controller.current_mode == "light" else 0)
        dark_flags = MF_STRING | (MF_CHECKED if controller.current_mode == "dark" else 0)

        user32.AppendMenuW(menu_handle, current_flags, 0, controller.status_text())
        user32.AppendMenuW(menu_handle, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu_handle, MF_STRING, ID_TOGGLE, "Toggle")
        user32.AppendMenuW(menu_handle, light_flags, ID_LIGHT, "Switch to Light")
        user32.AppendMenuW(menu_handle, dark_flags, ID_DARK, "Switch to Dark")
        user32.AppendMenuW(menu_handle, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu_handle, MF_STRING, ID_OPEN_CONFIG, "Open Config")
        user32.AppendMenuW(menu_handle, MF_STRING, ID_RUN_SETUP, "Run Setup")
        user32.AppendMenuW(menu_handle, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu_handle, MF_STRING, ID_EXIT, "Exit")
        return menu_handle

    def show_menu(anchor=None):
        point = POINT()
        if anchor is None:
            user32.GetCursorPos(ctypes.byref(point))
        else:
            point.x, point.y = anchor
        user32.SetForegroundWindow(hwnd)
        menu_handle = build_menu()
        command_id = user32.TrackPopupMenu(
            menu_handle,
            TPM_RIGHTBUTTON | TPM_NONOTIFY | TPM_RETURNCMD,
            point.x,
            point.y,
            0,
            hwnd,
            None,
        )
        user32.PostMessageW(hwnd, WM_NULL, 0, 0)
        user32.DestroyMenu(menu_handle)
        if command_id:
            should_continue = controller.handle_command(command_id)
            if not should_continue:
                user32.DestroyWindow(hwnd)
                return
            update_tray_icon()

    @WNDPROC
    def window_proc(window_handle, message, w_param, l_param):
        if message == TRAY_CALLBACK_MESSAGE:
            notification_code = int(l_param) & 0xFFFF
            anchor = _menu_position_from_wparam(w_param)

            if notification_code in (WM_CONTEXTMENU, WM_RBUTTONDOWN, WM_RBUTTONUP):
                show_menu(anchor)
                return 0
            if notification_code in (WM_LBUTTONUP, NIN_SELECT, NIN_KEYSELECT):
                show_menu(anchor)
                return 0
            if notification_code == WM_LBUTTONDBLCLK:
                controller.toggle_mode()
                update_tray_icon()
            return 0

        if message == WM_DESTROY:
            notify_data = NOTIFYICONDATAW()
            notify_data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            notify_data.hWnd = window_handle
            notify_data.uID = 1
            shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(notify_data))
            user32.PostQuitMessage(0)
            return 0

        return user32.DefWindowProcW(window_handle, message, w_param, l_param)

    window_class = WNDCLASSW()
    window_class.lpfnWndProc = window_proc
    window_class.hInstance = h_instance
    window_class.lpszClassName = window_class_name
    window_class.hIcon = current_icon_handle()
    window_class.hCursor = cursor_handle

    if not user32.RegisterClassW(ctypes.byref(window_class)):
        raise OSError("Failed to register Daybreak tray window class.")

    hwnd = user32.CreateWindowExW(
        0,
        window_class_name,
        "Daybreak",
        WS_OVERLAPPED,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        None,
        None,
        h_instance,
        None,
    )

    if not hwnd:
        raise OSError("Failed to create Daybreak tray window.")

    notify_data = NOTIFYICONDATAW()
    notify_data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
    notify_data.hWnd = hwnd
    notify_data.uID = 1
    notify_data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
    notify_data.uCallbackMessage = TRAY_CALLBACK_MESSAGE
    notify_data.hIcon = current_icon_handle()
    notify_data.szTip = controller.tooltip_text()

    if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(notify_data)):
        user32.DestroyWindow(hwnd)
        raise OSError("Failed to add Daybreak tray icon.")

    notify_data.uTimeoutOrVersion = NOTIFYICON_VERSION_4
    shell32.Shell_NotifyIconW(NIM_SETVERSION, ctypes.byref(notify_data))

    logger.info("Daybreak tray is running.")

    message = MSG()
    while True:
        result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
        if result == -1:
            user32.DestroyWindow(hwnd)
            raise OSError("Daybreak tray message loop failed.")
        if result == 0:
            break
        user32.TranslateMessage(ctypes.byref(message))
        user32.DispatchMessageW(ctypes.byref(message))

    for icon in set(icon_handles.values()):
        if icon:
            user32.DestroyIcon(icon)
