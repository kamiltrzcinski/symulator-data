from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    def load_all(self) -> list[T]:
        ...
