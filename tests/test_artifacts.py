import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.core.artifacts import generate_artifacts


_TOKENS = {
    "bg": "#2e3440",
    "fg": "#d8dee9",
    "cursor": "#d8dee9",
    "muted": "#4c566a",
    "primary": "#81a1c1",
    "success": "#a3be8c",
    "warning": "#ebcb8b",
    "error": "#bf616a",
    "info": "#88c0d0",
    "surface_1": "#3b4252",
    "surface_2": "#434c5e",
    "surface_3": "#4c566a",
}

_ACCENT_TOKENS = {
    "accent_primary": "#81a1c1",
    "accent_secondary": "#b48ead",
    "accent_success": "#a3be8c",
    "accent_warning": "#ebcb8b",
    "accent_error": "#bf616a",
    "accent_selection": "#3b4252",
}

_PALETTE = {
    "special": {"background": "#2e3440", "foreground": "#d8dee9", "cursor": "#d8dee9"},
    "colors": {
        "0": "#3b4252", "1": "#bf616a", "2": "#a3be8c", "3": "#ebcb8b",
        "4": "#81a1c1", "5": "#b48ead", "6": "#88c0d0", "7": "#e5e9f0",
    },
}


class ArtifactGenerationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.config_dir = Path(self._tmp)

    def _run(self, theme="Nord", mode="dark"):
        generate_artifacts(self.config_dir, theme, mode, _TOKENS, _ACCENT_TOKENS, _PALETTE)

    def test_palette_json_created(self):
        self._run()
        self.assertTrue((self.config_dir / "palette.json").exists())

    def test_palette_json_content(self):
        self._run(theme="Nord", mode="dark")
        data = json.loads((self.config_dir / "palette.json").read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "Nord")
        self.assertEqual(data["mode"], "dark")
        self.assertIn("tokens", data)
        self.assertIn("accent_tokens", data)
        self.assertIn("palette", data)
        self.assertIn("bg", data["tokens"])
        self.assertIn("accent_primary", data["accent_tokens"])

    def test_env_sh_created(self):
        self._run()
        self.assertTrue((self.config_dir / "env.sh").exists())

    def test_env_sh_content(self):
        self._run(theme="Gruvbox", mode="light")
        content = (self.config_dir / "env.sh").read_text(encoding="utf-8")
        self.assertIn('DAYBREAK_THEME="Gruvbox"', content)
        self.assertIn('DAYBREAK_MODE="light"', content)
        self.assertIn("DAYBREAK_ACCENT_PRIMARY", content)
        self.assertIn("DAYBREAK_ACCENT_SELECTION", content)
        self.assertIn("export DAYBREAK_THEME", content)

    def test_ls_colors_sh_created(self):
        self._run()
        self.assertTrue((self.config_dir / "ls_colors.sh").exists())

    def test_ls_colors_sh_content(self):
        self._run()
        content = (self.config_dir / "ls_colors.sh").read_text(encoding="utf-8")
        self.assertIn("LS_COLORS=", content)
        self.assertIn("export LS_COLORS", content)
        # Directories should be included
        self.assertIn("di=", content)
        # Executables should be included
        self.assertIn("ex=", content)

    def test_artifacts_fail_safely_on_write_error(self):
        read_only = self.config_dir / "readonly_dir"
        read_only.mkdir()
        read_only.chmod(0o444)
        # Should not raise — failures are swallowed with a warning
        try:
            generate_artifacts(read_only / "sub", "Nord", "dark", _TOKENS, _ACCENT_TOKENS, _PALETTE)
        except Exception as exc:
            self.fail(f"generate_artifacts raised unexpectedly: {exc}")
        finally:
            read_only.chmod(0o755)

    def test_artifacts_overwrite_on_subsequent_call(self):
        self._run(theme="Nord", mode="dark")
        self._run(theme="Gruvbox", mode="light")
        data = json.loads((self.config_dir / "palette.json").read_text(encoding="utf-8"))
        self.assertEqual(data["theme"], "Gruvbox")
        self.assertEqual(data["mode"], "light")


class OrchestratorArtifactIntegrationTests(unittest.TestCase):
    """Smoke test: orchestrator.apply() generates artifacts."""

    def test_apply_writes_palette_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp)
            with patch("daybreak.core.orchestrator.config") as mock_cfg:
                mock_cfg.get_mode_theme_name.return_value = "Nord"
                mock_cfg.config_dir = config_dir

                from daybreak.core.orchestrator import ThemeOrchestrator

                orch = ThemeOrchestrator(system_adapter=None, terminal_adapters=[])
                orch.apply("dark")

            self.assertTrue((config_dir / "palette.json").exists())
            data = json.loads((config_dir / "palette.json").read_text(encoding="utf-8"))
            self.assertEqual(data["theme"], "Nord")


if __name__ == "__main__":
    unittest.main()
