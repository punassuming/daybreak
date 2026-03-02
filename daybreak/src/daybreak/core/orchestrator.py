import logging

from daybreak.config import config
from .theme_model import normalize_mode
from .theme_registry import ThemeRegistry

logger = logging.getLogger("daybreak")


class ThemeOrchestrator:
    def __init__(self, system_adapter=None, terminal_adapters=None, registry=None):
        self.system_adapter = system_adapter
        self.terminal_adapters = terminal_adapters or []
        self.registry = registry or ThemeRegistry()

    def get_current_mode(self) -> str:
        if not self.system_adapter:
            return "light"
        try:
            return normalize_mode(self.system_adapter.get_current_mode())
        except Exception as exc:
            logger.warning(f"Failed to detect current mode. Defaulting to light: {exc}")
            return "light"

    def apply(self, mode: str, theme_name: str = None) -> str:
        normalized_mode = normalize_mode(mode)
        resolved_theme = theme_name or config.get_mode_theme_name(normalized_mode)
        palette = self.registry.get_palette(resolved_theme, normalized_mode)

        if self.system_adapter:
            self.system_adapter.set_mode(normalized_mode)

        for adapter in self.terminal_adapters:
            try:
                adapter.apply_mode(normalized_mode, resolved_theme, palette)
            except Exception as exc:
                name = getattr(adapter, "name", adapter.__class__.__name__)
                logger.warning(f"Terminal adapter '{name}' failed: {exc}")

        return resolved_theme

    def apply_toggle(self, explicit_theme_name: str = None):
        target_mode = "light" if self.get_current_mode() == "dark" else "dark"
        theme_name = self.apply(target_mode, explicit_theme_name)
        return target_mode, theme_name
