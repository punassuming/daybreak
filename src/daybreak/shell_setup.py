import os
import platform
import logging
import shutil
import shlex
import json
import stat
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger("daybreak")


def _normalize_integrations_section_text(content: str) -> str:
    lines = content.splitlines()
    output_lines = []
    integrations = {}
    integrations_order = []
    insert_at = None
    in_integrations = False

    def _set_integration(key: str, rhs: str):
        if not key:
            return
        if key in integrations:
            integrations_order.remove(key)
        integrations[key] = rhs
        integrations_order.append(key)

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section_name = stripped[1:-1].strip()
            if section_name == "integrations":
                in_integrations = True
                if insert_at is None:
                    insert_at = len(output_lines)
                continue
            in_integrations = False
            output_lines.append(line)
            continue

        if in_integrations:
            parts = line.split("=", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                rhs = parts[1].strip()
                if key and rhs:
                    _set_integration(key, rhs)
            continue

        output_lines.append(line)

    if not integrations:
        return content if content.endswith("\n") else content + "\n"

    if insert_at is None:
        insert_at = len(output_lines)

    block = []
    if insert_at > 0 and output_lines[insert_at - 1].strip() != "":
        block.append("")
    block.append("[integrations]")
    for key in integrations_order:
        block.append(f"{key} = {integrations[key]}")
    if insert_at < len(output_lines) and output_lines[insert_at].strip() != "":
        block.append("")

    normalized_lines = output_lines[:insert_at] + block + output_lines[insert_at:]
    return "\n".join(normalized_lines).rstrip() + "\n"


def _normalize_integrations_section_file(path: Path) -> bool:
    if not path.exists():
        return False
    original = path.read_text(encoding="utf-8")
    normalized = _normalize_integrations_section_text(original)
    if normalized == original:
        return False
    path.write_text(normalized, encoding="utf-8")
    return True


def refresh_generated_artifacts():
    """
    Refresh Daybreak-owned generated files in the config directory.

    This is best-effort and intentionally avoids applying system/terminal mode
    globally. It regenerates shared artifacts and Neovim helper files based on
    the currently detected (or last known) mode.
    """
    from daybreak.config import config
    from daybreak.core.artifacts import generate_artifacts
    from daybreak.core.theme_model import normalize_mode
    from daybreak.core.theme_registry import ThemeRegistry
    from daybreak.terminals.neovim import Neovim

    mode = None

    # Prefer runtime-detected current mode when available.
    try:
        from daybreak.cli.runtime import build_orchestrator

        mode = normalize_mode(build_orchestrator().get_current_mode())
    except Exception as exc:
        logger.debug(f"Could not detect current mode during setup refresh: {exc}")

    # Fallback to last generated mode from palette artifact.
    if mode not in ("light", "dark"):
        try:
            palette_path = config.config_dir / "palette.json"
            if palette_path.exists():
                data = json.loads(palette_path.read_text(encoding="utf-8"))
                candidate = data.get("mode")
                if candidate in ("light", "dark"):
                    mode = candidate
        except Exception as exc:
            logger.debug(f"Could not read palette mode during setup refresh: {exc}")

    if mode not in ("light", "dark"):
        mode = "light"

    try:
        if _normalize_integrations_section_file(config.config_file):
            logger.info(f"Normalized duplicate integrations sections in {config.config_file}")

        registry = ThemeRegistry()
        theme_name = config.get_mode_theme_name(mode)
        palette = registry.get_palette(theme_name, mode)
        tokens = registry.get_tokens(theme_name, mode)
        accent_tokens = registry.get_accent_tokens(theme_name, mode)
        generate_artifacts(config.config_dir, theme_name, mode, tokens, accent_tokens, palette)
        neovim = Neovim(config_dir=config.config_dir)
        neovim._generate_helper_plugin()
        neovim._generate_bootstrap_plugin()
        neovim.set_mode(mode)
        logger.info(f"Refreshed Daybreak generated artifacts ({mode}: {theme_name}).")
    except Exception as exc:
        logger.warning(f"Failed to refresh Daybreak generated artifacts: {exc}")

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
        _install_windows_tray_launcher()
        return

    if system == "Linux":
        _install_linux_desktop_entry()
        _install_linux_tray_autostart()

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


def _get_linux_applications_dir() -> Path:
    return Path.home() / ".local" / "share" / "applications"


def _get_windows_programs_dir() -> Path:
    appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    return appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs"


def _get_windows_startup_dir() -> Path:
    return _get_windows_programs_dir() / "Startup"


def _build_daybreak_command(*args, prefer_gui=False) -> str:
    gui_executable = None
    if prefer_gui:
        gui_executable = shutil.which("daybreak-tray.exe") or shutil.which("daybreak-tray")

    if gui_executable:
        parts = [gui_executable]
    else:
        executable = shutil.which("daybreak.exe") or shutil.which("daybreak")
        if executable:
            parts = [executable, *args]
        else:
            python_executable = Path(sys.executable)
            if prefer_gui and python_executable.name.lower() == "python.exe":
                pythonw = python_executable.with_name("pythonw.exe")
                if pythonw.exists():
                    python_executable = pythonw
            parts = [str(python_executable), "-m", "daybreak", *args]

    if platform.system() == "Windows":
        return subprocess.list2cmdline(parts)

    return shlex.join(parts)


def _install_linux_desktop_entry():
    applications_dir = _get_linux_applications_dir()
    applications_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = applications_dir / "daybreak.desktop"
    command = _build_daybreak_command()
    desktop_file.write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "Name=Daybreak",
                "Comment=Toggle System & Terminal Theme",
                f"Exec={command} toggle",
                "Icon=preferences-desktop-display-color",
                "Type=Application",
                "Categories=Utility;System;",
                "Terminal=false",
                "Actions=Light;Dark;Select;",
                "",
                "[Desktop Action Light]",
                "Name=Switch to Light",
                f"Exec={command} light",
                "Icon=weather-clear",
                "",
                "[Desktop Action Dark]",
                "Name=Switch to Dark",
                f"Exec={command} dark",
                "Icon=weather-clear-night",
                "",
                "[Desktop Action Select]",
                "Name=Select Theme...",
                f"Exec={command} select",
                "Icon=preferences-desktop-theme",
                "Terminal=true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    desktop_file.chmod(desktop_file.stat().st_mode | stat.S_IXUSR)
    logger.info(f"Installed Daybreak desktop launcher at {desktop_file}")


def _install_linux_tray_autostart():
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    desktop_file = autostart_dir / "daybreak-tray.desktop"
    command = _build_daybreak_command("tray")
    desktop_file.write_text(
        "\n".join(
            [
                "[Desktop Entry]",
                "Name=Daybreak Tray",
                "Comment=Daybreak theme-switcher system tray icon",
                f"Exec={command}",
                "Icon=preferences-desktop-display-color",
                "Type=Application",
                "Categories=Utility;System;",
                "Terminal=false",
                "X-KDE-autostart-after=panel",
                "X-KDE-StartupNotify=false",
                "X-GNOME-Autostart-enabled=true",
                "Hidden=false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    desktop_file.chmod(desktop_file.stat().st_mode | stat.S_IXUSR)
    logger.info(f"Installed Daybreak tray autostart at {desktop_file}")


def _install_windows_tray_launcher():
    command = _build_daybreak_command("tray", prefer_gui=True)
    double_quote = '"'
    launcher_script = '\n'.join(
        [
            'Set shell = CreateObject("WScript.Shell")',
            f'shell.Run "{command.replace(double_quote, double_quote * 2)}", 0',
            "",
        ]
    )

    programs_dir = _get_windows_programs_dir()
    startup_dir = _get_windows_startup_dir()

    for directory in (programs_dir, startup_dir):
        directory.mkdir(parents=True, exist_ok=True)

    launchers = [
        programs_dir / "Daybreak Tray.vbs",
        startup_dir / "Daybreak Tray.vbs",
    ]

    for path in launchers:
        path.write_text(launcher_script, encoding="utf-8")
        logger.info(f"Installed Daybreak tray launcher at {path}")

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
