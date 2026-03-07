import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak import shell_setup


class ShellSetupTests(unittest.TestCase):
    def test_install_linux_desktop_entry_writes_launcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            applications_dir = Path(tmp) / "applications"
            with patch("daybreak.shell_setup._get_linux_applications_dir", return_value=applications_dir), patch(
                "daybreak.shell_setup.shutil.which", return_value="/usr/local/bin/daybreak"
            ):
                shell_setup._install_linux_desktop_entry()

            desktop_file = applications_dir / "daybreak.desktop"
            self.assertTrue(desktop_file.exists())
            content = desktop_file.read_text(encoding="utf-8")
            self.assertIn("Exec=/usr/local/bin/daybreak toggle", content)
            self.assertIn("Exec=/usr/local/bin/daybreak light", content)
            self.assertIn("Exec=/usr/local/bin/daybreak dark", content)
            self.assertIn("Exec=/usr/local/bin/daybreak select", content)

    def test_install_windows_tray_launcher_writes_hidden_launchers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            programs_dir = root / "Programs"
            startup_dir = programs_dir / "Startup"
            with patch("daybreak.shell_setup._get_windows_programs_dir", return_value=programs_dir), patch(
                "daybreak.shell_setup._get_windows_startup_dir", return_value=startup_dir
            ), patch(
                "daybreak.shell_setup.shutil.which",
                side_effect=[r"C:\Tools\daybreak-tray.exe", None, None],
            ), patch(
                "daybreak.shell_setup.platform.system", return_value="Windows"
            ):
                shell_setup._install_windows_tray_launcher()

            for launcher in (programs_dir / "Daybreak Tray.vbs", startup_dir / "Daybreak Tray.vbs"):
                self.assertTrue(launcher.exists())
                content = launcher.read_text(encoding="utf-8")
                self.assertIn(r'C:\Tools\daybreak-tray.exe', content)
                self.assertNotIn(r'C:\Tools\daybreak-tray.exe tray', content)
                self.assertIn("shell.Run", content)

    def test_install_shell_hook_on_windows_installs_tray_launcher(self):
        with patch("daybreak.shell_setup.platform.system", return_value="Windows"), patch(
            "daybreak.shell_setup._install_powershell_hook"
        ) as install_powershell_hook, patch(
            "daybreak.shell_setup._install_windows_tray_launcher"
        ) as install_windows_tray_launcher:
            shell_setup.install_shell_hook()

        install_powershell_hook.assert_called_once_with()
        install_windows_tray_launcher.assert_called_once_with()

    def test_install_shell_hook_on_linux_installs_desktop_entry_without_shell_env(self):
        with patch("daybreak.shell_setup.platform.system", return_value="Linux"), patch.dict(os.environ, {}, clear=True), patch(
            "daybreak.shell_setup._install_linux_desktop_entry"
        ) as install_linux_desktop_entry:
            shell_setup.install_shell_hook()

        install_linux_desktop_entry.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
