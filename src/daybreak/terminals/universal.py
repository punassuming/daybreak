import os
import glob
import logging
from .base import Terminal
from daybreak.config import config
from daybreak.themes import get_theme_palette

logger = logging.getLogger("daybreak")

class UniversalPty(Terminal):
    """
    Broadcasts full 16-color palette OSC escape sequences to all open PTYs.
    Fetches theme from config and generates light/dark variants if needed.
    """
    def set_mode(self, mode: str):
        theme_name = config.get_terminal_theme_name(mode)
        self.apply_theme(theme_name, mode)

    def apply_theme(self, theme_name: str, mode: str):
        palette_set = get_theme_palette(theme_name)
        
        theme = palette_set.get(mode)
        if not theme:
            logger.warning(f"Theme '{theme_name}' does not support {mode} mode.")
            return
            
        # Only log if not in interactive/silent mode? 
        # For now, logging is fine, it goes to stderr usually or we can suppress it in interactive.
        
        sequences = []
        
        # 1. Special Colors (OSC 10, 11, 12)
        sequences.append(f"\033]10;{theme['special']['foreground']}\007")
        sequences.append(f"\033]11;{theme['special']['background']}\007")
        sequences.append(f"\033]12;{theme['special']['cursor']}\007")

        # 2. ANSI Colors 0-15 (OSC 4)
        for i, color in theme['colors'].items():
            sequences.append(f"\033]4;{i};{color}\007")

        full_payload = "".join(sequences)
        
        self._broadcast(full_payload)
        self._write_shell_script(full_payload)

    def _broadcast(self, payload):
        ptys = glob.glob("/dev/pts/[0-9]*")
        count = 0
        for pty_path in ptys:
            try:
                fd = os.open(pty_path, os.O_WRONLY | os.O_NOCTTY)
                with os.fdopen(fd, 'w') as f:
                    f.write(payload)
                count += 1
            except (PermissionError, OSError):
                pass 
        
        if count > 0:
            logger.info(f"Broadcasted palette to {count} terminals.")

    def _write_shell_script(self, payload):
        config_dir = os.path.expanduser("~/.config/daybreak")
        os.makedirs(config_dir, exist_ok=True)
        
        # 1. POSIX (Bash/Zsh)
        # Using raw bytes is fine for printf
        try:
            with open(os.path.join(config_dir, "theme.sh"), "w") as f:
                f.write("#!/bin/sh\n")
                f.write(f"printf '{payload}'\n")
        except Exception as e:
            logger.warning(f"Failed to write theme.sh: {e}")

        # 2. Fish
        try:
            with open(os.path.join(config_dir, "theme.fish"), "w") as f:
                f.write(f"printf '{payload}'\n")
        except Exception as e:
            logger.warning(f"Failed to write theme.fish: {e}")

        # 3. PowerShell
        # Needs careful escaping. \033 might need to be explicit
        try:
            # Replace raw ESC char (which is in payload) with PowerShell expression
            # Python's payload string contains actual \x1b bytes.
            # We want to write: Write-Host "$([char]0x1b)]10;..." -NoNewline
            
            # Escape single quotes if any (though unlikely in our payload)
            ps_payload = payload.replace("'", "''")
            
            # We construct a string where we interpolate the escape char
            # But payload already has the escape char embedded.
            # Let's escape the escape char for PS logic? 
            # Actually, modern PS Core handles raw ESC bytes in strings if file is UTF8.
            # But safest legacy-compat way:
            ps_payload_safe = payload.replace("\033", "$([char]0x1b)")
            
            with open(os.path.join(config_dir, "theme.ps1"), "w") as f:
                f.write(f"Write-Host \"{ps_payload_safe}\" -NoNewline\n")
        except Exception as e:
            logger.warning(f"Failed to write theme.ps1: {e}")
