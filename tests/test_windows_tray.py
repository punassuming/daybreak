import sys
import unittest
from ctypes import c_size_t
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.windows_tray import (
    ID_DARK,
    ID_EXIT,
    ID_LIGHT,
    ID_OPEN_CONFIG,
    ID_RUN_SETUP,
    ID_TOGGLE,
    TrayController,
    _configure_win32_api,
    _menu_position_from_wparam,
    _render_mode_icon_pixels,
)


class DummyFunction:
    pass


class TrayControllerTests(unittest.TestCase):
    def test_tooltip_uses_current_mode(self):
        orchestrator = Mock()
        orchestrator.get_current_mode.return_value = "dark"

        controller = TrayController(orchestrator=orchestrator)

        self.assertEqual(controller.tooltip_text(), "Daybreak (Dark: Nord)")
        self.assertEqual(controller.status_text(), "Dark mode - Nord")

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

    def test_open_config_and_setup_commands_delegate(self):
        controller = TrayController(orchestrator=Mock(get_current_mode=Mock(return_value="light")))
        controller.open_config = Mock()
        controller.run_setup = Mock()

        self.assertTrue(controller.handle_command(ID_OPEN_CONFIG))
        self.assertTrue(controller.handle_command(ID_RUN_SETUP))

        controller.open_config.assert_called_once_with()
        controller.run_setup.assert_called_once_with()

    def test_mode_icon_pixels_differ_between_light_and_dark(self):
        light_pixels = _render_mode_icon_pixels("light", size=16)
        dark_pixels = _render_mode_icon_pixels("dark", size=16)

        self.assertEqual(len(light_pixels), 16 * 16 * 4)
        self.assertEqual(len(dark_pixels), 16 * 16 * 4)
        self.assertNotEqual(light_pixels, dark_pixels)

    def test_menu_position_decodes_signed_coordinates(self):
        self.assertEqual(_menu_position_from_wparam((250 << 16) | 120), (120, 250))
        self.assertEqual(_menu_position_from_wparam((0xFFFF << 16) | 0xFFFF), None)

    def test_configure_win32_api_sets_pointer_sized_signatures(self):
        user32 = SimpleNamespace(
            RegisterClassW=DummyFunction(),
            CreateWindowExW=DummyFunction(),
            DefWindowProcW=DummyFunction(),
            DestroyWindow=DummyFunction(),
            LoadIconW=DummyFunction(),
            LoadCursorW=DummyFunction(),
            CreatePopupMenu=DummyFunction(),
            DestroyMenu=DummyFunction(),
            AppendMenuW=DummyFunction(),
            GetCursorPos=DummyFunction(),
            SetForegroundWindow=DummyFunction(),
            TrackPopupMenu=DummyFunction(),
            PostMessageW=DummyFunction(),
            GetMessageW=DummyFunction(),
            TranslateMessage=DummyFunction(),
            DispatchMessageW=DummyFunction(),
            PostQuitMessage=DummyFunction(),
            CreateIconIndirect=DummyFunction(),
            DestroyIcon=DummyFunction(),
        )
        shell32 = SimpleNamespace(Shell_NotifyIconW=DummyFunction())
        wintypes_module = SimpleNamespace(
            DWORD=int,
            LPCWSTR=str,
            HWND=int,
            HMENU=int,
            HINSTANCE=int,
            HANDLE=int,
            UINT=int,
            WPARAM=int,
            LPARAM=int,
            BOOL=bool,
            HICON=int,
            HCURSOR=int,
            WORD=int,
            HBITMAP=int,
            HGDIOBJ=int,
            LPVOID=object,
        )

        _configure_win32_api(user32, shell32, wintypes_module, "WNDCLASS_PTR", "POINT_PTR", "MSG_PTR", "NID_PTR")

        self.assertEqual(user32.RegisterClassW.argtypes, ["WNDCLASS_PTR"])
        self.assertEqual(user32.DefWindowProcW.argtypes, [int, int, int, int])
        self.assertEqual(user32.CreateWindowExW.argtypes[-1], object)
        self.assertEqual(user32.TrackPopupMenu.argtypes[-1], object)
        self.assertEqual(user32.TrackPopupMenu.restype, c_size_t)
        self.assertEqual(user32.GetMessageW.argtypes, ["MSG_PTR", int, int, int])
        self.assertEqual(shell32.Shell_NotifyIconW.argtypes, [int, "NID_PTR"])


if __name__ == "__main__":
    unittest.main()
