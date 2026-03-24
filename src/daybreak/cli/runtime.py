import platform

from daybreak.adapters.system import KDESystemAdapter, WindowsSystemAdapter
from daybreak.adapters.terminal import build_linux_terminal_adapters, build_windows_terminal_adapters
from daybreak.core import ThemeOrchestrator


def build_orchestrator() -> ThemeOrchestrator:
    os_name = platform.system()

    if os_name == "Linux":
        return ThemeOrchestrator(
            system_adapter=KDESystemAdapter(),
            terminal_adapters=build_linux_terminal_adapters(),
        )

    if os_name == "Windows":
        return ThemeOrchestrator(
            system_adapter=WindowsSystemAdapter(),
            terminal_adapters=build_windows_terminal_adapters(),
        )

    raise NotImplementedError(f"OS {os_name} not supported yet.")
