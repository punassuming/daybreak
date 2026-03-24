import os
import shutil
from pathlib import Path
from .base import Terminal
import logging

logger = logging.getLogger("daybreak")

class BaseConfigTerminal(Terminal):
    """
    Helper for terminals that use a config file with an include directive.
    Strategy: Overwrite the 'current_theme' file with the content of 'dark_theme' or 'light_theme'.
    """
    def __init__(self, name, config_dir, theme_file_name="theme.conf", dark_src="dark.conf", light_src="light.conf"):
        self.name = name
        self.config_dir = Path(os.path.expanduser(config_dir))
        self.theme_file = self.config_dir / theme_file_name
        self.dark_src = self.config_dir / "themes" / dark_src
        self.light_src = self.config_dir / "themes" / light_src

    def set_mode(self, mode: str):
        if not self.config_dir.exists():
            # logger.debug(f"{self.name} config dir not found at {self.config_dir}")
            return

        src = self.dark_src if mode == "dark" else self.light_src
        
        if not src.exists():
            logger.warning(f"{self.name}: Theme source file {src} does not exist. Skipping.")
            return

        try:
            # Ensure parent exists (it should if config_dir exists)
            self.theme_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy content instead of symlink to avoid issues with some editors/file watchers
            shutil.copy(src, self.theme_file)
            logger.info(f"{self.name}: Updated {self.theme_file} to {mode} mode.")
            self.reload_config()
        except Exception as e:
            logger.error(f"{self.name}: Failed to update config: {e}")

    def reload_config(self):
        """Override in subclass if a specific reload command is needed"""
        pass

class Ghostty(BaseConfigTerminal):
    def __init__(self):
        # Ghostty: ~/.config/ghostty/config
        # We assume user has `config-file = theme` in their main config
        # and we swap `~/.config/ghostty/theme`
        super().__init__("Ghostty", "~/.config/ghostty", "theme", "dark", "light")
    
    def reload_config(self):
        # Ghostty reloads automatically on file change usually, but we can try signaling if needed.
        # Currently, Ghostty auto-reloads.
        pass

class WezTerm(BaseConfigTerminal):
    def __init__(self):
        # WezTerm: ~/.config/wezterm/wezterm.lua
        # Setup: Main lua requires a theme module or reads a file.
        # Strategy: Swap a `theme.lua` file.
        super().__init__("WezTerm", "~/.config/wezterm", "theme.lua", "dark.lua", "light.lua")
        
    def reload_config(self):
        # WezTerm auto-reloads
        pass
