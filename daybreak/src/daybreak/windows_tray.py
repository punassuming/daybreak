import logging
import platform

from daybreak.cli.runtime import build_orchestrator

logger = logging.getLogger("daybreak")

WM_APP = 0x8000
TRAY_CALLBACK_MESSAGE = WM_APP + 1
ID_TOGGLE = 1001
ID_LIGHT = 1002
ID_DARK = 1003
ID_EXIT = 1004


class TrayController:
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator or build_orchestrator()
        self.current_mode = self.orchestrator.get_current_mode()

    def tooltip_text(self) -> str:
        return f"Daybreak ({self.current_mode.title()})"

    def apply_mode(self, mode: str):
        theme_name = self.orchestrator.apply(mode)
        self.current_mode = mode
        logger.info(f"Switched to {mode} mode using theme '{theme_name}'.")
        return theme_name

    def toggle_mode(self):
        mode, theme_name = self.orchestrator.apply_toggle()
        self.current_mode = mode
        logger.info(f"Switched to {mode} mode using theme '{theme_name}'.")
        return mode, theme_name

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

    WM_COMMAND = 0x0111
    WM_DESTROY = 0x0002
    WM_RBUTTONUP = 0x0205
    WM_LBUTTONDBLCLK = 0x0203
    WM_NULL = 0x0000
    WS_OVERLAPPED = 0x00000000
    CW_USEDEFAULT = 0x80000000
    NIM_ADD = 0x00000000
    NIM_MODIFY = 0x00000001
    NIM_DELETE = 0x00000002
    NIF_MESSAGE = 0x00000001
    NIF_ICON = 0x00000002
    NIF_TIP = 0x00000004
    MF_STRING = 0x00000000
    TPM_RIGHTBUTTON = 0x0002
    IDI_APPLICATION = 32512
    IDC_ARROW = 32512
    WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

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

    shell32 = ctypes.windll.shell32
    shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]

    controller = TrayController()
    window_class_name = "DaybreakTrayWindow"
    h_instance = kernel32.GetModuleHandleW(None)

    def make_int_resource(resource_id: int):
        return ctypes.cast(ctypes.c_void_p(resource_id), wintypes.LPCWSTR)

    icon_handle = user32.LoadIconW(None, make_int_resource(IDI_APPLICATION))
    cursor_handle = user32.LoadCursorW(None, make_int_resource(IDC_ARROW))
    menu_handle = user32.CreatePopupMenu()
    hwnd = None

    def update_tooltip():
        if hwnd is None:
            return
        notify_data = NOTIFYICONDATAW()
        notify_data.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        notify_data.hWnd = hwnd
        notify_data.uID = 1
        notify_data.uFlags = NIF_TIP
        notify_data.szTip = controller.tooltip_text()
        shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(notify_data))

    def show_menu():
        point = POINT()
        user32.GetCursorPos(ctypes.byref(point))
        user32.SetForegroundWindow(hwnd)
        user32.TrackPopupMenu(menu_handle, TPM_RIGHTBUTTON, point.x, point.y, 0, hwnd, None)
        user32.PostMessageW(hwnd, WM_NULL, 0, 0)

    @WNDPROC
    def window_proc(window_handle, message, w_param, l_param):
        if message == TRAY_CALLBACK_MESSAGE:
            if l_param == WM_RBUTTONUP:
                show_menu()
                return 0
            if l_param == WM_LBUTTONDBLCLK:
                controller.toggle_mode()
                update_tooltip()
                return 0

        if message == WM_COMMAND:
            command_id = w_param & 0xFFFF
            should_continue = controller.handle_command(command_id)
            if not should_continue:
                user32.DestroyWindow(window_handle)
                return 0
            update_tooltip()
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
    window_class.hIcon = icon_handle
    window_class.hCursor = cursor_handle

    if not user32.RegisterClassW(ctypes.byref(window_class)):
        raise OSError("Failed to register Daybreak tray window class.")

    user32.AppendMenuW(menu_handle, MF_STRING, ID_TOGGLE, "Toggle")
    user32.AppendMenuW(menu_handle, MF_STRING, ID_LIGHT, "Light")
    user32.AppendMenuW(menu_handle, MF_STRING, ID_DARK, "Dark")
    user32.AppendMenuW(menu_handle, MF_STRING, ID_EXIT, "Exit")

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
    notify_data.hIcon = icon_handle
    notify_data.szTip = controller.tooltip_text()

    if not shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(notify_data)):
        user32.DestroyWindow(hwnd)
        raise OSError("Failed to add Daybreak tray icon.")

    logger.info("Daybreak tray is running.")

    message = MSG()
    while user32.GetMessageW(ctypes.byref(message), None, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(message))
        user32.DispatchMessageW(ctypes.byref(message))
