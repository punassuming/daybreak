import os
import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.config import ConfigManager


class ConfigMigrationTests(unittest.TestCase):
    def test_migrates_legacy_terminal_theme_keys(self):
        manager = ConfigManager(config_dir=Path.cwd())
        migrated, changed = manager._migrate(
            {
                "system": {"linux_kde_light": "BreathLight", "linux_kde_dark": "BreathDark"},
                "terminal": {"theme": "Nord", "theme_light": "Catppuccin", "theme_dark": "Tokyo Night"},
            }
        )
        self.assertTrue(changed)
        self.assertEqual(migrated["schema_version"], 2)
        self.assertEqual(migrated["theme"]["light"], "Catppuccin")
        self.assertEqual(migrated["theme"]["dark"], "Tokyo Night")
        self.assertNotIn("terminal", migrated)

    def test_honors_env_config_dir_override(self):
        temp_dir = str(Path.cwd() / ".daybreak-test-config")
        os.environ["DAYBREAK_CONFIG_DIR"] = temp_dir
        try:
            manager = ConfigManager()
            self.assertEqual(manager.config_dir, Path(temp_dir))
        finally:
            os.environ.pop("DAYBREAK_CONFIG_DIR", None)

    def test_migration_backfills_neovim_integration_keys(self):
        manager = ConfigManager(config_dir=Path.cwd())
        migrated, changed = manager._migrate(
            {
                "schema_version": 2,
                "system": {"linux_kde_light": "BreathLight", "linux_kde_dark": "BreathDark"},
                "theme": {"active": "Nord", "light": "Nord", "dark": "Nord"},
                "integrations": {
                    "windows_terminal_light_scheme": "One Half Light",
                    "windows_terminal_dark_scheme": "One Half Dark",
                    "obsidian_light_theme": "moonstone",
                    "obsidian_dark_theme": "obsidian",
                },
            }
        )
        self.assertTrue(changed)
        self.assertEqual(migrated["integrations"]["neovim_light_scheme"], "tokyonight-day")
        self.assertEqual(migrated["integrations"]["neovim_dark_scheme"], "tokyonight")

    def test_reload_reflects_updated_file_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            config_file = config_dir / "config.toml"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file.write_text(
                """schema_version = 2

[system]
linux_kde_light = "BreathLight"
linux_kde_dark = "BreathDark"
windows_light_reg = 1
windows_dark_reg = 0

[theme]
active = "Nord"
light = "Nord"
dark = "Nord"

[integrations]
windows_terminal_light_scheme = "One Half Light"
windows_terminal_dark_scheme = "One Half Dark"
obsidian_light_theme = "moonstone"
obsidian_dark_theme = "obsidian"
neovim_light_scheme = "tokyonight-day"
neovim_dark_scheme = "tokyonight"
""",
                encoding="utf-8",
            )
            manager = ConfigManager(config_dir=config_dir)
            self.assertEqual(manager.get_mode_theme_name("dark"), "Nord")

            config_file.write_text(
                """schema_version = 2

[system]
linux_kde_light = "BreathLight"
linux_kde_dark = "BreathDark"
windows_light_reg = 1
windows_dark_reg = 0

[theme]
active = "One Dark"
light = "Monokai"
dark = "One Dark"

[integrations]
windows_terminal_light_scheme = "One Half Light"
windows_terminal_dark_scheme = "One Half Dark"
obsidian_light_theme = "moonstone"
obsidian_dark_theme = "obsidian"
neovim_light_scheme = "tokyonight-day"
neovim_dark_scheme = "onedark"
""",
                encoding="utf-8",
            )

            manager.reload()
            self.assertEqual(manager.get_mode_theme_name("dark"), "One Dark")
            self.assertEqual(manager.get("integrations", "neovim_dark_scheme"), "onedark")


if __name__ == "__main__":
    unittest.main()
