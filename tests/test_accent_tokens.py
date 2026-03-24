import sys
import unittest
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from daybreak.core.theme_model import ACCENT_KEYS
from daybreak.core.theme_registry import ThemeRegistry
from daybreak.core.theme_transform import palette_to_accent_tokens


class AccentTokenModelTests(unittest.TestCase):
    def test_accent_keys_defined(self):
        expected = {
            "accent_primary",
            "accent_secondary",
            "accent_success",
            "accent_warning",
            "accent_error",
            "accent_selection",
        }
        self.assertEqual(set(ACCENT_KEYS), expected)


class AccentTokenTransformTests(unittest.TestCase):
    _PALETTE = {
        "special": {"background": "#2e3440", "foreground": "#d8dee9", "cursor": "#d8dee9"},
        "colors": {
            "1": "#bf616a", "2": "#a3be8c", "3": "#ebcb8b",
            "4": "#81a1c1", "5": "#b48ead",
        },
    }

    def test_all_accent_keys_present(self):
        accents = palette_to_accent_tokens(self._PALETTE, "dark")
        for key in ACCENT_KEYS:
            self.assertIn(key, accents, f"Missing accent key: {key}")

    def test_accent_values_are_hex_colors(self):
        accents = palette_to_accent_tokens(self._PALETTE, "dark")
        for key, value in accents.items():
            self.assertRegex(value, r"^#[0-9a-f]{6}$", f"Invalid hex for {key}: {value}")

    def test_accent_tokens_light_mode(self):
        light_palette = {
            "special": {"background": "#e5e9f0", "foreground": "#2e3440", "cursor": "#2e3440"},
            "colors": {
                "1": "#bf616a", "2": "#a3be8c", "3": "#ebcb8b",
                "4": "#5e81ac", "5": "#b48ead",
            },
        }
        accents = palette_to_accent_tokens(light_palette, "light")
        for key in ACCENT_KEYS:
            self.assertIn(key, accents)
        self.assertRegex(accents["accent_primary"], r"^#[0-9a-f]{6}$")

    def test_accent_tokens_empty_palette_does_not_crash(self):
        accents = palette_to_accent_tokens({}, "dark")
        for key in ACCENT_KEYS:
            self.assertIn(key, accents)


class AccentTokenRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = ThemeRegistry()

    def test_get_accent_tokens_returns_all_keys(self):
        accents = self.registry.get_accent_tokens("Nord", "dark")
        for key in ACCENT_KEYS:
            self.assertIn(key, accents)

    def test_get_accent_tokens_hex_format(self):
        accents = self.registry.get_accent_tokens("Gruvbox", "light")
        for key, value in accents.items():
            self.assertRegex(value, r"^#[0-9a-f]{6}$")

    def test_get_theme_includes_accent_tokens(self):
        theme = self.registry.get_theme("Nord", "dark")
        self.assertIn("accent_tokens", theme)
        for key in ACCENT_KEYS:
            self.assertIn(key, theme["accent_tokens"])

    def test_accent_tokens_all_themes(self):
        for theme_name in self.registry.list_themes():
            for mode in ("light", "dark"):
                accents = self.registry.get_accent_tokens(theme_name, mode)
                for key in ACCENT_KEYS:
                    self.assertIn(key, accents, f"{theme_name}/{mode} missing {key}")
                    self.assertRegex(
                        accents[key],
                        r"^#[0-9a-f]{6}$",
                        f"{theme_name}/{mode}/{key} not valid hex",
                    )


if __name__ == "__main__":
    unittest.main()
