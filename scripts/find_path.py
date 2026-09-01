import json
import sys
from pathlib import Path
from collections import deque

ROOT = Path(__file__).resolve().parent.parent

def load_catalog():
    points = {}
    points_by_name = {}
    points_dir = ROOT / "data" / "timetable_points"
    if points_dir.exists():
        for p in points_dir.rglob("*.json"):
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
                uid = obj["uid"]
                name = obj["name"]
                points[uid] = name
                points_by_name[name] = uid
                
    connections = {}
    conn_dir = ROOT / "data" / "timetable_connections"
    if conn_dir.exists():
        for p in conn_dir.rglob("*.json"):
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
                fr = obj["from_uid"]
                to = obj["to_uid"]
                if fr not in connections:
                    connections[fr] = []
                connections[fr].append(to)
                
    return points, points_by_name, connections

def find_path(start_name, end_name):
    points, points_by_name, connections = load_catalog()
    
    if start_name not in points_by_name:
        print(f"Error: Start point '{start_name}' not found in catalog.")
        return
    if end_name not in points_by_name:
        print(f"Error: End point '{end_name}' not found in catalog.")
        return
        
    start_uid = points_by_name[start_name]
    end_uid = points_by_name[end_name]
    
    if not connections:
        print("Error: No timetable connections exist in the database. Topology is empty.")
        return
        
    queue = deque([(start_uid, [start_uid])])
    visited = {start_uid}
    
    while queue:
        current, path = queue.popleft()
        if current == end_uid:
            print("Path found:")
            for p in path:
                print(f" -> {points[p]}")
            return
            
        for neighbor in connections.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
                
    print(f"No path found between '{start_name}' and '{end_name}'.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python find_path.py <Start Point> <End Point>")
        sys.exit(1)
    find_path(sys.argv[1], sys.argv[2])
