import os
import sys
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


if __name__ == "__main__":
    unittest.main()
