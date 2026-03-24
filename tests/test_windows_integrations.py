import json
import os
import sys
import uuid
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.adapters.terminal.obsidian import ObsidianAdapter
from daybreak.adapters.terminal.windows_terminal import WindowsTerminalAdapter
from daybreak.config import config


class WindowsIntegrationAdapterTests(unittest.TestCase):
    def setUp(self):
        self.test_root = Path.cwd() / f".test-win-int-{uuid.uuid4().hex}"
        self.test_root.mkdir(parents=True, exist_ok=True)
        self.addCleanup(self._cleanup)

        self.old_localappdata = os.environ.get("LOCALAPPDATA")
        self.old_appdata = os.environ.get("APPDATA")

        os.environ["LOCALAPPDATA"] = str(self.test_root / "local")
        os.environ["APPDATA"] = str(self.test_root / "roaming")

        config.data.setdefault("integrations", {})
        config.data["integrations"]["windows_terminal_light_scheme"] = "One Half Light"
        config.data["integrations"]["windows_terminal_dark_scheme"] = "One Half Dark"
        config.data["integrations"]["obsidian_light_theme"] = "moonstone"
        config.data["integrations"]["obsidian_dark_theme"] = "obsidian"

    def tearDown(self):
        if self.old_localappdata is None:
            os.environ.pop("LOCALAPPDATA", None)
        else:
            os.environ["LOCALAPPDATA"] = self.old_localappdata

        if self.old_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = self.old_appdata

    def _cleanup(self):
        if not self.test_root.exists():
            return
        for path in sorted(self.test_root.rglob("*"), reverse=True):
            try:
                if path.is_file():
                    path.unlink()
                else:
                    path.rmdir()
            except OSError:
                pass
        try:
            self.test_root.rmdir()
        except OSError:
            pass

    def test_windows_terminal_adapter_updates_defaults_and_existing_profile_overrides(self):
        settings_path = (
            Path(os.environ["LOCALAPPDATA"])
            / "Packages"
            / "Microsoft.WindowsTerminalPreview_Test"
            / "LocalState"
            / "settings.json"
        )
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            "\n".join(
                [
                    "{",
                    '  // comment',
                    '  "profiles": {',
                    '    "defaults": {},',
                    '    "list": [',
                    '      { "name": "PowerShell", "colorScheme": "One Half Dark", },',
                    '      { "name": "Command Prompt" }',
                    "    ],",
                    "  },",
                    "}",
                ]
            ),
            encoding="utf-8",
        )

        WindowsTerminalAdapter().apply_mode("light", "Nord")

        result = json.loads(settings_path.read_text(encoding="utf-8"))
        self.assertEqual(result["profiles"]["defaults"]["colorScheme"], "One Half Light")
        self.assertEqual(result["profiles"]["list"][0]["colorScheme"], "One Half Light")
        self.assertNotIn("colorScheme", result["profiles"]["list"][1])

    def test_obsidian_adapter_updates_global_and_vault_theme(self):
        vault_path = self.test_root / "vault-a"
        (vault_path / ".obsidian").mkdir(parents=True, exist_ok=True)
        app_json = vault_path / ".obsidian" / "app.json"
        app_json.write_text('{"theme":"obsidian"}', encoding="utf-8")

        global_path = Path(os.environ["APPDATA"]) / "obsidian" / "obsidian.json"
        global_path.parent.mkdir(parents=True, exist_ok=True)
        global_path.write_text(
            json.dumps(
                {
                    "theme": "obsidian",
                    "vaults": {"one": {"path": str(vault_path)}},
                }
            ),
            encoding="utf-8",
        )

        ObsidianAdapter().apply_mode("light", "Nord")

        global_result = json.loads(global_path.read_text(encoding="utf-8"))
        vault_result = json.loads(app_json.read_text(encoding="utf-8"))
        self.assertEqual(global_result["theme"], "moonstone")
        self.assertEqual(vault_result["theme"], "moonstone")

if __name__ == "__main__":
    unittest.main()
