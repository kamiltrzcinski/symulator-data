import json
import sys
import pickle
import argparse
from pathlib import Path
from collections import deque

ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "data" / ".topology_cache.pkl"

def build_cache():
    print("Budowanie indeksu bazy (to potrwa tylko za pierwszym razem)...", flush=True)
    points = {}
    points_by_name = {}
    points_dir = ROOT / "data" / "timetable_points"
    if points_dir.exists():
        for p in points_dir.glob("*.json"):
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
                uid = obj["uid"]
                name = obj["name"]
                points[uid] = name
                points_by_name[name.lower()] = (uid, name)
                
    connections = {}
    conn_dir = ROOT / "data" / "timetable_connections"
    if conn_dir.exists():
        for p in conn_dir.glob("*.json"):
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
                fr = obj["from_uid"]
                to = obj["to_uid"]
                if fr not in connections:
                    connections[fr] = []
                connections[fr].append(to)
                
    cache_data = (points, points_by_name, connections)
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(cache_data, f)
    except Exception:
        pass
    return cache_data

def load_catalog():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    return build_cache()

def bfs_segment(start_uid, end_uid, connections, excluded_uids):
    """Finds shortest path between two points avoiding excluded points."""
    if start_uid == end_uid:
        return [start_uid]
        
    queue = deque([(start_uid, [start_uid])])
    visited = {start_uid} | (excluded_uids - {start_uid, end_uid})
    
    while queue:
        current, path = queue.popleft()
        if current == end_uid:
            return path
            
        for neighbor in connections.get(current, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None

def resolve_point(name, points_by_name, role="Punkt"):
    key = name.strip().lower()
    if key in points_by_name:
        return points_by_name[key]
    
    print(f"Blad: {role} '{name}' nie zostal znaleziony w katalogu.")
    matches = [orig for k, (_, orig) in points_by_name.items() if key in k][:5]
    if matches:
        print(f"Podpowiedzi: {', '.join(matches)}")
    return None, None

def find_route(start_name, end_name, via_names=None, exclude_names=None):
    if via_names is None:
        via_names = []
    if exclude_names is None:
        exclude_names = []
        
    points, points_by_name, connections = load_catalog()
    
    if not connections:
        print("Blad: Brak polaczen w bazie.")
        return

    # Rozwiaz punkty
    start_uid, start_orig = resolve_point(start_name, points_by_name, "Punkt poczatkowy")
    if not start_uid:
        return

    end_uid, end_orig = resolve_point(end_name, points_by_name, "Punkt koncowy")
    if not end_uid:
        return

    # Punkty posrednie
    resolved_via = []
    for v_name in via_names:
        v_uid, v_orig = resolve_point(v_name, points_by_name, "Punkt posredni")
        if not v_uid:
            return
        resolved_via.append((v_uid, v_orig))

    # Punkty wykluczone
    excluded_uids = set()
    excluded_names_display = []
    for ex_name in exclude_names:
        ex_uid, ex_orig = resolve_point(ex_name, points_by_name, "Punkt wykluczony")
        if not ex_uid:
            return
        excluded_uids.add(ex_uid)
        excluded_names_display.append(ex_orig)

    # Sprawdz kolizje
    all_targets = [start_uid] + [u for u, _ in resolved_via] + [end_uid]
    for target in all_targets:
        if target in excluded_uids:
            print(f"Blad: Punkt '{points[target]}' nie moze byc jednoczesnie na trasie i wsrod wykluczonych!")
            return

    # Pelna sekwencja kamieni milowych trasy
    waypoints = [(start_uid, start_orig)] + resolved_via + [(end_uid, end_orig)]
    
    via_str = f" przez: {', '.join([o for _, o in resolved_via])}" if resolved_via else ""
    ex_str = f" [wykluczone: {', '.join(excluded_names_display)}]" if excluded_names_display else ""
    print(f"Szukanie trasy: {start_orig} -> {end_orig}{via_str}{ex_str}...", flush=True)

    full_path = []
    for i in range(len(waypoints) - 1):
        seg_start_uid, seg_start_name = waypoints[i]
        seg_end_uid, seg_end_name = waypoints[i + 1]
        
        seg_path = bfs_segment(seg_start_uid, seg_end_uid, connections, excluded_uids)
        if not seg_path:
            print(f"\nNie znaleziono polaczenia na odcinku: {seg_start_name} -> {seg_end_name} z uwzglednieniem podanych kryteriow.")
            return
            
        if not full_path:
            full_path.extend(seg_path)
        else:
            full_path.extend(seg_path[1:]) # unikamy dublowania punktu stykowego

    print("\nZnaleziona trasa:")
    for idx, p in enumerate(full_path):
        tag = ""
        if p == start_uid:
            tag = "  [START]"
        elif p == end_uid:
            tag = "  [CEL]"
        elif any(p == v_uid for v_uid, _ in resolved_via):
            tag = "  [PRZEZ]"
        print(f" {idx+1:3d}. {points.get(p, str(p))}{tag}")
        
    print(f"\nLaczna liczba punktow konstrukcyjnych na trasie: {len(full_path)}")

def main():
    parser = argparse.ArgumentParser(
        description="Wyszukiwarka tras kolejowych w oparciu o topologie SKRJ Kalkulacja.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("start", help="Nazwa punktu poczatkowego (np. \"Kielce Glowne\")")
    parser.add_argument("end", help="Nazwa punktu koncowego (np. \"Krakow Glowny\")")
    parser.add_argument(
        "--via", "-v", 
        nargs="+", 
        default=[], 
        help="Punkty posrednie przez ktore musi przebiegac trasa (kolejnosc ma znaczenie).\nPrzyklad: --via \"Radom Glowny\" \"Deblin\""
    )
    parser.add_argument(
        "--exclude", "-e", 
        nargs="+", 
        default=[], 
        help="Punkty/posterunki wykluczone z wyznaczania trasy (objazdy).\nPrzyklad: --exclude \"Tunel\" \"Miechow\""
    )
    
    if len(sys.argv) < 3:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    find_route(args.start, args.end, via_names=args.via, exclude_names=args.exclude)

if __name__ == "__main__":
    main()
