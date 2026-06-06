from dataclasses import dataclass
from typing import Optional


@dataclass
class Vehicle:
    uid: int
    pID: str
    displayName: str
    type_uid: Optional[int] = None
    source_file: str = ""
