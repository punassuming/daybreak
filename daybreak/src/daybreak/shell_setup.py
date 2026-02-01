import os
import platform
import logging
from pathlib import Path

logger = logging.getLogger("daybreak")

def get_shell_config(shell_name):
    home = Path.home()
    
    if "bash" in shell_name:
        return {
            "path": home / ".bashrc",
            "hook": '\n# Daybreak Theme Hook\n[ -f "$HOME/.config/daybreak/theme.sh" ] && . "$HOME/.config/daybreak/theme.sh"\n'
        }
    elif "zsh" in shell_name:
        return {
            "path": home / ".zshrc",
            "hook": '\n# Daybreak Theme Hook\n[ -f "$HOME/.config/daybreak/theme.sh" ] && . "$HOME/.config/daybreak/theme.sh"\n'
        }
    elif "fish" in shell_name:
        return {
            "path": home / ".config" / "fish" / "config.fish",
            "hook": '\n# Daybreak Theme Hook\nif test -f "$HOME/.config/daybreak/theme.fish"\n    source "$HOME/.config/daybreak/theme.fish"\nend\n'
        }
    return None

def install_shell_hook():
    system = platform.system()
    
    if system == "Windows":
        _install_powershell_hook()
        return

    # Linux/Mac
    shell_path = os.environ.get("SHELL", "")
    if not shell_path:
        logger.warning("Could not detect shell (SHELL env var missing).")
        return

    shell_name = Path(shell_path).name.lower()
    config = get_shell_config(shell_name)

    if not config:
        logger.warning(f"Shell '{shell_name}' is not currently supported for auto-setup.")
        logger.info("Please manually add the source command to your shell configuration.")
        return

    rc_path = config["path"]
    hook_content = config["hook"]

    _write_hook(rc_path, hook_content, shell_name)

def _install_powershell_hook():
    # PowerShell Profile
    # On Windows, usually $HOME\Documents\PowerShell\Microsoft.PowerShell_profile.ps1
    # or $HOME\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
    
    # We can try to detect common paths or rely on `subprocess` to ask PowerShell for its profile path?
    # Running a subprocess is safest.
    import subprocess
    
    try:
        # Ask PowerShell for the CurrentUserCurrentHost profile path
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Write-Host $PROFILE.CurrentUserCurrentHost"],
            capture_output=True, text=True
        )
        profile_path_str = result.stdout.strip()
        if not profile_path_str:
            # Try pwsh (PowerShell Core)
             result = subprocess.run(
                ["pwsh", "-NoProfile", "-Command", "Write-Host $PROFILE.CurrentUserCurrentHost"],
                capture_output=True, text=True
            )
             profile_path_str = result.stdout.strip()

        if not profile_path_str:
            logger.warning("Could not determine PowerShell profile path.")
            return
            
        rc_path = Path(profile_path_str)
        
        # PowerShell Hook
        # Note: using `use strict` or similar might break simple concatenation so we just append.
        hook = '\n# Daybreak Theme Hook\nif (Test-Path "$HOME/.config/daybreak/theme.ps1") {\n    . "$HOME/.config/daybreak/theme.ps1"\n}\n'
        
        _write_hook(rc_path, hook, "PowerShell")
        
    except FileNotFoundError:
        logger.warning("PowerShell executable not found.")
    except Exception as e:
        logger.error(f"Failed to install PowerShell hook: {e}")

def _write_hook(rc_path, hook, shell_name):
    if not rc_path.exists():
        logger.info(f"Config file {rc_path} not found. Creating it...")
        try:
            rc_path.parent.mkdir(parents=True, exist_ok=True)
            rc_path.touch()
        except Exception as e:
            logger.error(f"Failed to create config file: {e}")
            return

    try:
        content = rc_path.read_text(encoding='utf-8', errors='ignore')
        
        # Simple check for duplication
        if "daybreak/theme" in content:
            logger.info(f"Daybreak hook already found in {rc_path}. Skipping.")
            return

        with open(rc_path, "a", encoding='utf-8') as f:
            f.write(hook)
        
        logger.info(f"Successfully added Daybreak hook to {shell_name} config:")
        logger.info(f"  -> {rc_path}")
        logger.info("Restart your shell or source the file to apply changes.")
        
    except Exception as e:
        logger.error(f"Failed to write to config file: {e}")
