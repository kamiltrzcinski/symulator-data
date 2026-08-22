import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

SOURCE_PATH = Path(r"C:\Users\tymon\Desktop\posterunki_i_punkty_konstrukcyjne_wszystkie_kategorie.txt")
OUTPUT_PATH = Path(r"C:\Users\tymon\Desktop\SUSRK\symulator-data\data\operating_points\operating_points.json")

def make_uid(domain: int, kind: int, scope: int, instance: int) -> int:
    return (domain << 40) | (kind << 32) | (scope << 16) | instance

def main():
    if not SOURCE_PATH.exists():
        print(f"Error: {SOURCE_PATH} not found!")
        sys.exit(1)

    with open(SOURCE_PATH, "r", encoding="utf-8-sig") as f:
        raw_lines = f.readlines()

    seen = set()
    cleaned_points = []
    duplicates_count = 0

    for line in raw_lines:
        name = line.strip()
        if not name:
            continue
        if name in seen:
            duplicates_count += 1
            continue
        seen.add(name)
        cleaned_points.append(name)

    print(f"Total lines in source: {len(raw_lines)}")
    print(f"Duplicates skipped: {duplicates_count}")
    print(f"Unique operating points: {len(cleaned_points)}")

    # Generate JSON records
    records = []
    for idx, name in enumerate(cleaned_points, start=1):
        uid = make_uid(domain=0x02, kind=0x11, scope=0, instance=idx)
        records.append({
            "uid": uid,
            "name": name
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out:
        json.dump(records, out, indent=2, ensure_ascii=False)

    print(f"Successfully generated {len(records)} operating points in {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
