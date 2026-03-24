from .base import PlatformHandler
from daybreak.adapters.system import KDESystemAdapter
from daybreak.adapters.terminal import build_linux_terminal_adapters
from daybreak.core import ThemeOrchestrator


class KDELinuxHandler(PlatformHandler):
    def __init__(self):
        self.orchestrator = ThemeOrchestrator(
            system_adapter=KDESystemAdapter(),
            terminal_adapters=build_linux_terminal_adapters(),
        )

    def get_current_mode(self) -> str:
        return self.orchestrator.get_current_mode()

    def set_mode(self, mode: str):
        self.orchestrator.apply(mode)
