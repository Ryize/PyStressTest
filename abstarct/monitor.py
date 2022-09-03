from abc import ABC, abstractmethod
from typing import Union, Optional


class AbstractMonitor(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def set_params(self, kill: Optional[bool], timeout: Optional[Union[float, int]], max_thread_count: Optional[int]):
        pass

    @abstractmethod
    def build_graph(self):
        pass

    @abstractmethod
    def stop(self):
        pass
