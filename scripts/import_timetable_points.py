import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "timetable_points"
REGISTRY_FILE = ROOT / "data" / "timetable_points_registry.json"

DOMAIN_OPERATIONS = 0x03
KIND_TIMETABLE_POINT = 0x24

def make_uid(domain: int, kind: int, scope: int, instance: int) -> int:
    return (domain << 40) | (kind << 32) | (scope << 16) | instance

def sanitize_filename(name: str) -> str:
    keepchars = (' ', '.', '_', '-')
    s = "".join(c for c in name if c.isalnum() or c in keepchars).strip()
    return s.replace(" ", "_")

def main():
    source_path = Path(r"C:\Users\tymon\Desktop\posterunki_i_punkty_konstrukcyjne_wszystkie_kategorie.txt")
    if not source_path.exists():
        print(f"File not found: {source_path}", file=sys.stderr)
        return 1

    with open(source_path, "r", encoding="utf-8-sig") as f:
        lines = [line.strip() for line in f if line.strip()]

    unique_names = list(dict.fromkeys(lines))
    
    registry = {}
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            registry = json.load(f)
            
    next_instance = max(registry.values(), default=0) + 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # clear existing files
    for old_file in DATA_DIR.glob("*.json"):
        old_file.unlink()

    created_count = 0
    for name in unique_names:
        if name not in registry:
            registry[name] = next_instance
            next_instance += 1
            
        instance = registry[name]
        uid = make_uid(DOMAIN_OPERATIONS, KIND_TIMETABLE_POINT, 0, instance)
        
        filename = sanitize_filename(name)
        if not filename:
            filename = f"point_{instance}"
            
        out_path = DATA_DIR / f"{filename}_{instance}.json"
        
        record = {
            "uid": uid,
            "type": "TIMETABLE_POINT",
            "name": name,
            "point_type": "OTHER"
        }
        
        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(record, out_f, indent=2, ensure_ascii=False)
            
        created_count += 1

    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully generated {created_count} timetable points.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
