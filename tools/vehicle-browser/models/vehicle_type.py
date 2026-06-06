from dataclasses import dataclass
from typing import Optional


@dataclass
class VehicleType:
    uid: int
    typeName: str
    vehicleType: str
    vehicleSubtype: str
    lengthM: Optional[float] = None
    massGrossT: Optional[float] = None
    maxSpeedKmh: Optional[int] = None
    source_file: str = ""
