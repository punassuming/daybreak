from abc import ABC, abstractmethod

class Terminal(ABC):
    @abstractmethod
    def set_mode(self, mode: str):
        pass
