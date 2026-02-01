import logging
import subprocess
from .base import PlatformHandler
from daybreak.terminals.kitty import Kitty
from daybreak.terminals.config_terminals import Ghostty, WezTerm
from daybreak.terminals.konsole import Konsole
from daybreak.terminals.universal import UniversalPty
from daybreak.terminals.neovim import Neovim
from daybreak.browsers import Firefox, Chrome
from daybreak.config import config

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
        # 1. Change KDE System Colors (App Body)
        # ---------------------------------------
        color_scheme = config.get_system_theme("linux_kde", mode)
        
        try:
            # Apply Color Scheme (Application Colors)
            subprocess.run(["plasma-apply-colorscheme", color_scheme], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"Applied KDE color scheme: {color_scheme}")
        except (subprocess.CalledProcessError, FileNotFoundError):
             logger.error(f"Failed to apply color scheme {color_scheme}")

        # 2. Change Plasma Style (Panels, Widgets)
        # ---------------------------------------
        # Mapping: BreathLight -> breath-light, BreathDark -> breath-dark
        # Ideally this should be in config, but we derive it for now or check config
        plasma_theme = "breath-dark" if mode == "dark" else "breath-light"
        
        try:
             # Try using the CLI tool if available (Plasma 6 specific mostly)
             # plasma-apply-desktoptheme <theme>
             subprocess.run(["plasma-apply-desktoptheme", plasma_theme], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             logger.info(f"Applied Plasma desktop theme: {plasma_theme}")
        except FileNotFoundError:
            # Fallback: Write config and reload plasmashell (Older method)
            try:
                subprocess.run(["kwriteconfig6", "--file", "plasmarc", "--group", "Theme", "--key", "name", plasma_theme], check=True)
                # We need to restart/reload plasmashell to pick this up effectively in some versions
                # or rely on KGlobalSettings.
                logger.info(f"Set plasmarc theme to {plasma_theme} (Manual write)")
            except Exception as e:
                logger.error(f"Failed to update plasmarc: {e}")
        except subprocess.CalledProcessError:
             logger.error(f"Failed to apply desktop theme {plasma_theme}")

        # 3. Window Decorations (Titlebars)
        # ---------------------------------------
        # Usually 'Breeze' follows the color scheme. 
        # If using a specific theme that has separate light/dark titlebars, we'd swap it here.
        # For Breath/Breeze, changing the color scheme is usually sufficient for the titlebar *colors*.
        
        # 4. Update Terminals
        for term in self.terminals:
            try:
                term.set_mode(mode)
            except Exception as e:
                logger.warning(f"Failed to update terminal {term.__class__.__name__}: {e}")

        # 3. Update Browsers (Logging only, they follow system)
        for browser in self.browsers:
            browser.set_mode(mode)