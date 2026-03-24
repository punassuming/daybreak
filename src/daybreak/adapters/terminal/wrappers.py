from daybreak.terminals.base import Terminal
from daybreak.terminals.universal import UniversalPty


class UniversalPtyAdapter:
    name = "universal_pty"

    def __init__(self):
        self.terminal = UniversalPty()

    def apply_mode(self, mode: str, theme_name: str, palette: dict = None):
        self.terminal.apply_theme(theme_name, mode)


class LegacyModeTerminalAdapter:
    def __init__(self, terminal: Terminal, name: str = None):
        self.terminal = terminal
        self.name = name or terminal.__class__.__name__

    def apply_mode(self, mode: str, theme_name: str, palette: dict = None):
        self.terminal.set_mode(mode)
