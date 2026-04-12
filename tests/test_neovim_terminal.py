import sys
import tempfile
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.terminals.neovim import Neovim
from daybreak.config import config


class NeovimTerminalTests(unittest.TestCase):
    def test_set_mode_writes_theme_and_watcher_to_config_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            terminal = Neovim(config_dir=config_dir)

            terminal.set_mode("dark")

            theme_file = config_dir / "theme.lua"
            watcher_file = config_dir / "nvim_watcher.lua"
            bootstrap_file = config_dir / "nvim_bootstrap.lua"

            self.assertTrue(theme_file.exists())
            self.assertTrue(watcher_file.exists())
            self.assertTrue(bootstrap_file.exists())

            theme_content = theme_file.read_text(encoding="utf-8")
            self.assertIn('vim.o.background = "dark"', theme_content)
            self.assertIn('vim.g.daybreak_mode = "dark"', theme_content)
            self.assertIn('vim.g.daybreak_target_colorscheme = "', theme_content)
            self.assertIn("pcall(vim.cmd.colorscheme, vim.g.colors_name)", theme_content)
            self.assertIn('pcall(vim.api.nvim_exec_autocmds, "User"', theme_content)

            watcher_content = watcher_file.read_text(encoding="utf-8")
            self.assertIn(f"local theme_file = [=[{theme_file}]=]", watcher_content)
            self.assertIn("vim.g.daybreak_nvim_watcher_loaded", watcher_content)
            self.assertIn("uv.new_fs_event", watcher_content)
            self.assertIn("schedule_reload()", watcher_content)
            self.assertIn('vim.api.nvim_create_user_command("DaybreakReload"', watcher_content)
            self.assertIn("{ force = true }", watcher_content)

            bootstrap_content = bootstrap_file.read_text(encoding="utf-8")
            self.assertIn("Daybreak Neovim Bootstrap", bootstrap_content)
            self.assertIn(f"local theme_file = [=[{theme_file}]=]", bootstrap_content)
            self.assertIn(f"local watcher_file = [=[{watcher_file}]=]", bootstrap_content)
            self.assertIn("function M.load_watcher()", bootstrap_content)
            self.assertIn("function M.apply_target_scheme()", bootstrap_content)
            self.assertIn("function M.toggle_daybreak()", bootstrap_content)
            self.assertIn('pattern = "DaybreakThemeChanged"', bootstrap_content)
            self.assertIn('vim.api.nvim_create_autocmd("ColorScheme"', bootstrap_content)
            self.assertIn("set_neovim_scheme(vim.g.daybreak_mode, vim.g.colors_name)", bootstrap_content)
            self.assertIn('vim.api.nvim_create_user_command("DaybreakToggle", M.toggle_daybreak', bootstrap_content)
            self.assertIn("if vim.system then", bootstrap_content)
            self.assertIn("vim.fn.jobstart(cmd", bootstrap_content)
            self.assertIn("_G.DaybreakNvim = M", bootstrap_content)
            self.assertIn("upsert_integrations(content, key, rhs)", bootstrap_content)
            self.assertNotIn("^%%s*%%[integrations%%]%%s*$", bootstrap_content)
            self.assertNotIn('local key_pattern = "^%%s*"', bootstrap_content)

    def test_set_mode_light_writes_light_background(self):
        with tempfile.TemporaryDirectory() as tmp:
            terminal = Neovim(config_dir=Path(tmp))
            terminal.set_mode("light")

            content = (Path(tmp) / "theme.lua").read_text(encoding="utf-8")
            self.assertIn('vim.o.background = "light"', content)
            self.assertIn('vim.g.daybreak_mode = "light"', content)
            self.assertIn('vim.g.daybreak_target_colorscheme = "', content)

    def test_set_mode_uses_neovim_scheme_from_integrations_config(self):
        original_light = config.get("integrations", "neovim_light_scheme")
        original_dark = config.get("integrations", "neovim_dark_scheme")
        try:
            config.data.setdefault("integrations", {})
            config.data["integrations"]["neovim_light_scheme"] = "catppuccin-latte"
            config.data["integrations"]["neovim_dark_scheme"] = "catppuccin-mocha"

            with tempfile.TemporaryDirectory() as tmp:
                terminal = Neovim(config_dir=Path(tmp))
                terminal.set_mode("dark")
                dark_content = (Path(tmp) / "theme.lua").read_text(encoding="utf-8")
                self.assertIn('vim.g.daybreak_target_colorscheme = "catppuccin-mocha"', dark_content)

                terminal.set_mode("light")
                light_content = (Path(tmp) / "theme.lua").read_text(encoding="utf-8")
                self.assertIn('vim.g.daybreak_target_colorscheme = "catppuccin-latte"', light_content)
        finally:
            config.data.setdefault("integrations", {})
            config.data["integrations"]["neovim_light_scheme"] = original_light
            config.data["integrations"]["neovim_dark_scheme"] = original_dark

    def test_set_mode_does_not_overwrite_existing_static_support_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            watcher_file = config_dir / "nvim_watcher.lua"
            bootstrap_file = config_dir / "nvim_bootstrap.lua"
            watcher_file.write_text("-- watcher sentinel\n", encoding="utf-8")
            bootstrap_file.write_text("-- bootstrap sentinel\n", encoding="utf-8")

            terminal = Neovim(config_dir=config_dir)
            terminal.set_mode("dark")

            self.assertEqual(watcher_file.read_text(encoding="utf-8"), "-- watcher sentinel\n")
            self.assertEqual(bootstrap_file.read_text(encoding="utf-8"), "-- bootstrap sentinel\n")


if __name__ == "__main__":
    unittest.main()
