import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("daybreak")

class Browser(ABC):
    @abstractmethod
    def set_mode(self, mode: str):
        pass

class SystemThemedBrowser(Browser):
    def __init__(self, name):
        self.name = name

    def set_mode(self, mode: str):
        # Browsers like Chrome/Firefox automatically track the system theme (GTK/Windows).
        # We don't need to do anything specific usually, but we log it for the user.
        logger.debug(f"{self.name}: Relying on system theme change to switch to {mode}.")

class Firefox(SystemThemedBrowser):
    def __init__(self):
        super().__init__("Firefox")

class Chrome(SystemThemedBrowser):
    def __init__(self):
        super().__init__("Google Chrome")
