"""Scan JSON files in the repo and build the set of occupied UIDs."""

import json
from pathlib import Path
from uid_codec import UIDCodec


class UIDRegistry:
    def __init__(self, root: Path):
        self._root = root
        self._uids: set[int] = set()

    def scan(self) -> None:
        self._uids.clear()
        for json_path in self._root.rglob("*.json"):
            self._scan_file(json_path)

    def _scan_file(self, path: Path) -> None:
        try:
            with open(path) as f:
                obj = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        if isinstance(obj, dict):
            self._collect_uids_from_dict(obj)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict):
                    self._collect_uids_from_dict(item)

    def _collect_uids_from_dict(self, obj: dict) -> None:
        for key in ("uid", "type_uid"):
            val = obj.get(key)
            if isinstance(val, int) and val > 0:
                self._uids.add(val)
        for val in obj.get("vehicle_uids", []):
            if isinstance(val, int) and val > 0:
                self._uids.add(val)
        carriers = obj.get("carriers")
        if isinstance(carriers, list):
            for c in carriers:
                if isinstance(c, dict):
                    carrier_id = c.get("id")
                    if isinstance(carrier_id, int) and carrier_id > 0:
                        self._uids.add(carrier_id)

    def uids_for_kind(self, kind: int) -> set[int]:
        result = set()
        for uid in self._uids:
            _, k, _, _ = UIDCodec.decode(uid)
            if k == kind:
                result.add(uid)
        return result

    @property
    def all_uids(self) -> set[int]:
        return frozenset(self._uids)
