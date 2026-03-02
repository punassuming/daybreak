import logging
import os
from pathlib import Path

from daybreak.config import config

from .jsonc import dump_json_file, load_jsonc_file

logger = logging.getLogger("daybreak")

OBSIDIAN_GLOBAL_SETTINGS = Path(r"obsidian\obsidian.json")


class ObsidianAdapter:
    name = "obsidian"

    def apply_mode(self, mode: str, theme_name: str, palette: dict = None):
        if os.name != "nt":
            return

        app_data = os.environ.get("APPDATA")
        if not app_data:
            return

        target_theme = config.get(
            "integrations",
            f"obsidian_{mode}_theme",
            "moonstone" if mode == "light" else "obsidian",
        )

        global_path = Path(app_data) / OBSIDIAN_GLOBAL_SETTINGS
        if not global_path.exists():
            logger.debug("Obsidian: global settings file not found, skipping.")
            return

        vault_paths = []
        try:
            global_data = load_jsonc_file(global_path)
            changed = False
            if isinstance(global_data, dict):
                if global_data.get("theme") != target_theme:
                    global_data["theme"] = target_theme
                    changed = True

                vault_paths = _extract_vault_paths(global_data)

            if changed:
                dump_json_file(global_path, global_data)
                logger.info(f"Obsidian: Applied theme '{target_theme}' to {global_path}")
        except Exception as exc:
            logger.warning(f"Obsidian: Failed to update {global_path}: {exc}")

        for vault_path in vault_paths:
            app_json = vault_path / ".obsidian" / "app.json"
            if not app_json.exists():
                continue
            try:
                app_data_json = load_jsonc_file(app_json)
                if not isinstance(app_data_json, dict):
                    continue
                if app_data_json.get("theme") == target_theme:
                    continue
                app_data_json["theme"] = target_theme
                dump_json_file(app_json, app_data_json)
                logger.info(f"Obsidian: Applied theme '{target_theme}' to {app_json}")
            except Exception as exc:
                logger.warning(f"Obsidian: Failed to update {app_json}: {exc}")


def _extract_vault_paths(global_data: dict):
    vaults = global_data.get("vaults")
    if not isinstance(vaults, dict):
        return []

    results = []
    for entry in vaults.values():
        if not isinstance(entry, dict):
            continue
        path_value = entry.get("path")
        if isinstance(path_value, str) and path_value:
            vault_path = Path(path_value)
            if vault_path.exists():
                results.append(vault_path)
    return results
