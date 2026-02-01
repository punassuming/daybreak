import logging
import platform
from .base import PlatformHandler

logger = logging.getLogger("daybreak")

class WindowsHandler(PlatformHandler):
    def get_current_mode(self) -> str:
        if platform.system() != "Windows":
            return "light" # Fallback for non-Windows dev environments

        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if value == 1 else "dark"
        except Exception as e:
            logger.error(f"Failed to read Windows registry: {e}")
            return "light"

    def set_mode(self, mode: str):
        if platform.system() != "Windows":
            logger.warning("Not running on Windows, skipping registry changes.")
            return

        try:
            import winreg
            import ctypes
            
            val = 1 if mode == "light" else 0
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            
            # Open key for writing
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "AppsUseLightTheme", 0, winreg.REG_DWORD, val)
            winreg.SetValueEx(key, "SystemUsesLightTheme", 0, winreg.REG_DWORD, val)
            winreg.CloseKey(key)
            
            logger.info(f"Registry updated for {mode} mode.")
            
            # Broadcast change to system
            # WM_SETTINGCHANGE = 0x001A
            # HWND_BROADCAST = 0xFFFF
            ctypes.windll.user32.SendMessageTimeoutW(
                0xFFFF, 0x001A, 0, "ImmersiveColorSet", 0x0002, 5000, 0
            )
            logger.info("Broadcasted WM_SETTINGCHANGE.")
            
        except Exception as e:
            logger.error(f"Failed to change Windows theme: {e}")