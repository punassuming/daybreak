import logging
import os
from pathlib import Path

from daybreak.config import config

from .jsonc import dump_json_file, load_jsonc_file

logger = logging.getLogger("daybreak")


class WindowsTerminalAdapter:
    name = "windows_terminal"

    def apply_mode(self, mode: str, theme_name: str, palette: dict = None):
        if os.name != "nt":
            return

        target_scheme = config.get(
            "integrations",
            f"windows_terminal_{mode}_scheme",
            "One Half Light" if mode == "light" else "One Half Dark",
        )

        for settings_path in _iter_windows_terminal_settings():
            self._apply_scheme(settings_path, target_scheme)

    def _apply_scheme(self, path: Path, target_scheme: str):
        try:
            data = load_jsonc_file(path)
        except Exception as exc:
            logger.warning(f"Windows Terminal: Failed to parse {path}: {exc}")
            return

        changed = False
        profiles = data.setdefault("profiles", {})
        defaults = profiles.setdefault("defaults", {})
        if defaults.get("colorScheme") != target_scheme:
            defaults["colorScheme"] = target_scheme
            changed = True

        profile_list = profiles.get("list", [])
        if isinstance(profile_list, list):
            for entry in profile_list:
                if isinstance(entry, dict) and "colorScheme" in entry:
                    if entry.get("colorScheme") != target_scheme:
                        entry["colorScheme"] = target_scheme
                        changed = True

        if changed:
            try:
                dump_json_file(path, data)
                logger.info(f"Windows Terminal: Applied colorScheme '{target_scheme}' to {path}")
            except Exception as exc:
                logger.warning(f"Windows Terminal: Failed writing {path}: {exc}")


def _iter_windows_terminal_settings():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return []

    base = Path(local_app_data)
    results = []
    seen = set()

    packaged_root = base / "Packages"
    if packaged_root.exists():
        for package_dir in packaged_root.iterdir():
            if not package_dir.is_dir():
                continue
            if not package_dir.name.startswith("Microsoft.WindowsTerminal"):
                continue
            candidate = package_dir / "LocalState" / "settings.json"
            if candidate.exists() and str(candidate) not in seen:
                results.append(candidate)
                seen.add(str(candidate))

    unpackaged_candidate = base / "Microsoft" / "Windows Terminal" / "settings.json"
    if unpackaged_candidate.exists() and str(unpackaged_candidate) not in seen:
        results.append(unpackaged_candidate)

    return results
