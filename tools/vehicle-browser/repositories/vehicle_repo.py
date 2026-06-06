import json
from pathlib import Path
from models.vehicle import Vehicle
from repositories.base_repository import AbstractRepository


class VehicleRepository(AbstractRepository[Vehicle]):
    def __init__(self, root: Path):
        self._root = root

    def load_all(self) -> list[Vehicle]:
        results = []
        vehicles_dir = self._root / "data" / "vehicles"
        if not vehicles_dir.exists():
            return results
        for path in sorted(vehicles_dir.rglob("vehicle.json")):
            try:
                with open(path) as f:
                    obj = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            if "uid" not in obj:
                continue
            results.append(Vehicle(
                uid=obj["uid"],
                pID=obj.get("pID", ""),
                displayName=obj.get("displayName", ""),
                type_uid=obj.get("type_uid"),
                source_file=str(path.relative_to(self._root)),
            ))
        return results
