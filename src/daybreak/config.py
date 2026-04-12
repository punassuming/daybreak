import copy
import logging
import os
from pathlib import Path

try:
    import toml as _toml_lib
except ImportError:  # pragma: no cover - exercised via fallback paths
    _toml_lib = None

import tomllib

logger = logging.getLogger("daybreak")

CURRENT_SCHEMA_VERSION = 2

DEFAULT_CONFIG = {
    "schema_version": CURRENT_SCHEMA_VERSION,
    "system": {
        "linux_kde_light": "BreathLight",
        "linux_kde_dark": "BreathDark",
        "windows_light_reg": 1,
        "windows_dark_reg": 0,
    },
    "theme": {
        "active": "Nord",
        "light": "Nord",
        "dark": "Nord",
    },
    "integrations": {
        "windows_terminal_light_scheme": "One Half Light",
        "windows_terminal_dark_scheme": "One Half Dark",
        "obsidian_light_theme": "moonstone",
        "obsidian_dark_theme": "obsidian",
        "neovim_light_scheme": "tokyonight-day",
        "neovim_dark_scheme": "tokyonight",
    },
}


class ConfigManager:
    def __init__(self, config_dir=None):
        env_config_dir = os.environ.get("DAYBREAK_CONFIG_DIR")
        if config_dir is None and env_config_dir:
            self.config_dir = Path(env_config_dir)
        elif config_dir is None:
            self.config_dir = Path(os.path.expanduser("~/.config/daybreak"))
        else:
            self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "config.toml"
        self.data = self._load()

    def _load(self):
        if not self.config_file.exists():
            return self._create_default()

        try:
            raw_data = _load_toml(self.config_file)
        except Exception as exc:
            logger.error(f"Failed to load config: {exc}. Using defaults.")
            return copy.deepcopy(DEFAULT_CONFIG)

        migrated, changed = self._migrate(raw_data)
        if changed:
            try:
                self._save(migrated)
            except Exception as exc:
                logger.warning(f"Failed to write migrated config: {exc}")
        return migrated

    def _create_default(self):
        data = copy.deepcopy(DEFAULT_CONFIG)
        try:
            self._save(data)
            logger.info(f"Created default config at {self.config_file}")
        except Exception as exc:
            logger.warning(f"Failed to persist default config: {exc}")
        return data

    def _save(self, data):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as handle:
            _dump_toml(data, handle)

    def _migrate(self, raw_data):
        if not isinstance(raw_data, dict):
            return copy.deepcopy(DEFAULT_CONFIG), True

        migrated = copy.deepcopy(raw_data)
        changed = False

        if migrated.get("schema_version") != CURRENT_SCHEMA_VERSION:
            migrated["schema_version"] = CURRENT_SCHEMA_VERSION
            changed = True

        system_cfg = migrated.get("system")
        if not isinstance(system_cfg, dict):
            system_cfg = {}
            changed = True
        for key, default_value in DEFAULT_CONFIG["system"].items():
            if key not in system_cfg:
                system_cfg[key] = default_value
                changed = True
        migrated["system"] = system_cfg

        legacy_terminal = migrated.get("terminal", {})
        if not isinstance(legacy_terminal, dict):
            legacy_terminal = {}

        theme_cfg = migrated.get("theme")
        if not isinstance(theme_cfg, dict):
            theme_cfg = {}
            changed = True

        active = theme_cfg.get("active") or legacy_terminal.get("theme") or DEFAULT_CONFIG["theme"]["active"]
        light = theme_cfg.get("light") or legacy_terminal.get("theme_light") or active
        dark = theme_cfg.get("dark") or legacy_terminal.get("theme_dark") or active

        normalized_theme = {
            "active": active,
            "light": light,
            "dark": dark,
        }
        if theme_cfg != normalized_theme:
            changed = True
        migrated["theme"] = normalized_theme

        integrations_cfg = migrated.get("integrations")
        if not isinstance(integrations_cfg, dict):
            integrations_cfg = {}
            changed = True
        for key, default_value in DEFAULT_CONFIG["integrations"].items():
            if key not in integrations_cfg:
                integrations_cfg[key] = default_value
                changed = True
        migrated["integrations"] = integrations_cfg

        if "terminal" in migrated:
            migrated.pop("terminal", None)
            changed = True

        return migrated, changed

    def save(self):
        try:
            self._save(self.data)
        except Exception as exc:
            logger.warning(f"Failed to save config: {exc}")

    def reload(self):
        """Reload config data from disk, keeping prior data on failure."""
        try:
            self.data = self._load()
        except Exception as exc:
            logger.warning(f"Failed to reload config: {exc}")

    def get(self, section, key, default=None):
        section_data = self.data.get(section, {})
        if not isinstance(section_data, dict):
            return default
        return section_data.get(key, default)

    def get_system_theme(self, os_type, mode):
        if os_type == "linux_kde":
            key = "linux_kde_light" if mode == "light" else "linux_kde_dark"
            return self.get("system", key, DEFAULT_CONFIG["system"][key])
        return None

    def get_active_theme_name(self):
        return self.get("theme", "active", DEFAULT_CONFIG["theme"]["active"])

    def get_mode_theme_name(self, mode):
        if mode == "light":
            return self.get("theme", "light", self.get_active_theme_name())
        if mode == "dark":
            return self.get("theme", "dark", self.get_active_theme_name())
        return self.get_active_theme_name()

    def get_terminal_theme_name(self, mode=None):
        # Backward-compatible alias used by legacy terminal code.
        if mode in ("light", "dark"):
            return self.get_mode_theme_name(mode)
        return self.get_active_theme_name()

    def set_mode_themes(self, light_theme: str, dark_theme: str):
        self.data.setdefault("theme", {})
        self.data["theme"]["light"] = light_theme
        self.data["theme"]["dark"] = dark_theme
        if not self.data["theme"].get("active"):
            self.data["theme"]["active"] = dark_theme
        self.save()


def _load_toml(path: Path):
    if _toml_lib is not None:
        return _toml_lib.load(path)
    with open(path, "rb") as handle:
        return tomllib.load(handle)


def _dump_toml(data: dict, handle):
    if _toml_lib is not None:
        _toml_lib.dump(data, handle)
        return
    handle.write(_to_toml(data))


def _to_toml(data: dict) -> str:
    lines = []
    _append_table(lines, data, prefix=None)
    return "\n".join(lines).strip() + "\n"


def _append_table(lines, table, prefix):
    scalar_items = []
    nested_items = []

    for key, value in table.items():
        if isinstance(value, dict):
            nested_items.append((key, value))
        else:
            scalar_items.append((key, value))

    if prefix:
        lines.append(f"[{prefix}]")
    for key, value in scalar_items:
        lines.append(f"{key} = {_format_toml_value(value)}")

    if scalar_items and nested_items:
        lines.append("")

    for index, (key, nested) in enumerate(nested_items):
        child_prefix = key if not prefix else f"{prefix}.{key}"
        _append_table(lines, nested, child_prefix)
        if index != len(nested_items) - 1:
            lines.append("")


def _format_toml_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


config = ConfigManager()
