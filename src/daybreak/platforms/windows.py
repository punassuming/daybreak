from .base import PlatformHandler
from daybreak.adapters.system import WindowsSystemAdapter
from daybreak.core import ThemeOrchestrator


class WindowsHandler(PlatformHandler):
    def __init__(self):
        self.orchestrator = ThemeOrchestrator(
            system_adapter=WindowsSystemAdapter(),
            terminal_adapters=[],
        )

    def get_current_mode(self) -> str:
        return self.orchestrator.get_current_mode()

    def set_mode(self, mode: str):
        self.orchestrator.apply(mode)
