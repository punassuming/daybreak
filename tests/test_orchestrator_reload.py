import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.config import ConfigManager
from daybreak.core.orchestrator import ThemeOrchestrator


class OrchestratorReloadTests(unittest.TestCase):
    def test_apply_reloads_config_for_long_lived_process(self):
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

            fake_config = ConfigManager(config_dir=config_dir)
            orch = ThemeOrchestrator(system_adapter=None, terminal_adapters=[])

            with patch("daybreak.core.orchestrator.config", fake_config):
                first_theme = orch.apply("dark")
                self.assertEqual(first_theme, "Nord")

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

                second_theme = orch.apply("dark")
                self.assertEqual(second_theme, "One Dark")


if __name__ == "__main__":
    unittest.main()
