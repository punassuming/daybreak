import logging
import subprocess
from pathlib import Path

from daybreak.colors import hex_to_rgb
from daybreak.config import config
from daybreak.core.theme_transform import palette_to_tokens, palette_to_accent_tokens

logger = logging.getLogger("daybreak")

_KDE_COLORSCHEME_NAME = "DaybreakTheme"


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

    def set_mode(self, mode: str, palette: dict = None):
        if palette is not None:
            self._write_kde_colorscheme(mode, palette)

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

    def _write_kde_colorscheme(self, mode: str, palette: dict) -> None:
        """Generate a Daybreak-managed KDE colorscheme file with accent colors.

        The file is written to ~/.local/share/color-schemes/DaybreakTheme.colors
        using the standard KDE INI colorscheme format.  Users can opt in by
        setting linux_kde_light / linux_kde_dark = "DaybreakTheme" in their
        Daybreak config.  This is a best-effort operation; any failure is
        logged and ignored.
        """
        try:
            tokens = palette_to_tokens(palette, mode)
            accent_tokens = palette_to_accent_tokens(palette, mode)
            scheme_dir = Path.home() / ".local" / "share" / "color-schemes"
            scheme_dir.mkdir(parents=True, exist_ok=True)
            scheme_path = scheme_dir / f"{_KDE_COLORSCHEME_NAME}.colors"
            content = _build_kde_colorscheme(tokens, accent_tokens)
            scheme_path.write_text(content, encoding="utf-8")
            logger.info(f"Wrote KDE colorscheme: {scheme_path}")
        except Exception as exc:
            logger.warning(f"Failed to write KDE colorscheme: {exc}")


def _rgb(hex_color: str) -> str:
    """Convert a hex colour string to the KDE INI format ``R,G,B``."""
    r, g, b = hex_to_rgb(hex_color)
    return f"{r},{g},{b}"


def _build_kde_colorscheme(tokens: dict, accent_tokens: dict) -> str:
    """Return the content of a KDE .colors INI file derived from *tokens*."""
    bg = tokens["bg"]
    fg = tokens["fg"]
    muted = tokens["muted"]
    primary = tokens["primary"]        # accent / focus / link
    success = tokens["success"]
    warning = tokens["warning"]
    error = tokens["error"]
    info = tokens["info"]
    surface_1 = tokens["surface_1"]
    surface_2 = tokens["surface_2"]
    accent = accent_tokens["accent_primary"]
    accent_selection = accent_tokens["accent_selection"]

    def _color_group(bg_normal, bg_alt, fg_normal, fg_inactive, active, link, negative, neutral, positive, visited, deco):
        return (
            f"BackgroundAlternate={_rgb(bg_alt)}\n"
            f"BackgroundNormal={_rgb(bg_normal)}\n"
            f"DecorationFocus={_rgb(deco)}\n"
            f"DecorationHover={_rgb(deco)}\n"
            f"ForegroundActive={_rgb(active)}\n"
            f"ForegroundInactive={_rgb(fg_inactive)}\n"
            f"ForegroundLink={_rgb(link)}\n"
            f"ForegroundNegative={_rgb(negative)}\n"
            f"ForegroundNeutral={_rgb(neutral)}\n"
            f"ForegroundNormal={_rgb(fg_normal)}\n"
            f"ForegroundPositive={_rgb(positive)}\n"
            f"ForegroundVisited={_rgb(visited)}\n"
        )

    window_group = _color_group(surface_1, surface_2, fg, muted, accent, info, error, warning, success, primary, accent)
    button_group = _color_group(surface_1, surface_2, fg, muted, accent, info, error, warning, success, primary, accent)
    view_group = _color_group(bg, surface_1, fg, muted, accent, info, error, warning, success, primary, accent)
    selection_group = _color_group(accent, accent_selection, bg, muted, accent, info, error, warning, success, primary, accent)
    tooltip_group = _color_group(surface_1, surface_2, fg, muted, accent, info, error, warning, success, primary, accent)
    header_group = _color_group(surface_2, surface_1, fg, muted, accent, info, error, warning, success, primary, accent)

    lines = [
        "[ColorEffects:Disabled]",
        "Color=56,56,56",
        "ColorAmount=0",
        "ColorEffect=0",
        "ContrastAmount=0.65",
        "ContrastEffect=1",
        "IntensityAmount=0.1",
        "IntensityEffect=2",
        "",
        "[ColorEffects:Inactive]",
        "ChangeSelectionColor=true",
        f"Color={_rgb(muted)}",
        "ColorAmount=0.025",
        "ColorEffect=2",
        "ContrastAmount=0.1",
        "ContrastEffect=2",
        "Enable=false",
        "IntensityAmount=0",
        "IntensityEffect=0",
        "",
        "[Colors:Button]",
        button_group,
        "[Colors:Complementary]",
        view_group,
        "[Colors:Header]",
        header_group,
        "[Colors:Selection]",
        selection_group,
        "[Colors:Tooltip]",
        tooltip_group,
        "[Colors:View]",
        view_group,
        "[Colors:Window]",
        window_group,
        "[General]",
        f"ColorScheme={_KDE_COLORSCHEME_NAME}",
        f"Name=Daybreak Theme",
        "shadeSortColumn=true",
        "",
        "[KDE]",
        "contrast=4",
        "",
        "[WM]",
        f"activeBackground={_rgb(surface_1)}",
        f"activeForeground={_rgb(fg)}",
        f"inactiveBackground={_rgb(bg)}",
        f"inactiveForeground={_rgb(muted)}",
        "",
    ]
    return "\n".join(lines)
