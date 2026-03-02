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

    def set_mode(self, mode: str):
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

            ctypes.windll.user32.SendMessageTimeoutW(
                0xFFFF, 0x001A, 0, "ImmersiveColorSet", 0x0002, 5000, 0
            )
            logger.info("Broadcasted WM_SETTINGCHANGE.")
        except Exception as exc:
            logger.error(f"Failed to change Windows theme: {exc}")
