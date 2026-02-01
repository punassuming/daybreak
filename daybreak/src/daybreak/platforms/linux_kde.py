import logging
import subprocess
from .base import PlatformHandler
from daybreak.terminals.kitty import Kitty
from daybreak.terminals.config_terminals import Ghostty, WezTerm
from daybreak.terminals.konsole import Konsole
from daybreak.terminals.universal import UniversalPty
from daybreak.terminals.neovim import Neovim
from daybreak.browsers import Firefox, Chrome

logger = logging.getLogger("daybreak")

class KDELinuxHandler(PlatformHandler):
    def __init__(self):
        # UniversalPty is added to handle immediate broadcasting to all open shells
        self.terminals = [UniversalPty(), Neovim(), Kitty(), Ghostty(), WezTerm(), Konsole()]
        self.browsers = [Firefox(), Chrome()]

    def get_current_mode(self) -> str:
        # Check KDE color scheme in kdeglobals
        try:
            # Try reading the ColorScheme from kdeglobals [General]
            result = subprocess.run(
                ["kreadconfig6", "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"],
                capture_output=True, text=True
            )
            scheme = result.stdout.strip().lower()
            
            if not scheme:
                # Fallback to older kreadconfig5 if 6 returned nothing useful (unlikely on Plasma 6 but good for compat)
                 result = subprocess.run(
                    ["kreadconfig5", "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"],
                    capture_output=True, text=True
                )
                 scheme = result.stdout.strip().lower()

            if "dark" in scheme:
                return "dark"
            return "light"
        except Exception as e:
            logger.error(f"Failed to detect theme: {e}")
            return "light" # Safe default

    def set_mode(self, mode: str):
        # 1. Change KDE System Theme
        # Switched to Manjaro Breath themes
        kde_theme = "org.manjaro.breath-dark.desktop" if mode == "dark" else "org.manjaro.breath-light.desktop"
        
        # Try Plasma 6 tool first, fallback to 5
        tool = "lookandfeeltool"
        
        try:
            # Capture both stdout and stderr to completely silence xrdb noise
            # We only care if it fails (check=True will raise CalledProcessError)
            subprocess.run(
                [tool, "--apply", kde_theme], 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Set KDE theme to {kde_theme}")
        except subprocess.CalledProcessError:
             logger.error("Failed to set KDE theme.")
        except FileNotFoundError:
             logger.error(f"Could not find {tool}. Is it installed?")

        # 2. Update Terminals
        for term in self.terminals:
            try:
                term.set_mode(mode)
            except Exception as e:
                logger.warning(f"Failed to update terminal {term.__class__.__name__}: {e}")

        # 3. Update Browsers (Logging only, they follow system)
        for browser in self.browsers:
            browser.set_mode(mode)