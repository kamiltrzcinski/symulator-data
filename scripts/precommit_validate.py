import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

errors: list[str] = []
global_uids: dict[int, str] = {}

def err(file: str, msg: str) -> None:
    errors.append(f"{file}: {msg}")
    print(f"ERROR: {file}: {msg}", file=sys.stderr)

def uid_domain(uid: int) -> int:
    return (uid >> 40) & 0xFF

def uid_kind(uid: int) -> int:
    return (uid >> 32) & 0xFF

def validate_uid(uid: int, field_name: str, rel_path: str) -> bool:
    if not isinstance(uid, int):
        err(rel_path, f"'{field_name}' must be an integer, got {type(uid).__name__}")
        return False
    if uid == 0:
        err(rel_path, f"'{field_name}' cannot be 0")
        return False
    if uid < 0 or uid > 9007199254740991:
        err(rel_path, f"'{field_name}' out of range: {uid} (must be 0 < uid <= 2^53-1)")
        return False
    return True

def register_global(uid: int, rel_path: str) -> None:
    if uid in global_uids and global_uids[uid] != rel_path:
        err(rel_path, f"GLOBAL collision: UID {uid:#x} is already used in {global_uids[uid]}")
    global_uids[uid] = rel_path

def validate_vehicle_types() -> None:
    d = ROOT / "data" / "vehicle_types"
    if not d.exists(): return
    seen: dict[int, str] = {}
    for path in d.rglob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            try: obj = json.load(f)
            except Exception as e:
                err(str(path.relative_to(ROOT)), str(e))
                continue
        rel = str(path.relative_to(ROOT))
        if "uid" in obj and validate_uid(obj["uid"], "uid", rel):
            u = obj["uid"]
            if uid_kind(u) != 0x01: err(rel, "not VEHICLE_TYPE kind")
            if u in seen: err(rel, f"duplicate uid {u:#x}")
            else:
                seen[u] = rel
                register_global(u, rel)

def validate_vehicles() -> dict[int, str]:
    d = ROOT / "data" / "vehicles"
    seen: dict[int, str] = {}
    if not d.exists(): return seen
    for path in d.rglob("vehicle.json"):
        with open(path, "r", encoding="utf-8") as f:
            try: obj = json.load(f)
            except Exception as e:
                err(str(path.relative_to(ROOT)), str(e))
                continue
        rel = str(path.relative_to(ROOT))
        if "uid" in obj and validate_uid(obj["uid"], "uid", rel):
            u = obj["uid"]
            if uid_kind(u) != 0x02: err(rel, "not VEHICLE kind")
            if u in seen: err(rel, f"duplicate uid {u:#x}")
            else:
                seen[u] = rel
                register_global(u, rel)
    return seen

def validate_trains(vehicles: dict[int, str]) -> None:
    d = ROOT / "data" / "trains"
    if not d.exists(): return
    seen: dict[int, str] = {}
    for path in d.rglob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            try: obj = json.load(f)
            except Exception as e:
                err(str(path.relative_to(ROOT)), str(e))
                continue
        rel = str(path.relative_to(ROOT))
        if "uid" in obj and validate_uid(obj["uid"], "uid", rel):
            u = obj["uid"]
            if uid_kind(u) != 0x03: err(rel, "not TRAIN_CONSIST kind")
            if u in seen: err(rel, f"duplicate uid {u:#x}")
            else:
                seen[u] = rel
                register_global(u, rel)

def validate_timetable_points() -> dict[str, int]:
    d = ROOT / "data" / "timetable_points"
    seen_uids: dict[int, str] = {}
    name_to_uid: dict[str, int] = {}
    if not d.exists(): return name_to_uid
    for path in d.rglob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            try: obj = json.load(f)
            except Exception as e:
                err(str(path.relative_to(ROOT)), str(e))
                continue
        rel = str(path.relative_to(ROOT))
        if "uid" not in obj:
            err(rel, "missing 'uid'")
            continue
        uid_val = obj["uid"]
        name = obj.get("name", "").strip()
        if not name: err(rel, "missing or empty 'name'")
        if validate_uid(uid_val, "uid", rel):
            if uid_domain(uid_val) != 0x03: err(rel, "domain not OPERATIONS (0x03)")
            if uid_kind(uid_val) != 0x24: err(rel, "kind not TIMETABLE_POINT (0x24)")
            if uid_val in seen_uids: err(rel, f"duplicate uid {uid_val:#x}")
            else:
                seen_uids[uid_val] = name
                register_global(uid_val, rel)
        if name in name_to_uid: err(rel, f"duplicate name: '{name}'")
        else: name_to_uid[name] = uid_val
    print(f"  Checked {len(seen_uids)} timetable point(s)")
    return name_to_uid

def validate_timetable_connections(points: dict[str, int]) -> None:
    d = ROOT / "data" / "timetable_connections"
    if not d.exists(): return
    valid_uids = set(points.values())
    seen: dict[int, str] = {}
    count = 0
    for path in d.rglob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            try: obj = json.load(f)
            except Exception as e:
                err(str(path.relative_to(ROOT)), str(e))
                continue
        rel = str(path.relative_to(ROOT))
        if "uid" in obj and validate_uid(obj["uid"], "uid", rel):
            u = obj["uid"]
            if uid_domain(u) != 0x03: err(rel, "domain not OPERATIONS")
            if uid_kind(u) != 0x25: err(rel, "kind not TIMETABLE_CONNECTION")
            if u in seen: err(rel, f"duplicate uid {u:#x}")
            else:
                seen[u] = rel
                register_global(u, rel)
        for field in ("from_uid", "to_uid"):
            if field in obj:
                val = obj[field]
                if validate_uid(val, field, rel) and val not in valid_uids:
                    err(rel, f"{field} references unknown point uid {val:#x}")
        count += 1
    print(f"  Checked {count} timetable connection(s)")

def validate_schedules(timetable_points: dict[str, int], vehicles: dict[int, str]) -> None:
    schedule_dirs = [ROOT / "data" / "schedules", ROOT / "schedules"]
    files = []
    for s_dir in schedule_dirs:
        if s_dir.exists(): files.extend(s_dir.rglob("*.json"))
    seen: dict[int, str] = {}
    count = 0
    for path in sorted(set(files)):
        with open(path, "r", encoding="utf-8") as f:
            try: obj = json.load(f)
            except Exception as e:
                err(str(path.relative_to(ROOT)), str(e))
                continue
        rel = str(path.relative_to(ROOT))
        if "uid" in obj and validate_uid(obj["uid"], "uid", rel):
            u = obj["uid"]
            if u in seen: err(rel, f"duplicate uid {u:#x}")
            else:
                seen[u] = rel
                register_global(u, rel)
                
        if "vehicle_uids" in obj and isinstance(obj["vehicle_uids"], list):
            for i, vu in enumerate(obj["vehicle_uids"]):
                if validate_uid(vu, f"vehicle_uids[{i}]", rel):
                    if vu not in vehicles:
                        err(rel, f"vehicle_uids[{i}] {vu:#x} not found in vehicles catalog")
                        
        if "route" in obj and isinstance(obj["route"], list):
            for i, stop in enumerate(obj["route"]):
                if not isinstance(stop, dict): continue
                st_name = stop.get("stationName")
                p_uid = stop.get("point_uid")
                
                if p_uid:
                    if validate_uid(p_uid, f"route[{i}].point_uid", rel):
                        if p_uid not in timetable_points.values():
                            err(rel, f"route[{i}] point_uid {p_uid:#x} not found in catalog")
                elif st_name:
                    if st_name not in timetable_points:
                        err(rel, f"route[{i}] stationName '{st_name}' not found in catalog")
                else:
                    err(rel, f"route[{i}] missing both stationName and point_uid")
        count += 1
    print(f"  Checked {count} schedule file(s)")

def main() -> int:
    print("=== symulator-data UID Validation ===")
    points = validate_timetable_points()
    validate_timetable_connections(points)
    validate_vehicle_types()
    veh = validate_vehicles()
    validate_trains(veh)
    validate_schedules(points, veh)
    print(f"\n-- Global cross-file check: {len(global_uids)} unique UIDs total --")
    if errors:
        print(f"FAILED: {len(errors)} error(s) found.", file=sys.stderr)
        return 1
    print("OK: all UID values valid.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
