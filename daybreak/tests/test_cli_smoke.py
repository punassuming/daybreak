import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.cli.main import main


class CLISmokeTests(unittest.TestCase):
    def test_dark_dispatches_to_orchestrator(self):
        with patch("daybreak.cli.main.build_orchestrator") as build_orchestrator:
            orchestrator = build_orchestrator.return_value
            orchestrator.apply.return_value = "Nord"
            main(["dark"])
            orchestrator.apply.assert_called_once_with("dark")

    def test_toggle_dispatches_to_toggle_path(self):
        with patch("daybreak.cli.main.build_orchestrator") as build_orchestrator:
            orchestrator = build_orchestrator.return_value
            orchestrator.apply_toggle.return_value = ("light", "Nord")
            main(["toggle"])
            orchestrator.apply_toggle.assert_called_once_with()

    def test_select_dispatches_to_interactive(self):
        fake_module = types.ModuleType("daybreak.interactive")
        fake_module.run_interactive_selector = Mock()
        with patch.dict(sys.modules, {"daybreak.interactive": fake_module}):
            main(["select"])
        fake_module.run_interactive_selector.assert_called_once_with()

    def test_setup_dispatches_to_shell_setup(self):
        fake_module = types.ModuleType("daybreak.shell_setup")
        fake_module.install_shell_hook = Mock()
        with patch.dict(sys.modules, {"daybreak.shell_setup": fake_module}):
            main(["setup"])
        fake_module.install_shell_hook.assert_called_once_with()

    def test_tray_dispatches_to_windows_tray(self):
        fake_module = types.ModuleType("daybreak.windows_tray")
        fake_module.run_windows_tray = Mock()
        with patch.dict(sys.modules, {"daybreak.windows_tray": fake_module}):
            main(["tray"])
        fake_module.run_windows_tray.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
