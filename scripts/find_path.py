import json
import pickle
import heapq
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE_FILE = ROOT / "data" / ".topology_cache.pkl"
REGISTRY_FILE = ROOT / "data" / "plk_registry.json"

def load_registry():
    if not REGISTRY_FILE.exists():
        print(f"Brak pliku {REGISTRY_FILE.name}. Uruchom najpierw import_plk_registry.py.", file=sys.stderr)
        return {}
    with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

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
                
                # Zapisujemy dystans, nr linii, oraz poczatek/koniec kilometracji 
                dist = 0
                line_no = "999"
                from_meter = 0
                to_meter = 0
                
                if lines_data:
                    from_meter = lines_data[0].get("from_meter", 0)
                    to_meter = lines_data[0].get("to_meter", 0)
                    dist = abs(to_meter - from_meter)
                    line_no = str(lines_data[0].get("line_no", "999"))
                
                if fr not in connections:
                    connections[fr] = []
                connections[fr].append((to, dist, line_no, from_meter, to_meter))
                
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

def get_segment_vmax(line_no: str, from_m: int, to_m: int, registry: dict) -> float:
    """Zwraca usredniona predkosc dla danego odcinka na podstawie rejestru PLK."""
    line_data = registry.get(line_no)
    if not line_data:
        return 40.0 # domyslna niska predkosc dla nieznanych linii (np. lacznice)
        
    speeds = line_data.get("speeds", [])
    if not speeds:
        return 40.0
        
    start_km = min(from_m, to_m) / 1000.0
    end_km = max(from_m, to_m) / 1000.0
    
    total_weighted_vmax = 0.0
    total_length = 0.0
    
    for s in speeds:
        # Zakladamy tor 1 lub N dla uproszczenia (mozna dopracowac o konkretny tor)
        if s["track"] not in ["1", "N"]:
            continue
            
        s_km_start = min(s["km_start"], s["km_end"])
        s_km_end = max(s["km_start"], s["km_end"])
        
        # Oblicz czesc wspolna przedzialow
        overlap_start = max(start_km, s_km_start)
        overlap_end = min(end_km, s_km_end)
        
        if overlap_end > overlap_start:
            length = overlap_end - overlap_start
            vmax = s["vmax_pas"] if s["vmax_pas"] > 0 else 40.0
            total_weighted_vmax += vmax * length
            total_length += length
            
    if total_length > 0:
        return total_weighted_vmax / total_length
    else:
        # Jesli nie znalezlismy zadnego pokrycia, wez maksymalna dla calej linii
        max_v = max([s["vmax_pas"] for s in speeds if s["vmax_pas"] > 0] + [40.0])
        return max_v

def get_segment_class(line_no: str, from_m: int, to_m: int, registry: dict) -> str:
    """Zwraca dominujaca klase odcinka na podstawie rejestru PLK."""
    line_data = registry.get(line_no)
    if not line_data:
        return ""
        
    classes = line_data.get("classes", [])
    if not classes:
        return ""
        
    start_km = min(from_m, to_m) / 1000.0
    end_km = max(from_m, to_m) / 1000.0
    
    class_lengths = {}
    for c in classes:
        if c["track"] not in ["1", "N"]:
            continue
            
        c_km_start = min(c["km_start"], c["km_end"])
        c_km_end = max(c["km_start"], c["km_end"])
        
        overlap_start = max(start_km, c_km_start)
        overlap_end = min(end_km, c_km_end)
        
        if overlap_end > overlap_start:
            length = overlap_end - overlap_start
            klasa = c["class"]
            class_lengths[klasa] = class_lengths.get(klasa, 0) + length
            
    if class_lengths:
        # Zwroc klase, ktora pokrywa najdluzszy fragment
        return max(class_lengths.items(), key=lambda x: x[1])[0]
    return ""

def dijkstra_segment(start_uid, end_uid, connections, excluded_uids, registry, traction=None):
    """Finds optimal path using Dijkstra prioritizing time based on factual PLK speed limits."""
    if start_uid == end_uid:
        return [start_uid], 0
        
    # (cost_minutes, physical_distance, current_uid, path, last_line_no)
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
                neighbor, edge_dist, line_no, from_meter, to_meter = edge_tuple
            elif len(edge_tuple) == 3:
                neighbor, edge_dist, line_no = edge_tuple
                from_meter, to_meter = 0, 0
            else:
                neighbor, edge_dist = edge_tuple[:2]
                line_no, from_meter, to_meter = "999", 0, 0

            if neighbor not in visited:
                vmax = get_segment_vmax(line_no, from_meter, to_meter, registry)
                klasa = get_segment_class(line_no, from_meter, to_meter, registry)
                
                # Czas przejazdu w minutach (dystans w km / vmax w km/h * 60)
                # Zabezpieczenie przed dystansem = 0
                dist_km = max(edge_dist, 100) / 1000.0
                time_cost = (dist_km / vmax) * 60.0
                
                # Kara za zmiane linii (zapobiega niepotrzebnemu skakaniu po lacznicach i wezlach)
                if last_line is not None and last_line != line_no:
                    time_cost += 5.0  # +5 minut za zmiane linii (karygodne zygzakowanie)
                    
                # Brak twardych danych o trakcji z ZAL 2.2, ale stosujemy ogolna heurystyke na podstawie klas i predkosci:
                # Linie znaczenia miejscowego o niskiej predkosci rzadko maja siec trakcyjna.
                if traction == "E":
                    if vmax < 60.0 and klasa not in ["C3", "C4", "D3", "D4"]:
                        time_cost *= 3.0 # Duza kara dla tras potencjalnie niezelektryfikowanych
                
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
    registry = load_registry()
    
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
    print(f"Szukanie optymalnej trasy (na bazie predkosci z reg. PLK): {start_orig} -> {end_orig}{via_str}{ex_str}{tr_str}...", flush=True)

    full_path = []
    total_distance = 0
    for i in range(len(waypoints) - 1):
        seg_start_uid, seg_start_name = waypoints[i]
        seg_end_uid, seg_end_name = waypoints[i + 1]
        
        seg_path, seg_dist = dijkstra_segment(seg_start_uid, seg_end_uid, connections, excluded_uids, registry, traction=traction)
        if not seg_path:
            print(f"\nNie znaleziono polaczenia na odcinku: {seg_start_name} -> {seg_end_name} z uwzglednieniem podanych kryteriow.")
            return
            
        total_distance += seg_dist
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
    print(f"Laczny dystans: {total_distance / 1000.0:.3f} km")

def main():
    parser = argparse.ArgumentParser(
        description="Wyszukiwarka tras w oparciu o parametry z Regulaminu Sieci PLK.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("start", help="Nazwa punktu poczatkowego")
    parser.add_argument("end", help="Nazwa punktu koncowego")
    parser.add_argument(
        "--via", "-v", 
        nargs="+", 
        default=[], 
        help="Punkty posrednie przez ktore musi przebiegac trasa"
    )
    parser.add_argument(
        "--exclude", "-e", 
        nargs="+", 
        default=[], 
        help="Punkty wykluczone z wyznaczania trasy"
    )
    parser.add_argument(
        "--traction", "-t",
        choices=["E", "S"],
        default=None,
        help="Rodzaj trakcji (E/S) - wariant przyblizony"
    )
    
    if len(sys.argv) < 3:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()
    find_route(args.start, args.end, via_names=args.via, exclude_names=args.exclude, traction=args.traction)

if __name__ == "__main__":
    main()
