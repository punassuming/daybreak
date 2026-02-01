import argparse
import sys
import platform
import logging
from daybreak.platforms.linux_kde import KDELinuxHandler
from daybreak.platforms.windows import WindowsHandler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("daybreak")

def get_platform_handler():
    os_name = platform.system()
    if os_name == "Linux":
        # Todo: Add detection for DE (GNOME, KDE, etc.)
        # For now, assuming KDE as per requirements
        return KDELinuxHandler()
    elif os_name == "Windows":
        return WindowsHandler()
    else:
        raise NotImplementedError(f"OS {os_name} not supported yet.")

def main():
    parser = argparse.ArgumentParser(description="Daybreak: Toggle system and application themes.")
    parser.add_argument("mode", choices=["light", "dark", "toggle", "select"], nargs="?", default="toggle", help="Mode to switch to or 'select' for interactive UI")
    
    args = parser.parse_args()
    
    if args.mode == "select":
        from daybreak.interactive import run_interactive_selector
        run_interactive_selector()
        return

    handler = get_platform_handler()
    
    target_mode = args.mode
    if target_mode == "toggle":
        current = handler.get_current_mode()
        target_mode = "light" if current == "dark" else "dark"
    
    logger.info(f"Switching to {target_mode} mode...")
    handler.set_mode(target_mode)
    logger.info("Done.")

if __name__ == "__main__":
    main()
