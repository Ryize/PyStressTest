from abc import ABC, abstractmethod


class AbstractStressTest(ABC):
    @abstractmethod
    def create_connection(self):
        pass

    @abstractmethod
    def kill_all_connections(self):
        pass

    @abstractmethod
    def auto_create_connection(self):
        pass

    @abstractmethod
    def set_increase_connections(self, func):
        pass

    @abstractmethod
    def stats(self):
        pass

    @abstractmethod
    def auto_get_stats(self):
        pass
