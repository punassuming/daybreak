import configparser
import logging
from pathlib import Path
from .base import Terminal

logger = logging.getLogger("daybreak")

class Konsole(Terminal):
    def set_mode(self, mode: str):
        # 1. Find default profile
        config_path = Path.home() / ".config" / "konsolerc"
        if not config_path.exists():
            return

        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            
            default_profile_name = "Default"
            if "Desktop Entry" in config and "DefaultProfile" in config["Desktop Entry"]:
                default_profile_name = config["Desktop Entry"]["DefaultProfile"]
            
            # Profile file path
            profile_path = Path.home() / ".local" / "share" / "konsole" / default_profile_name
            if not profile_path.suffix == ".profile":
                profile_path = profile_path.with_suffix(".profile")
            
            if not profile_path.exists():
                logger.warning(f"Konsole profile {profile_path} not found.")
                return
            
            # 2. Update ColorScheme in profile
            # We use a raw read/replace to avoid ConfigParser issues with some KDE file quirks or just to be safe with casing.
            # But ConfigParser is safer for structure. KDE config files are usually INI-like.
            
            profile_config = configparser.ConfigParser()
            # Preserve case is important for KDE? Usually keys are case sensitive.
            profile_config.optionxform = str 
            profile_config.read(profile_path)
            
            target_scheme = "Breeze" if mode == "light" else "BreezeDark"
            
            if "Appearance" not in profile_config:
                profile_config["Appearance"] = {}
            
            profile_config["Appearance"]["ColorScheme"] = target_scheme
            
            with open(profile_path, 'w') as f:
                profile_config.write(f)
                
            logger.info(f"Konsole: Updated profile {default_profile_name} to {target_scheme}")
            
        except Exception as e:
            logger.error(f"Konsole: Failed to update profile: {e}")
