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
                lines_data = obj.get("lines", [])
                dist = 0
                line_no = "999"
                if lines_data:
                    dist = abs(lines_data[0].get("to_meter", 0) - lines_data[0].get("from_meter", 0))
                    line_no = str(lines_data[0].get("line_no", "999"))
                
                if fr not in connections:
                    connections[fr] = []
                connections[fr].append((to, dist, line_no))
                
    cache_data = (points, points_by_name, connections)
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(cache_data, f)
    except Exception:
        CACHE_FILE.unlink(missing_ok=True)
    return cache_data

def load_catalog():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception:
            CACHE_FILE.unlink(missing_ok=True)
    return build_cache()

import heapq

# Explicit classification based on PKP PLK Id-12 (Wykaz linii kolejowych PLK)
# Classification: M = Magistralna (1.0), P = Pierwszorzedna (1.2), D = Drugorzedna (2.5), J = Miejscowa (4.5), L = Lacznik/Manewrowa (10.0)
PLK_MAGISTRALE = {
    "1", "2", "3", "4", "6", "7", "8", "9", "11", "12", "13", "14", "15", "16", "17", "18", "19", 
    "21", "22", "25", "26", "91", "131", "133", "271", "272", "273", "274", "351", "353", "447", "448"
}

PLK_PIERWSZORZEDNE = {
    "20", "23", "24", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "38", "39", "40",
    "41", "42", "43", "44", "45", "61", "93", "106", "137", "138", "139", "143", "144", "145",
    "201", "202", "203", "275", "355", "356", "401", "402", "403"
}

PLK_DRUGORZEDNE = {
    "107", "108", "117", "140", "146", "204", "207", "208", "213", "281", "357", "358", "395"
}

def get_line_multiplier(line_no_str: str, traction: str = None) -> float:
    line_clean = line_no_str.strip()
    
    # 1. Official PLK Id-12 explicit classification
    if line_clean in PLK_MAGISTRALE:
        mult = 1.0
    elif line_clean in PLK_PIERWSZORZEDNE:
        mult = 1.25
    elif line_clean in PLK_DRUGORZEDNE:
        mult = 2.5
    else:
        try:
            num = int(line_clean)
            if 1 <= num <= 450:
                mult = 1.8
            elif 451 <= num <= 699:
                mult = 4.0
            else:
                mult = 12.0 # 700+ lacznice/manewrowe
        except ValueError:
            mult = 8.0

    # Traction modifier: if Electric, apply additional penalty to non-magistral/branch lines
    if traction == "E":
        if line_clean not in PLK_MAGISTRALE and line_clean not in PLK_PIERWSZORZEDNE:
            mult *= 4.0

    return mult

def dijkstra_segment(start_uid, end_uid, connections, excluded_uids, traction=None):
    """Finds optimal path using Dijkstra prioritizing mainlines and avoiding backwoods."""
    if start_uid == end_uid:
        return [start_uid], 0
        
    # (weighted_cost, physical_distance, current_uid, path, last_line_no)
    pq = [(0, 0, start_uid, [start_uid], None)]
    visited = excluded_uids.copy()
    best_dist = {}
    
    while pq:
        cost, dist, current, path, last_line = heapq.heappop(pq)
        
        if current == end_uid:
            return path, dist
            
        if current in visited and current != start_uid:
            continue
        visited.add(current)
            
        for edge_tuple in connections.get(current, []):
            if len(edge_tuple) == 3:
                neighbor, edge_dist, line_no = edge_tuple
            else:
                neighbor, edge_dist = edge_tuple[:2]
                line_no = "999"

            if neighbor not in visited:
                mult = get_line_multiplier(line_no, traction)
                edge_cost = edge_dist * mult
                
                # Penalty for changing lines to avoid zigzagging across switching connections
                if last_line is not None and last_line != line_no:
                    edge_cost += 2000.0  # 2 km virtual penalty for switching lines
                    
                heapq.heappush(pq, (cost + edge_cost, dist + edge_dist, neighbor, path + [neighbor], line_no))
    return None, 0

def resolve_point(name, points_by_name, role="Punkt"):
    key = name.strip().lower()
    if key in points_by_name:
        return points_by_name[key]
    
    print(f"Blad: {role} '{name}' nie zostal znaleziony w katalogu.")
    matches = [orig for k, (_, orig) in points_by_name.items() if key in k][:5]
    if matches:
        print(f"Podpowiedzi: {', '.join(matches)}")
    return None, None

def find_route(start_name, end_name, via_names=None, exclude_names=None, traction=None):
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
    tr_str = f" [trakcja: {traction}]" if traction else ""
    print(f"Szukanie optymalnej trasy PLK: {start_orig} -> {end_orig}{via_str}{ex_str}{tr_str}...", flush=True)

    full_path = []
    total_distance = 0
    for i in range(len(waypoints) - 1):
        seg_start_uid, seg_start_name = waypoints[i]
        seg_end_uid, seg_end_name = waypoints[i + 1]
        
        seg_path, seg_dist = dijkstra_segment(seg_start_uid, seg_end_uid, connections, excluded_uids, traction=traction)
        if not seg_path:
            print(f"\nNie znaleziono polaczenia na odcinku: {seg_start_name} -> {seg_end_name} z uwzglednieniem podanych kryteriow.")
            return
            
        total_distance += seg_dist
        if not full_path:
            full_path.extend(seg_path)
        else:
            full_path.extend(seg_path[1:]) # unikamy dublowania punktu stykowego

    print("\nZnaleziona trasa (z uwzglednieniem priorytetu magistrali PLK):")
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
    print(f"Laczny dystans: {total_distance / 1000.0:.3f} km")

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
    parser.add_argument(
        "--traction", "-t",
        choices=["E", "S"],
        default=None,
        help="Rodzaj trakcji (E - Elektryczna, S - Spalinowa).\nPrzyklad: -t E"
    )
    
    if len(sys.argv) < 3:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    find_route(args.start, args.end, via_names=args.via, exclude_names=args.exclude, traction=args.traction)

if __name__ == "__main__":
    main()
