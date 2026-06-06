from typing import Protocol, TypeVar

T = TypeVar("T", contravariant=True)


class SortStrategy(Protocol[T]):
    @property
    def label(self) -> str: ...
    def key(self, item: T): ...
