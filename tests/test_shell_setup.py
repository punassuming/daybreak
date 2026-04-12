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
        ) as install_linux_desktop_entry, patch(
            "daybreak.shell_setup._install_linux_tray_autostart"
        ) as install_linux_tray_autostart:
            shell_setup.install_shell_hook()

        install_linux_desktop_entry.assert_called_once_with()
        install_linux_tray_autostart.assert_called_once_with()

    def test_refresh_generated_artifacts_runs_neovim_and_shared_artifacts(self):
        fake_config = type("Config", (), {})()
        fake_config.config_dir = Path("/tmp/daybreak-test")
        fake_config.config_file = Path("/tmp/daybreak-test/config.toml")
        fake_config.get_mode_theme_name = lambda mode: "Nord"

        fake_registry = type(
            "Registry",
            (),
            {
                "get_palette": lambda self, theme, mode: {"special": {}, "colors": {}},
                "get_tokens": lambda self, theme, mode: {"bg": "#000000", "fg": "#ffffff", "cursor": "#ffffff", "muted": "#888888", "primary": "#4488ff", "success": "#44aa66", "warning": "#ffaa33", "error": "#ff4455", "info": "#44bbff", "surface_1": "#111111", "surface_2": "#222222", "surface_3": "#333333"},
                "get_accent_tokens": lambda self, theme, mode: {"accent_primary": "#4488ff", "accent_secondary": "#7788aa", "accent_success": "#44aa66", "accent_warning": "#ffaa33", "accent_error": "#ff4455", "accent_selection": "#333333"},
            },
        )

        with patch("daybreak.config.config", fake_config), patch(
            "daybreak.core.theme_registry.ThemeRegistry", return_value=fake_registry()
        ), patch("daybreak.core.artifacts.generate_artifacts") as generate_artifacts, patch(
            "daybreak.terminals.neovim.Neovim"
        ) as neovim_cls, patch(
            "daybreak.cli.runtime.build_orchestrator"
        ) as build_orchestrator:
            build_orchestrator.return_value.get_current_mode.return_value = "dark"

            shell_setup.refresh_generated_artifacts()

        generate_artifacts.assert_called_once()
        neovim_cls.assert_called_once_with(config_dir=fake_config.config_dir)
        neovim_cls.return_value.set_mode.assert_called_once_with("dark")

    def test_normalize_integrations_section_text_dedupes_sections(self):
        content = """schema_version = 2

[theme]
active = "Nord"

[integrations]
neovim_dark_scheme = "nord"

[integrations]
windows_terminal_dark_scheme = "One Half Dark"

[integrations]
neovim_dark_scheme = "onedark"
"""
        normalized = shell_setup._normalize_integrations_section_text(content)
        self.assertEqual(normalized.count("[integrations]"), 1)
        self.assertIn('neovim_dark_scheme = "onedark"', normalized)
        self.assertIn('windows_terminal_dark_scheme = "One Half Dark"', normalized)
        self.assertEqual(normalized.count('neovim_dark_scheme = "onedark"'), 1)

    def test_refresh_generated_artifacts_normalizes_config_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            config_file = config_dir / "config.toml"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file.write_text(
                """schema_version = 2

[integrations]
neovim_dark_scheme = "nord"

[integrations]
neovim_dark_scheme = "onedark"
""",
                encoding="utf-8",
            )

            fake_config = type("Config", (), {})()
            fake_config.config_dir = config_dir
            fake_config.config_file = config_file
            fake_config.get_mode_theme_name = lambda mode: "Nord"

            fake_registry = type(
                "Registry",
                (),
                {
                    "get_palette": lambda self, theme, mode: {"special": {}, "colors": {}},
                    "get_tokens": lambda self, theme, mode: {"bg": "#000000", "fg": "#ffffff", "cursor": "#ffffff", "muted": "#888888", "primary": "#4488ff", "success": "#44aa66", "warning": "#ffaa33", "error": "#ff4455", "info": "#44bbff", "surface_1": "#111111", "surface_2": "#222222", "surface_3": "#333333"},
                    "get_accent_tokens": lambda self, theme, mode: {"accent_primary": "#4488ff", "accent_secondary": "#7788aa", "accent_success": "#44aa66", "accent_warning": "#ffaa33", "accent_error": "#ff4455", "accent_selection": "#333333"},
                },
            )

            with patch("daybreak.config.config", fake_config), patch(
                "daybreak.core.theme_registry.ThemeRegistry", return_value=fake_registry()
            ), patch("daybreak.core.artifacts.generate_artifacts"), patch(
                "daybreak.terminals.neovim.Neovim"
            ) as neovim_cls, patch(
                "daybreak.cli.runtime.build_orchestrator"
            ) as build_orchestrator:
                build_orchestrator.return_value.get_current_mode.return_value = "dark"
                shell_setup.refresh_generated_artifacts()

            self.assertTrue(neovim_cls.called)
            final = config_file.read_text(encoding="utf-8")
            self.assertEqual(final.count("[integrations]"), 1)
            self.assertIn('neovim_dark_scheme = "onedark"', final)


if __name__ == "__main__":
    unittest.main()
