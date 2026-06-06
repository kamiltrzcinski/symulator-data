import json
from pathlib import Path
from models.vehicle_type import VehicleType
from repositories.base_repository import AbstractRepository


class VehicleTypeRepository(AbstractRepository[VehicleType]):
    def __init__(self, root: Path):
        self._root = root

    def load_all(self) -> list[VehicleType]:
        results = []
        types_dir = self._root / "data" / "vehicle_types"
        if not types_dir.exists():
            return results
        for path in sorted(types_dir.rglob("*.json")):
            try:
                with open(path) as f:
                    obj = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            if "uid" not in obj or "typeName" not in obj:
                continue
            results.append(VehicleType(
                uid=obj["uid"],
                typeName=obj.get("typeName", ""),
                vehicleType=obj.get("vehicleType", ""),
                vehicleSubtype=obj.get("vehicleSubtype", ""),
                lengthM=obj.get("lengthM"),
                massGrossT=obj.get("massGrossT"),
                maxSpeedKmh=obj.get("maxSpeedKmh"),
                source_file=str(path.relative_to(self._root)),
            ))
        return results
