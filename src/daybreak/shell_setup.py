import os
import platform
import logging
import shutil
import shlex
import stat
import subprocess
import sys
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
