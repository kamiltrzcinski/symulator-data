from abc import ABC, abstractmethod


class AbstractFormatter(ABC):
    @abstractmethod
    def format(self, uid: int, domain: int, kind: int, scope: int, instance: int) -> str:
        ...
