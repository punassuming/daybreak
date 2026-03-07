import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.windows_tray import ID_DARK, ID_EXIT, ID_LIGHT, ID_TOGGLE, TrayController


class TrayControllerTests(unittest.TestCase):
    def test_tooltip_uses_current_mode(self):
        orchestrator = Mock()
        orchestrator.get_current_mode.return_value = "dark"

        controller = TrayController(orchestrator=orchestrator)

        self.assertEqual(controller.tooltip_text(), "Daybreak (Dark)")

    def test_toggle_command_updates_mode(self):
        orchestrator = Mock()
        orchestrator.get_current_mode.return_value = "light"
        orchestrator.apply_toggle.return_value = ("dark", "Nord")
        controller = TrayController(orchestrator=orchestrator)

        result = controller.handle_command(ID_TOGGLE)

        self.assertTrue(result)
        self.assertEqual(controller.current_mode, "dark")
        orchestrator.apply_toggle.assert_called_once_with()

    def test_light_and_dark_commands_apply_explicit_modes(self):
        orchestrator = Mock()
        orchestrator.get_current_mode.return_value = "dark"
        orchestrator.apply.side_effect = ["Catppuccin", "Nord"]
        controller = TrayController(orchestrator=orchestrator)

        self.assertTrue(controller.handle_command(ID_LIGHT))
        self.assertEqual(controller.current_mode, "light")
        self.assertTrue(controller.handle_command(ID_DARK))
        self.assertEqual(controller.current_mode, "dark")
        orchestrator.apply.assert_any_call("light")
        orchestrator.apply.assert_any_call("dark")

    def test_exit_command_stops_loop(self):
        controller = TrayController(orchestrator=Mock(get_current_mode=Mock(return_value="light")))

        self.assertFalse(controller.handle_command(ID_EXIT))


if __name__ == "__main__":
    unittest.main()
