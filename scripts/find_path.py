import json
import pickle
import heapq
import sys
import argparse
from pathlib import Path
from abc import ABC, abstractmethod

ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "data" / ".topology_cache.pkl"

class CostStrategy(ABC):
    @abstractmethod
    def get_cost(self, edge_dist_m: float, vmax: float, line_no: str, klasa: str, last_line_no: str) -> float:
        """Calculates edge weight (e.g. time cost). Returns float('inf') if edge is forbidden."""
        pass

class BaseTractionStrategy(CostStrategy):
    def get_cost(self, edge_dist_m: float, vmax: float, line_no: str, klasa: str, last_line_no: str) -> float:
        # Distance in km, guard against zero/negative distances
        dist_km = max(edge_dist_m, 100) / 1000.0
        
        # Effective vmax, guard against division by zero
        vmax_eff = max(vmax, 10.0) 
        
        # Base time cost in minutes
        time_cost = (dist_km / vmax_eff) * 60.0
        
        # Penalty for changing lines to avoid zigzagging across junctions
        if last_line_no is not None and last_line_no != line_no:
            time_cost += 5.0
            
        return time_cost

class ElectricTractionStrategy(BaseTractionStrategy):
    def get_cost(self, edge_dist_m: float, vmax: float, line_no: str, klasa: str, last_line_no: str) -> float:
        base_cost = super().get_cost(edge_dist_m, vmax, line_no, klasa, last_line_no)
        
        # If line appears to be a low-speed local line without wire, strictly forbid entry
        if vmax < 60.0 and klasa not in ["C3", "C4", "D3", "D4"]:
            return float('inf')
            
        return base_cost

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
                vmax = 40.0
                klasa = ""
                
                if lines_data:
                    from_meter = lines_data[0].get("from_meter", 0)
                    to_meter = lines_data[0].get("to_meter", 0)
                    dist = abs(to_meter - from_meter)
                    line_no = str(lines_data[0].get("line_no", "999"))
                    vmax = float(lines_data[0].get("vmax", 40.0))
                    klasa = lines_data[0].get("class", "")
                
                if fr not in connections:
                    connections[fr] = []
                connections[fr].append((to, dist, line_no, vmax, klasa))
                
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
            pass
    return build_cache()

def dijkstra_segment(start_uid, end_uid, connections, excluded_uids, cost_strategy: CostStrategy):
    """Wyszukuje optymalna trase uzywajac wstrzyknietej strategii kosztowej (Dependency Injection)."""
    if start_uid == end_uid:
        return [start_uid], 0
        
    pq = [(0.0, 0, start_uid, [start_uid], None)]
    visited = excluded_uids.copy()
    
    while pq:
        cost, dist, current, path, last_line = heapq.heappop(pq)
        
        if current == end_uid:
            return path, dist
            
        if current in visited and current != start_uid:
            continue
        visited.add(current)
            
        for edge_tuple in connections.get(current, []):
            if len(edge_tuple) == 5:
                neighbor, edge_dist, line_no, vmax, klasa = edge_tuple
            else:
                neighbor, edge_dist = edge_tuple[:2]
                line_no, vmax, klasa = "999", 40.0, ""

            if neighbor not in visited:
                time_cost = cost_strategy.get_cost(edge_dist, vmax, line_no, klasa, last_line)
                
                if time_cost == float('inf'):
                    continue
                
                heapq.heappush(pq, (cost + time_cost, dist + edge_dist, neighbor, path + [neighbor], line_no))
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

    start_uid, start_orig = resolve_point(start_name, points_by_name, "Punkt poczatkowy")
    if not start_uid: return
    end_uid, end_orig = resolve_point(end_name, points_by_name, "Punkt koncowy")
    if not end_uid: return

    resolved_via = []
    for v_name in via_names:
        v_uid, v_orig = resolve_point(v_name, points_by_name, "Punkt posredni")
        if not v_uid: return
        resolved_via.append((v_uid, v_orig))

    excluded_uids = set()
    excluded_names_display = []
    for ex_name in exclude_names:
        ex_uid, ex_orig = resolve_point(ex_name, points_by_name, "Punkt wykluczony")
        if not ex_uid: return
        excluded_uids.add(ex_uid)
        excluded_names_display.append(ex_orig)

    all_targets = [start_uid] + [u for u, _ in resolved_via] + [end_uid]
    for target in all_targets:
        if target in excluded_uids:
            print(f"Blad: Punkt '{points[target]}' nie moze byc jednoczesnie na trasie i wsrod wykluczonych!")
            return

    waypoints = [(start_uid, start_orig)] + resolved_via + [(end_uid, end_orig)]
    via_str = f" przez: {', '.join([o for _, o in resolved_via])}" if resolved_via else ""
    ex_str = f" [wykluczone: {', '.join(excluded_names_display)}]" if excluded_names_display else ""
    tr_str = f" [trakcja: {traction}]" if traction else ""
    print(f"Szukanie optymalnej trasy: {start_orig} -> {end_orig}{via_str}{ex_str}{tr_str}...", flush=True)

    # Dependency Injection
    strategy = ElectricTractionStrategy() if traction == "E" else BaseTractionStrategy()

    full_path = []
    total_distance = 0
    for i in range(len(waypoints) - 1):
        seg_start_uid, seg_start_name = waypoints[i]
        seg_end_uid, seg_end_name = waypoints[i + 1]
        
        seg_path, seg_dist = dijkstra_segment(seg_start_uid, seg_end_uid, connections, excluded_uids, cost_strategy=strategy)
        if not seg_path:
            print(f"\nNie znaleziono polaczenia na odcinku: {seg_start_name} -> {seg_end_name} z uwzglednieniem podanych kryteriow.")
            return
            
        total_distance += seg_dist
        if not full_path:
            full_path.extend(seg_path)
        else:
            full_path.extend(seg_path[1:]) 

    print("\nZnaleziona trasa (zintegrowane dane PLK w bazie):")
    for idx, p in enumerate(full_path):
        tag = ""
        if p == start_uid: tag = "  [START]"
        elif p == end_uid: tag = "  [CEL]"
        elif any(p == v_uid for v_uid, _ in resolved_via): tag = "  [PRZEZ]"
        print(f" {idx+1:3d}. {points.get(p, str(p))}{tag}")
        
    print(f"\nLaczna liczba punktow konstrukcyjnych na trasie: {len(full_path)}")
    print(f"Laczny dystans: {total_distance / 1000.0:.3f} km")

def main():
    parser = argparse.ArgumentParser(
        description="Wyszukiwarka tras kolejowych - baza przechowuje natywne atrybuty (vmax, klasa).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("start", help="Nazwa punktu poczatkowego")
    parser.add_argument("end", help="Nazwa punktu koncowego")
    parser.add_argument("--via", "-v", nargs="+", default=[], help="Punkty posrednie")
    parser.add_argument("--exclude", "-e", nargs="+", default=[], help="Punkty wykluczone")
    parser.add_argument("--traction", "-t", choices=["E", "S"], default=None, help="Rodzaj trakcji (E/S)")
    
    if len(sys.argv) < 3:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    find_route(args.start, args.end, via_names=args.via, exclude_names=args.exclude, traction=args.traction)

if __name__ == "__main__":
    main()
