from daybreak.terminals.config_terminals import Ghostty, WezTerm
from daybreak.terminals.kitty import Kitty
from daybreak.terminals.konsole import Konsole
from daybreak.terminals.neovim import Neovim

from .windows_terminal import WindowsTerminalAdapter
from .wrappers import LegacyModeTerminalAdapter, UniversalPtyAdapter


def build_linux_terminal_adapters():
    return [
        UniversalPtyAdapter(),
        LegacyModeTerminalAdapter(Neovim()),
        LegacyModeTerminalAdapter(Kitty()),
        LegacyModeTerminalAdapter(Ghostty()),
        LegacyModeTerminalAdapter(WezTerm()),
        LegacyModeTerminalAdapter(Konsole()),
    ]


def build_windows_terminal_adapters():
    return [
        WindowsTerminalAdapter(),
    ]
