import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.linux_tray import (
    ID_DARK,
    ID_EXIT,
    ID_LIGHT,
    ID_OPEN_CONFIG,
    ID_RUN_SETUP,
    ID_TOGGLE,
    LinuxTrayController,
    _encode_pixmap_for_dbus,
    _render_sni_icon_pixels,
)


class LinuxTrayControllerTests(unittest.TestCase):
    def _make_controller(self, mode="dark", theme="Nord"):
        orchestrator = Mock()
        orchestrator.get_current_mode.return_value = mode
        with patch("daybreak.linux_tray.LinuxTrayController.__init__") as mock_init:
            mock_init.return_value = None
            controller = LinuxTrayController.__new__(LinuxTrayController)
        controller.orchestrator = orchestrator
        controller.current_mode = mode
        controller.current_theme = theme
        controller._config = Mock()
        controller._config.config_file = Path("/tmp/test_config.toml")
        return controller

    def test_tooltip_uses_current_mode(self):
        controller = self._make_controller("dark", "Nord")
        self.assertEqual(controller.tooltip_text(), "Daybreak (Dark: Nord)")
        self.assertEqual(controller.status_text(), "Dark mode - Nord")

    def test_toggle_command_updates_mode(self):
        controller = self._make_controller("light")
        controller.orchestrator.apply_toggle.return_value = ("dark", "Nord")

        result = controller.handle_command(ID_TOGGLE)

        self.assertTrue(result)
        self.assertEqual(controller.current_mode, "dark")
        controller.orchestrator.apply_toggle.assert_called_once_with()

    def test_light_and_dark_commands_apply_explicit_modes(self):
        controller = self._make_controller("dark")
        controller.orchestrator.apply.side_effect = ["Catppuccin", "Nord"]

        self.assertTrue(controller.handle_command(ID_LIGHT))
        self.assertEqual(controller.current_mode, "light")
        self.assertTrue(controller.handle_command(ID_DARK))
        self.assertEqual(controller.current_mode, "dark")

        controller.orchestrator.apply.assert_any_call("light")
        controller.orchestrator.apply.assert_any_call("dark")

    def test_exit_command_returns_false(self):
        controller = self._make_controller("light")
        self.assertFalse(controller.handle_command(ID_EXIT))

    def test_open_config_and_setup_commands_delegate(self):
        controller = self._make_controller("light")
        controller.open_config = Mock()
        controller.run_setup = Mock()

        self.assertTrue(controller.handle_command(ID_OPEN_CONFIG))
        self.assertTrue(controller.handle_command(ID_RUN_SETUP))

        controller.open_config.assert_called_once_with()
        controller.run_setup.assert_called_once_with()

    def test_open_config_uses_xdg_open(self):
        controller = self._make_controller("light")
        with patch("daybreak.linux_tray.subprocess.Popen") as mock_popen:
            controller.open_config()
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        self.assertEqual(cmd[0], "xdg-open")


class SniPixmapTests(unittest.TestCase):
    def test_light_and_dark_pixels_correct_size(self):
        size = 22
        light = _render_sni_icon_pixels("light", size)
        dark = _render_sni_icon_pixels("dark", size)

        self.assertEqual(len(light), size * size * 4)
        self.assertEqual(len(dark), size * size * 4)

    def test_light_and_dark_pixels_differ(self):
        light = _render_sni_icon_pixels("light", 22)
        dark = _render_sni_icon_pixels("dark", 22)
        self.assertNotEqual(light, dark)

    def test_pixels_are_argb_not_bgra(self):
        # ARGB: fully transparent pixels should have alpha=0 as first byte of each 4-byte group.
        # The sun icon has transparent background pixels. Check that *some* pixel has alpha as
        # the first channel by verifying the format differs from raw BGRA.
        from daybreak.windows_tray import _render_mode_icon_pixels

        size = 22
        bgra = _render_mode_icon_pixels("light", size)
        argb = _render_sni_icon_pixels("light", size)

        # For any non-transparent pixel, byte order must be swapped
        for i in range(0, len(bgra), 4):
            blue_bgra = bgra[i]
            alpha_argb = argb[i]
            red_bgra = bgra[i + 2]
            red_argb = argb[i + 1]
            # If the windows pixel is non-transparent, verify the conversion
            if bgra[i + 3] != 0:
                self.assertEqual(alpha_argb, bgra[i + 3])  # alpha moved to front
                self.assertEqual(red_argb, red_bgra)        # red moved to second

    def test_encode_pixmap_structure(self):
        size = 22
        pixels = _render_sni_icon_pixels("light", size)
        result = _encode_pixmap_for_dbus(pixels, size)

        self.assertEqual(len(result), 1)
        struct = result[0]
        self.assertEqual(int(struct[0]), size)   # width
        self.assertEqual(int(struct[1]), size)   # height
        self.assertEqual(len(struct[2]), size * size * 4)  # pixel data length


class AutostartInstallationTests(unittest.TestCase):
    def test_installs_autostart_desktop_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            autostart_dir = Path(tmpdir) / ".config" / "autostart"

            with patch("daybreak.shell_setup.Path.home", return_value=Path(tmpdir)):
                from daybreak.shell_setup import _install_linux_tray_autostart

                _install_linux_tray_autostart()

            desktop_file = autostart_dir / "daybreak-tray.desktop"
            self.assertTrue(desktop_file.exists())

            content = desktop_file.read_text(encoding="utf-8")
            self.assertIn("X-KDE-autostart-after=panel", content)
            self.assertIn("X-GNOME-Autostart-enabled=true", content)
            self.assertIn("Terminal=false", content)
            self.assertIn("[Desktop Entry]", content)

    def test_autostart_exec_contains_tray(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("daybreak.shell_setup.Path.home", return_value=Path(tmpdir)):
                from daybreak.shell_setup import _install_linux_tray_autostart

                _install_linux_tray_autostart()

            desktop_file = Path(tmpdir) / ".config" / "autostart" / "daybreak-tray.desktop"
            content = desktop_file.read_text(encoding="utf-8")
            exec_line = next(line for line in content.splitlines() if line.startswith("Exec="))
            self.assertIn("tray", exec_line)


class RunLinuxTrayGuardTests(unittest.TestCase):
    def test_raises_on_non_linux(self):
        with patch("daybreak.linux_tray.platform.system", return_value="Windows"):
            from daybreak.linux_tray import run_linux_tray

            with self.assertRaises(RuntimeError):
                run_linux_tray()


if __name__ == "__main__":
    unittest.main()
