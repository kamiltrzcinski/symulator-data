"""Encode and decode UID values from/to domain/kind/scope/instance parts."""

MAX_SAFE_JSON_INTEGER = (1 << 53) - 1


class UIDCodec:
    @staticmethod
    def encode(domain: int, kind: int, scope: int, instance: int) -> int:
        if not (1 <= domain <= 0xFF):
            raise ValueError(f"DOMAIN out of range: {domain:#x}")
        if not (1 <= kind <= 0xFF):
            raise ValueError(f"KIND out of range: {kind:#x}")
        if not (0 <= scope <= 0xFFFF):
            raise ValueError(f"SCOPE out of range: {scope}")
        if not (1 <= instance <= 0xFFFF):
            raise ValueError(f"INSTANCE out of range (must be 1..65535): {instance}")

        value = (domain << 40) | (kind << 32) | (scope << 16) | instance
        if value > MAX_SAFE_JSON_INTEGER:
            raise OverflowError(f"Encoded UID {value} exceeds 2^53-1")
        return value

    @staticmethod
    def decode(value: int) -> tuple[int, int, int, int]:
        domain = (value >> 40) & 0xFF
        kind = (value >> 32) & 0xFF
        scope = (value >> 16) & 0xFFFF
        instance = value & 0xFFFF
        return domain, kind, scope, instance
