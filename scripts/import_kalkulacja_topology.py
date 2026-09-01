import json
import os
import sys
from pathlib import Path

ROOT = Path('c:/Users/tymon/Desktop/SUSRK/symulator-data')

DOMAIN_OPERATIONS = 0x03
KIND_TIMETABLE_CONNECTION = 0x25

def make_uid(domain, kind, scope, instance):
    return (domain << 40) | (kind << 32) | (scope << 16) | instance

def main():
    print("Loading kalkulacja dictionaries...")
    with open('c:/Users/tymon/Desktop/kalkulacja_dictionaries.json', 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
        
    kalkulacja_objs = {obj['id']: obj['name'] for obj in data.get('railwayObjects', [])}
    
    # line_id -> line_no
    line_numbers = {obj['id']: obj.get('lineNo', str(obj['id'])) for obj in data.get('railwayLines', [])}
    
    print("Loading internal timetable points...")
    points_dir = ROOT / "data" / "timetable_points"
    internal_points = {} # name.lower() -> dict
    if points_dir.exists():
        for p in points_dir.glob("*.json"):
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
                internal_points[obj["name"].lower()] = {"uid": obj["uid"], "path": p, "data": obj}
    
    lines_dict = {}
    for obj in data.get('railwayObjectsOnRailwayLines', []):
        line_id = obj.get('railwayLineId')
        if line_id not in lines_dict:
            lines_dict[line_id] = []
        lines_dict[line_id].append(obj)
        
    connections = {}
    point_locations = {} # uid -> list of {line_no, meter}
    
    for line_id, objs in lines_dict.items():
        objs.sort(key=lambda x: x.get('axisMeter', 0))
        
        last_uid = None
        last_meter = None
        line_no = str(line_numbers.get(line_id, line_id))
        
        for o in objs:
            kalk_name = kalkulacja_objs.get(o.get('railwayObjectId'))
            if not kalk_name: continue
            
            pinfo = internal_points.get(kalk_name.lower())
            if not pinfo: continue
            uid = pinfo["uid"]
            meter = o.get('axisMeter', 0)
            
            # Save point location
            if uid not in point_locations:
                point_locations[uid] = []
            point_locations[uid].append({"line_no": line_no, "meter": meter})
            
            if last_uid and last_uid != uid:
                # Add bi-directional connection
                # Forward
                edge1 = (last_uid, uid)
                if edge1 not in connections: connections[edge1] = []
                connections[edge1].append({
                    "line_no": line_no,
                    "from_meter": last_meter,
                    "to_meter": meter
                })
                # Backward
                edge2 = (uid, last_uid)
                if edge2 not in connections: connections[edge2] = []
                connections[edge2].append({
                    "line_no": line_no,
                    "from_meter": meter,
                    "to_meter": last_meter
                })
                
            last_uid = uid
            last_meter = meter

    print("Updating points with kilometer data...")
    updated_points = 0
    for uid, locs in point_locations.items():
        # find point file
        # this is slow to search, but we have path in internal_points
        # find pinfo
        for pinfo in internal_points.values():
            if pinfo["uid"] == uid:
                pinfo["data"]["line_locations"] = locs
                with open(pinfo["path"], "w", encoding="utf-8") as f:
                    json.dump(pinfo["data"], f, indent=2)
                updated_points += 1
                break
                
    print(f"Updated {updated_points} points.")
    
    conn_dir = ROOT / "data" / "timetable_connections"
    conn_dir.mkdir(parents=True, exist_ok=True)
    for p in conn_dir.glob("*.json"): p.unlink()
    
    print("Saving connection JSONs...")
    for i, (edge, lines_info) in enumerate(connections.items()):
        f_uid, t_uid = edge
        instance = i + 1
        c_uid = make_uid(DOMAIN_OPERATIONS, KIND_TIMETABLE_CONNECTION, 0, instance)
        obj = {
            "uid": c_uid,
            "type": "TIMETABLE_CONNECTION",
            "from_uid": f_uid,
            "to_uid": t_uid,
            "lines": lines_info
        }
        with open(conn_dir / f"connection_{instance}.json", "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2)
            
    print("Done! Topology constructed with kilometers.")

if __name__ == "__main__":
    main()
