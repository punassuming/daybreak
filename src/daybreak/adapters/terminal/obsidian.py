import logging
import os
from pathlib import Path

from daybreak.config import config

from .jsonc import dump_json_file, load_jsonc_file

logger = logging.getLogger("daybreak")

OBSIDIAN_GLOBAL_SETTINGS = Path(r"obsidian\obsidian.json")


class ObsidianAdapter:
    """Sets the "theme" key in Obsidian's global settings file
    (%APPDATA%\\obsidian\\obsidian.json), the app-wide default new vaults
    inherit.

    Deliberately does NOT also loop over every vault registered in that
    file and overwrite each vault's own .obsidian/app.json: that forces
    vaults with their own deliberate theme choice (e.g. a non-coding notes
    vault) to match Daybreak's mode too, which surprised a user in
    practice once this adapter was actually wired in. Global-only leaves
    per-vault choices alone.
    """

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

        try:
            global_data = load_jsonc_file(global_path)
            if not isinstance(global_data, dict):
                return
            if global_data.get("theme") == target_theme:
                return
            global_data["theme"] = target_theme
            dump_json_file(global_path, global_data)
            logger.info(f"Obsidian: Applied theme '{target_theme}' to {global_path}")
        except Exception as exc:
            logger.warning(f"Obsidian: Failed to update {global_path}: {exc}")
