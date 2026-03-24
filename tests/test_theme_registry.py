import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.core.theme_registry import ThemeRegistry


class ThemeRegistryTests(unittest.TestCase):
    def test_list_themes_contains_nord(self):
        registry = ThemeRegistry()
        self.assertIn("Nord", registry.list_themes())

    def test_tokens_have_required_semantic_keys(self):
        registry = ThemeRegistry()
        tokens = registry.get_tokens("Nord", "dark")
        for key in (
            "bg",
            "fg",
            "cursor",
            "muted",
            "primary",
            "success",
            "warning",
            "error",
            "info",
            "surface_1",
            "surface_2",
            "surface_3",
        ):
            self.assertIn(key, tokens)
            self.assertRegex(tokens[key], r"^#[0-9a-f]{6}$")


if __name__ == "__main__":
    unittest.main()
