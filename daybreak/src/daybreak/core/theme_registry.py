from daybreak.themes import THEME_LIBRARY, get_theme_palette
from .theme_model import normalize_mode, validate_tokens
from .theme_transform import palette_to_tokens


class ThemeRegistry:
    def list_themes(self):
        return sorted(THEME_LIBRARY.keys())

    def get_palette(self, theme_name: str, mode: str) -> dict:
        normalized_mode = normalize_mode(mode)
        palette_set = get_theme_palette(theme_name)
        if normalized_mode not in palette_set:
            raise ValueError(f"Theme '{theme_name}' does not provide mode '{normalized_mode}'.")
        return palette_set[normalized_mode]

    def get_tokens(self, theme_name: str, mode: str) -> dict:
        palette = self.get_palette(theme_name, mode)
        tokens = palette_to_tokens(palette, mode)
        validate_tokens(tokens)
        return tokens

    def get_theme(self, theme_name: str, mode: str) -> dict:
        normalized_mode = normalize_mode(mode)
        tokens = self.get_tokens(theme_name, normalized_mode)
        palette = self.get_palette(theme_name, normalized_mode)
        return {
            "id": theme_name.lower().replace(" ", "-"),
            "name": theme_name,
            "mode": normalized_mode,
            "tokens": tokens,
            "palette": palette,
        }
