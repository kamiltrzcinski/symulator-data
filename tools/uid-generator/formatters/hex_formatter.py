from formatters.base_formatter import AbstractFormatter


class HexFormatter(AbstractFormatter):
    def format(self, uid: int, domain: int, kind: int, scope: int, instance: int) -> str:
        return (
            f"0x{domain:04X}_{kind:04X}_{scope:04X}_{instance:04X}"
            f"  (domain={domain:#04x}, kind={kind:#04x}, scope={scope}, instance={instance})"
        )
