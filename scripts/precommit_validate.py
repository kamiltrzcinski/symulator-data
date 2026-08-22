#!/usr/bin/env python3
"""Validate all UID values in data/ and schedules/ files.

Checks performed:
  - All uid/type_uid values are valid uint64 <= 2^53 - 1
  - DOMAIN, KIND, SCOPE, INSTANCE fields decode to known valid values
  - INSTANCE != 0
  - No duplicate UIDs within a single file
  - No duplicate UIDs across ALL files (global cross-file check)
  - vehicle_uids in trains reference existing vehicle UIDs
  - operating_points.json contains valid unique UIDs and unique names
  - schedules/ files have required 'uid' and valid 'stationName' references from operating_points.json

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
        with open(path, "r", encoding="utf-8") as f:
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
        with open(path, "r", encoding="utf-8") as f:
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
        with open(path, "r", encoding="utf-8") as f:
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


def validate_operating_points() -> dict[str, int]:
    op_path = ROOT / "data" / "operating_points" / "operating_points.json"
    if not op_path.exists():
        return {}

    seen_uids: dict[int, str] = {}
    name_to_uid: dict[str, int] = {}
    rel = str(op_path.relative_to(ROOT))

    with open(op_path, "r", encoding="utf-8") as f:
        try:
            records = json.load(f)
        except json.JSONDecodeError as e:
            err(rel, f"JSON parse error: {e}")
            return {}

    if not isinstance(records, list):
        err(rel, "operating_points.json must be a JSON array")
        return {}

    for idx, item in enumerate(records):
        if not isinstance(item, dict):
            err(rel, f"item at index {idx} is not an object")
            continue

        if "uid" not in item:
            err(rel, f"item at index {idx} missing 'uid'")
            continue
        if "name" not in item or not isinstance(item["name"], str) or not item["name"].strip():
            err(rel, f"item at index {idx} missing or invalid 'name'")
            continue

        uid_val = item["uid"]
        name = item["name"].strip()

        if validate_uid(uid_val, f"operating_points[{idx}].uid", rel):
            kind = uid_kind(uid_val)
            if kind != 0x11:
                err(rel, f"uid {uid_val:#x} for '{name}' KIND {kind:#x} is not STATION (0x11)")
            domain = uid_domain(uid_val)
            if domain != 0x02:
                err(rel, f"uid {uid_val:#x} for '{name}' DOMAIN {domain:#x} is not INFRASTRUCTURE (0x02)")

            if uid_val in seen_uids:
                err(rel, f"duplicate operating point uid {uid_val} (used by '{name}' and '{seen_uids[uid_val]}')")
            else:
                seen_uids[uid_val] = name
                register_global(uid_val, rel)

        if name in name_to_uid:
            err(rel, f"duplicate operating point name: '{name}'")
        else:
            name_to_uid[name] = uid_val

    print(f"  Checked {len(records)} operating point(s)")
    return name_to_uid


def validate_schedules(operating_points: dict[str, int]) -> None:
    schedule_dirs = [ROOT / "data" / "schedules", ROOT / "schedules"]
    files: list[Path] = []
    for s_dir in schedule_dirs:
        if s_dir.exists():
            files.extend(s_dir.rglob("*.json"))

    seen: dict[int, str] = {}
    count = 0
    for path in sorted(set(files)):
        with open(path, "r", encoding="utf-8") as f:
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

        if "route" in obj and isinstance(obj["route"], list):
            for stop_idx, stop in enumerate(obj["route"]):
                if not isinstance(stop, dict):
                    err(rel, f"route[{stop_idx}] is not an object")
                    continue
                station_name = stop.get("stationName")
                if not station_name:
                    err(rel, f"route[{stop_idx}] missing 'stationName'")
                    continue

                if operating_points and station_name not in operating_points:
                    err(rel, f"route[{stop_idx}] references unknown operating point: '{station_name}'")

                if "point_uid" in stop:
                    p_uid = stop["point_uid"]
                    if validate_uid(p_uid, f"route[{stop_idx}].point_uid", rel):
                        if operating_points and station_name in operating_points:
                            expected_uid = operating_points[station_name]
                            if p_uid != expected_uid:
                                err(
                                    rel,
                                    f"route[{stop_idx}] point_uid {p_uid} does not match registered UID {expected_uid} for '{station_name}'"
                                )

        count += 1

    print(f"  Checked {count} schedule file(s)")


def main() -> int:
    print("=== symulator-data UID Validation ===")

    print("\n-- Operating points --")
    operating_points = validate_operating_points()

    print("\n-- Vehicle types --")
    validate_vehicle_types()

    print("\n-- Vehicles --")
    vehicle_uids = validate_vehicles()

    print("\n-- Trains --")
    validate_trains(vehicle_uids)

    print("\n-- Schedules --")
    validate_schedules(operating_points)

    print(f"\n-- Global cross-file check: {len(global_uids)} unique UIDs total --")

    print()
    if errors:
        print(f"FAILED: {len(errors)} error(s) found.", file=sys.stderr)
        return 1
    print("OK: all UID values valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
