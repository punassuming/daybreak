import logging
import platform

logger = logging.getLogger("daybreak")


class WindowsSystemAdapter:
    name = "windows"

    def get_current_mode(self) -> str:
        if platform.system() != "Windows":
            return "light"
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except Exception as exc:
            logger.error(f"Failed to read Windows registry: {exc}")
            return "light"

    def set_mode(self, mode: str, palette: dict = None):
        if platform.system() != "Windows":
            logger.warning("Not running on Windows, skipping registry changes.")
            return

        try:
            import ctypes
            import winreg

            value = 1 if mode == "light" else 0
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, value)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, value)
            winreg.CloseKey(key)
            logger.info(f"Registry updated for {mode} mode.")
            self._broadcast_theme_change(ctypes)
            logger.info("Broadcasted WM_SETTINGCHANGE.")
        except Exception as exc:
            logger.error(f"Failed to change Windows theme: {exc}")

    def _broadcast_theme_change(self, ctypes_module):
        # Prefer async notify to avoid synchronous message handling issues in apps
        # that perform outgoing COM calls during WM_SETTINGCHANGE processing.
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        user32 = ctypes_module.windll.user32
        immersive_color_set = ctypes_module.c_wchar_p("ImmersiveColorSet")

        notify_ok = user32.SendNotifyMessageW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, immersive_color_set
        )

        if notify_ok:
            return

        user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            immersive_color_set,
            SMTO_ABORTIFHUNG,
            5000,
            0,
        )
