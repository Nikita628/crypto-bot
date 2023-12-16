from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    @abstractmethod
    def search_entry(self):
        pass

    @abstractmethod
    def search_exit(self):
        pass

    @abstractmethod
    def is_long_entry(self):
        pass

    @abstractmethod
    def is_long_exit(self):
        pass

    @abstractmethod
    def is_short_entry(self):
        pass

    @abstractmethod
    def is_short_exit(self):
        pass
