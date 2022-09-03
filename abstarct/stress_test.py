from abc import ABC, abstractmethod
from typing import Union, Optional


class AbstractStressTest(ABC):
    @abstractmethod
    def auto_create_connection(self, timeout: Optional[Union[int, float]] = None) -> None:
        pass

    @abstractmethod
    def auto_get_stats(self, timeout: Union[int, float] = 5) -> Union[list, int]:
        pass

    @abstractmethod
    def create_connection(self, connection_type: str = 'GET') -> None:
        pass

    @abstractmethod
    def kill_all_connections(self) -> None:
        pass

    @abstractmethod
    def set_increase_connections(self, func) -> None:
        pass

    @property
    def stats(self) -> dict:
        pass

    @property
    def errors(self) -> dict:
        pass

    @property
    def thread(self) -> dict:
        pass
