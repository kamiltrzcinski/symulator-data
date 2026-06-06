from formatters.base_formatter import AbstractFormatter


class DecimalFormatter(AbstractFormatter):
    def format(self, uid: int, domain: int, kind: int, scope: int, instance: int) -> str:
        return str(uid)
