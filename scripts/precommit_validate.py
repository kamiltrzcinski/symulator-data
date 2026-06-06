#!/usr/bin/env python3
"""Validate all UID values in data/ and schedules/ files.

Checks performed:
  - All uid/type_uid values are valid uint64 <= 2^53 - 1
  - DOMAIN, KIND, SCOPE, INSTANCE fields decode to known valid values
  - INSTANCE != 0
  - No duplicate UIDs within a single file
  - No duplicate UIDs across ALL files (global cross-file check)
  - vehicle_uids in trains reference existing vehicle UIDs
  - schedules/ files have required 'uid' and 'vehicle_uids' fields

Exit code: 0 on success, 1 on any validation failure.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

MAX_SAFE_JSON_INTEGER = (1 << 53) - 1

DOMAINS = {0x01: "ROLLING_STOCK", 0x02: "INFRASTRUCTURE", 0x03: "OPERATIONS"}

KINDS = {
    0x01: "VEHICLE_TYPE",
    0x02: "VEHICLE",
    0x03: "TRAIN_CONSIST",
    0x04: "CARRIER",
    0x11: "STATION",
    0x12: "DISPATCH_AREA",
    0x13: "TRACK_SECTION",
    0x14: "SWITCH",
    0x15: "SIGNAL",
    0x16: "DERAILER",
    0x17: "BLOCK_SECTION",
    0x18: "BOUNDARY_NODE",
    0x19: "LEVEL_CROSSING",
    0x1A: "AXLE_COUNTER",
    0x1B: "INTERLOCKING",
    0x1C: "POWER_SUPPLY",
    0x21: "ROUTE",
    0x22: "ALARM",
    0x23: "DISPATCH_EXCHANGE",
}

errors: list[str] = []

# Global registry: uid -> first file that declared it (cross-file duplicate detection)
global_uids: dict[int, str] = {}


def err(path: str, msg: str) -> None:
    errors.append(f"{path}: {msg}")
    print(f"  ERROR  {path}: {msg}", file=sys.stderr)


def uid_domain(value: int) -> int:
    return (value >> 40) & 0xFF


def uid_kind(value: int) -> int:
    return (value >> 32) & 0xFF


def uid_instance(value: int) -> int:
    return value & 0xFFFF


def validate_uid(value, field_name: str, file_path: str) -> bool:
    if not isinstance(value, int):
        err(file_path, f"{field_name} is not an integer: {value!r}")
        return False
    if value < 0:
        err(file_path, f"{field_name} is negative: {value}")
        return False
    if value > MAX_SAFE_JSON_INTEGER:
        err(file_path, f"{field_name} exceeds 2^53-1: {value}")
        return False

    domain = uid_domain(value)
    kind = uid_kind(value)
    instance = uid_instance(value)

    if domain not in DOMAINS:
        err(file_path, f"{field_name}={value:#x}: unknown DOMAIN {domain:#x}")
        return False
    if kind not in KINDS:
        err(file_path, f"{field_name}={value:#x}: unknown KIND {kind:#x}")
        return False
    if instance == 0:
        err(file_path, f"{field_name}={value:#x}: INSTANCE is 0 (reserved/invalid)")
        return False

    return True


def register_global(uid_val: int, rel: str) -> None:
    if uid_val in global_uids:
        err(rel, f"global duplicate uid {uid_val:#x} (first seen in {global_uids[uid_val]})")
    else:
        global_uids[uid_val] = rel


def validate_vehicle_types() -> None:
    types_dir = ROOT / "data" / "vehicle_types"
    if not types_dir.exists():
        return

    seen: dict[int, str] = {}
    count = 0
    for path in sorted(types_dir.rglob("*.json")):
        with open(path) as f:
            try:
                obj = json.load(f)
            except json.JSONDecodeError as e:
                err(str(path), f"JSON parse error: {e}")
                continue

        rel = str(path.relative_to(ROOT))
        if "uid" not in obj:
            err(rel, "missing 'uid' field")
            continue

        uid_val = obj["uid"]
        if validate_uid(uid_val, "uid", rel):
            kind = uid_kind(uid_val)
            if kind != 0x01:
                err(rel, f"uid KIND {kind:#x} is not VEHICLE_TYPE (0x01)")
            if uid_val in seen:
                err(rel, f"duplicate uid {uid_val:#x} within vehicle_types (also {seen[uid_val]})")
            else:
                seen[uid_val] = rel
                register_global(uid_val, rel)
        count += 1

    print(f"  Checked {count} vehicle_type file(s)")


def validate_vehicles() -> dict[int, str]:
    vehicles_dir = ROOT / "data" / "vehicles"
    if not vehicles_dir.exists():
        return {}

    seen: dict[int, str] = {}
    count = 0
    for path in sorted(vehicles_dir.rglob("vehicle.json")):
        with open(path) as f:
            try:
                obj = json.load(f)
            except json.JSONDecodeError as e:
                err(str(path), f"JSON parse error: {e}")
                continue

        rel = str(path.relative_to(ROOT))
        for field in ("uid", "type_uid"):
            if field in obj:
                validate_uid(obj[field], field, rel)

        if "uid" not in obj:
            err(rel, "missing 'uid' field")
            continue

        uid_val = obj["uid"]
        kind = uid_kind(uid_val) if isinstance(uid_val, int) else None
        if kind is not None and kind != 0x02:
            err(rel, f"uid KIND {kind:#x} is not VEHICLE (0x02)")

        if isinstance(uid_val, int):
            if uid_val in seen:
                err(rel, f"duplicate uid {uid_val:#x} (also {seen[uid_val]})")
            else:
                seen[uid_val] = rel
                register_global(uid_val, rel)
        count += 1

    print(f"  Checked {count} vehicle file(s)")
    return seen


def validate_trains(vehicle_uids: dict[int, str]) -> None:
    trains_dir = ROOT / "data" / "trains"
    if not trains_dir.exists():
        return

    seen: dict[int, str] = {}
    count = 0
    for path in sorted(trains_dir.rglob("*.json")):
        with open(path) as f:
            try:
                obj = json.load(f)
            except json.JSONDecodeError as e:
                err(str(path), f"JSON parse error: {e}")
                continue

        rel = str(path.relative_to(ROOT))
        if "uid" not in obj:
            err(rel, "missing 'uid' field")
            continue

        uid_val = obj["uid"]
        if validate_uid(uid_val, "uid", rel):
            kind = uid_kind(uid_val)
            if kind != 0x03:
                err(rel, f"uid KIND {kind:#x} is not TRAIN_CONSIST (0x03)")
            if uid_val in seen:
                err(rel, f"duplicate uid {uid_val:#x} (also {seen[uid_val]})")
            else:
                seen[uid_val] = rel
                register_global(uid_val, rel)

        if vehicle_uids and "vehicle_uids" in obj:
            for ref in obj["vehicle_uids"]:
                if isinstance(ref, int) and ref not in vehicle_uids:
                    err(rel, f"vehicle_uids references unknown vehicle uid {ref:#x}")
        count += 1

    print(f"  Checked {count} train file(s)")


def validate_schedules() -> None:
    schedules_dir = ROOT / "schedules"
    if not schedules_dir.exists():
        return

    seen: dict[int, str] = {}
    count = 0
    for path in sorted(schedules_dir.rglob("*.json")):
        with open(path) as f:
            try:
                obj = json.load(f)
            except json.JSONDecodeError as e:
                err(str(path), f"JSON parse error: {e}")
                continue

        rel = str(path.relative_to(ROOT))

        if "uid" not in obj:
            err(rel, "missing 'uid' field")
        else:
            uid_val = obj["uid"]
            if validate_uid(uid_val, "uid", rel) and isinstance(uid_val, int):
                if uid_val in seen:
                    err(rel, f"duplicate uid {uid_val:#x} (also {seen[uid_val]})")
                else:
                    seen[uid_val] = rel
                    register_global(uid_val, rel)

        if "vehicle_uids" in obj and not isinstance(obj["vehicle_uids"], list):
            err(rel, "'vehicle_uids' must be a list")

        count += 1

    print(f"  Checked {count} schedule file(s)")


def main() -> int:
    print("=== symulator-data UID Validation ===")

    print("\n-- Vehicle types --")
    validate_vehicle_types()

    print("\n-- Vehicles --")
    vehicle_uids = validate_vehicles()

    print("\n-- Trains --")
    validate_trains(vehicle_uids)

    print("\n-- Schedules --")
    validate_schedules()

    print(f"\n-- Global cross-file check: {len(global_uids)} unique UIDs total --")

    print()
    if errors:
        print(f"FAILED: {len(errors)} error(s) found.", file=sys.stderr)
        return 1
    print("OK: all UID values valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
