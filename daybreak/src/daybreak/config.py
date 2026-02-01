import os
import toml
import logging
from pathlib import Path
from .themes import THEME_LIBRARY

logger = logging.getLogger("daybreak")

DEFAULT_CONFIG = {
    "system": {
        # KDE Color Schemes (found in /usr/share/color-schemes/, without .colors ext)
        "linux_kde_light": "BreathLight",
        "linux_kde_dark": "BreathDark",
        "windows_light_reg": 1, 
        "windows_dark_reg": 0,
    },
    "terminal": {
        "theme": "Nord"
    }
}

class ConfigManager:
    def __init__(self):
        self.config_dir = Path(os.path.expanduser("~/.config/daybreak"))
        self.config_file = self.config_dir / "config.toml"
        self.data = self._load()

    def _load(self):
        if not self.config_file.exists():
            return self._create_default()
        
        try:
            return toml.load(self.config_file)
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using defaults.")
            return DEFAULT_CONFIG

    def _create_default(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Add a comment about available themes
        available_themes = ", ".join(THEME_LIBRARY.keys())
        
        # TOML doesn't support comments via `toml.dump` easily, so we write manually or just dump.
        # For a better user experience, let's dump then prepend a comment?
        try:
            with open(self.config_file, "w") as f:
                toml.dump(DEFAULT_CONFIG, f)
            logger.info(f"Created default config at {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
            
        return DEFAULT_CONFIG

    def get(self, section, key, default=None):
        return self.data.get(section, {}).get(key, default)

    def get_system_theme(self, os_type, mode):
        if os_type == "linux_kde":
            key = "linux_kde_light" if mode == "light" else "linux_kde_dark"
            return self.get("system", key, DEFAULT_CONFIG["system"][key])
        return None

    def get_terminal_theme_name(self):
        return self.get("terminal", "theme", "Nord")

# Singleton instance
config = ConfigManager()
