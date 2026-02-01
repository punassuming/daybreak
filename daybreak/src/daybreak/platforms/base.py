from abc import ABC, abstractmethod

class PlatformHandler(ABC):
    @abstractmethod
    def get_current_mode(self) -> str:
        """Returns 'light' or 'dark'"""
        pass

    @abstractmethod
    def set_mode(self, mode: str):
        """Sets the system mode to 'light' or 'dark'"""
        pass
