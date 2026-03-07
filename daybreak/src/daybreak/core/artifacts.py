"""
Generate Daybreak-owned shared theme artifacts.

Artifacts are written to the Daybreak config directory (default
~/.config/daybreak/) so that other tools and user dotfiles can consume
them voluntarily.  All writes are best-effort; failures are logged but
never abort the main theme-switching pipeline.

Generated files:
  palette.json    — machine-readable palette + semantic token export
  env.sh          — shell-friendly variable exports for accent / theme state
  ls_colors.sh    — LS_COLORS / dircolors-style output for terminal file listings
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("daybreak")


def generate_artifacts(
    config_dir: Path,
    theme_name: str,
    mode: str,
    tokens: dict,
    accent_tokens: dict,
    palette: dict,
) -> None:
    """Write Daybreak-owned shared theme artifacts to *config_dir*.

    Failures are logged at WARNING level but do not propagate.
    """
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        _write_palette_json(config_dir, theme_name, mode, tokens, accent_tokens, palette)
        _write_env_sh(config_dir, theme_name, mode, tokens, accent_tokens)
        _write_ls_colors(config_dir, mode, tokens)
    except Exception as exc:
        logger.warning(f"Failed to write theme artifacts: {exc}")


def _write_palette_json(config_dir, theme_name, mode, tokens, accent_tokens, palette):
    data = {
        "theme": theme_name,
        "mode": mode,
        "tokens": tokens,
        "accent_tokens": accent_tokens,
        "palette": {
            "special": palette.get("special", {}),
            "colors": {
                k: v
                for k, v in palette.get("colors", {}).items()
                if isinstance(v, str)
            },
        },
    }
    path = config_dir / "palette.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.debug(f"Wrote palette artifact: {path}")


def _write_env_sh(config_dir, theme_name, mode, tokens, accent_tokens):
    lines = [
        "# Daybreak theme environment — auto-generated, do not edit manually",
        f'DAYBREAK_THEME="{theme_name}"',
        f'DAYBREAK_MODE="{mode}"',
        f'DAYBREAK_COLOR_BG="{tokens["bg"]}"',
        f'DAYBREAK_COLOR_FG="{tokens["fg"]}"',
        f'DAYBREAK_COLOR_PRIMARY="{tokens["primary"]}"',
        f'DAYBREAK_COLOR_SUCCESS="{tokens["success"]}"',
        f'DAYBREAK_COLOR_WARNING="{tokens["warning"]}"',
        f'DAYBREAK_COLOR_ERROR="{tokens["error"]}"',
        f'DAYBREAK_COLOR_INFO="{tokens["info"]}"',
        f'DAYBREAK_ACCENT_PRIMARY="{accent_tokens["accent_primary"]}"',
        f'DAYBREAK_ACCENT_SECONDARY="{accent_tokens["accent_secondary"]}"',
        f'DAYBREAK_ACCENT_SUCCESS="{accent_tokens["accent_success"]}"',
        f'DAYBREAK_ACCENT_WARNING="{accent_tokens["accent_warning"]}"',
        f'DAYBREAK_ACCENT_ERROR="{accent_tokens["accent_error"]}"',
        f'DAYBREAK_ACCENT_SELECTION="{accent_tokens["accent_selection"]}"',
        "export DAYBREAK_THEME DAYBREAK_MODE",
        "export DAYBREAK_COLOR_BG DAYBREAK_COLOR_FG DAYBREAK_COLOR_PRIMARY",
        "export DAYBREAK_COLOR_SUCCESS DAYBREAK_COLOR_WARNING DAYBREAK_COLOR_ERROR DAYBREAK_COLOR_INFO",
        "export DAYBREAK_ACCENT_PRIMARY DAYBREAK_ACCENT_SECONDARY DAYBREAK_ACCENT_SUCCESS",
        "export DAYBREAK_ACCENT_WARNING DAYBREAK_ACCENT_ERROR DAYBREAK_ACCENT_SELECTION",
    ]
    path = config_dir / "env.sh"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.debug(f"Wrote env artifact: {path}")


def _write_ls_colors(config_dir, mode, tokens):
    """Generate an LS_COLORS / dircolors-compatible file from theme tokens.

    Uses true-color (24-bit) ANSI escape sequences so the output is as
    faithful to the active theme as possible.  The file is safe to source
    from any POSIX shell.
    """
    from daybreak.colors import hex_to_rgb

    def _fg(hex_color):
        r, g, b = hex_to_rgb(hex_color)
        return f"38;2;{r};{g};{b}"

    entries = {
        # Core file types
        "di": f"1;{_fg(tokens['primary'])}",       # directory: bold + primary
        "ln": _fg(tokens["info"]),                  # symbolic link
        "ex": _fg(tokens["success"]),               # executable file
        "pi": _fg(tokens["warning"]),               # named pipe (FIFO)
        "so": _fg(tokens["info"]),                  # socket
        "bd": _fg(tokens["warning"]),               # block device
        "cd": _fg(tokens["warning"]),               # character device
        "or": _fg(tokens["error"]),                 # orphaned symbolic link
        "mi": _fg(tokens["error"]),                 # missing file target
        # Archives / compressed
        "*.tar": f"1;{_fg(tokens['error'])}",
        "*.tgz": f"1;{_fg(tokens['error'])}",
        "*.gz": f"1;{_fg(tokens['error'])}",
        "*.bz2": f"1;{_fg(tokens['error'])}",
        "*.xz": f"1;{_fg(tokens['error'])}",
        "*.zip": f"1;{_fg(tokens['error'])}",
        "*.7z": f"1;{_fg(tokens['error'])}",
        # Source / scripts
        "*.py": _fg(tokens["primary"]),
        "*.sh": _fg(tokens["success"]),
        "*.bash": _fg(tokens["success"]),
        "*.zsh": _fg(tokens["success"]),
        "*.fish": _fg(tokens["success"]),
        # Configuration / data
        "*.json": _fg(tokens["warning"]),
        "*.toml": _fg(tokens["warning"]),
        "*.yaml": _fg(tokens["warning"]),
        "*.yml": _fg(tokens["warning"]),
        "*.ini": _fg(tokens["warning"]),
        "*.cfg": _fg(tokens["warning"]),
        # Documentation
        "*.md": _fg(tokens["info"]),
        "*.rst": _fg(tokens["info"]),
        "*.txt": _fg(tokens["muted"]),
    }

    ls_colors_value = ":".join(f"{k}={v}" for k, v in entries.items())
    lines = [
        "# Daybreak LS_COLORS — auto-generated, do not edit manually",
        "# Source this file to apply terminal file-type colours:",
        "#   [ -f \"$HOME/.config/daybreak/ls_colors.sh\" ] && . \"$HOME/.config/daybreak/ls_colors.sh\"",
        f'LS_COLORS="{ls_colors_value}"',
        "export LS_COLORS",
    ]
    path = config_dir / "ls_colors.sh"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.debug(f"Wrote LS_COLORS artifact: {path}")
