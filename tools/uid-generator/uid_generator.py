"""Return the next free UID for a given domain/kind/scope."""

from uid_codec import UIDCodec
from uid_registry import UIDRegistry


class UIDGenerator:
    def __init__(self, registry: UIDRegistry):
        self._registry = registry

    def next_uid(self, domain: int, kind: int, scope: int = 0) -> int:
        occupied = self._registry.all_uids
        instance = 1
        while instance <= 0xFFFF:
            candidate = UIDCodec.encode(domain, kind, scope, instance)
            if candidate not in occupied:
                return candidate
            instance += 1
        raise RuntimeError("All INSTANCE values exhausted for domain/kind/scope combination")
