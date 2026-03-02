import logging
import subprocess

from daybreak.config import config

logger = logging.getLogger("daybreak")


class KDESystemAdapter:
    name = "kde"

    def get_current_mode(self) -> str:
        try:
            result = subprocess.run(
                ["kreadconfig6", "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"],
                capture_output=True,
                text=True,
            )
            scheme = result.stdout.strip().lower()
            if not scheme:
                result = subprocess.run(
                    ["kreadconfig5", "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme"],
                    capture_output=True,
                    text=True,
                )
                scheme = result.stdout.strip().lower()
            return "dark" if "dark" in scheme else "light"
        except Exception as exc:
            logger.error(f"Failed to detect KDE mode: {exc}")
            return "light"

    def set_mode(self, mode: str):
        color_scheme = config.get_system_theme("linux_kde", mode)
        try:
            subprocess.run(
                ["plasma-apply-colorscheme", color_scheme],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Applied KDE color scheme: {color_scheme}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(f"Failed to apply color scheme {color_scheme}")

        plasma_theme = "breath-dark" if mode == "dark" else "breath-light"
        try:
            subprocess.run(
                ["plasma-apply-desktoptheme", plasma_theme],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Applied Plasma desktop theme: {plasma_theme}")
        except FileNotFoundError:
            try:
                subprocess.run(
                    ["kwriteconfig6", "--file", "plasmarc", "--group", "Theme", "--key", "name", plasma_theme],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info(f"Set plasmarc theme to {plasma_theme}")
            except Exception as exc:
                logger.error(f"Failed to update plasmarc: {exc}")
        except subprocess.CalledProcessError:
            logger.error(f"Failed to apply desktop theme {plasma_theme}")
