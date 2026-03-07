import argparse
import logging

from daybreak.cli.runtime import build_orchestrator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("daybreak")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Daybreak: Toggle system and application themes.")
    parser.add_argument(
        "mode",
        choices=["light", "dark", "toggle", "select", "setup", "tray"],
        nargs="?",
        default="toggle",
        help="Mode to switch to, 'select' for UI, 'setup' to install hooks, or 'tray' for Windows tray mode",
    )
    args = parser.parse_args(argv)

    if args.mode == "select":
        from daybreak.interactive import run_interactive_selector

        run_interactive_selector()
        return

    if args.mode == "setup":
        from daybreak.shell_setup import install_shell_hook

        install_shell_hook()
        return

    if args.mode == "tray":
        from daybreak.windows_tray import run_windows_tray

        run_windows_tray()
        return

    orchestrator = build_orchestrator()

    if args.mode == "toggle":
        target_mode, theme_name = orchestrator.apply_toggle()
    else:
        target_mode = args.mode
        theme_name = orchestrator.apply(target_mode)

    logger.info(f"Switched to {target_mode} mode using theme '{theme_name}'.")
