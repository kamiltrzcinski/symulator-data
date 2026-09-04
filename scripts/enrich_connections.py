import os
import json
import pandas as pd
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parent.parent

def parse_km(val):
    try:
        return float(str(val).replace(',', '.'))
    except (ValueError, TypeError):
        return 0.0

def parse_speed(val):
    try:
        return float(str(val).replace(',', '.'))
    except (ValueError, TypeError):
        return 0.0

def build_registry():
    sources_dir = ROOT / "data" / "plk_registry_sources"
    speeds_file = sources_dir / "N_ZAL_2.1_20252026_20260825065748.xlsx"
    classes_file = sources_dir / "N_ZAL_2.4_20252026_20260825065756.xlsx"
    
    registry = {}
    
    print("Reading maximum speeds from", speeds_file.name)
    xl_v = pd.ExcelFile(speeds_file)
    sheet_v = [s for s in xl_v.sheet_names if 'dane' in s][0]
    df_v = pd.read_excel(speeds_file, sheet_name=sheet_v)
    if 'Nr linii' not in str(df_v.columns):
        for i in range(10):
            if 'Nr linii' in str(df_v.iloc[i].values):
                df_v = pd.read_excel(speeds_file, sheet_name=sheet_v, header=i+1)
                break
                
    for _, row in df_v.iterrows():
        line_no = str(row.get('Nr linii', '')).strip()
        if not line_no or line_no == 'nan':
            continue
            
        km_start = parse_km(row.get('Km pocz. ', row.get('Km pocz.')))
        km_end = parse_km(row.get('Km końca'))
        tor = str(row.get('Tor', '1')).strip()
        
        pas_col = [c for c in df_v.columns if 'Pasażerskie' in str(c)]
        vmax_pas = parse_speed(row[pas_col[0]]) if pas_col else 0.0
        
        tow_col = [c for c in df_v.columns if 'towarowe' in str(c)]
        vmax_tow = parse_speed(row[tow_col[0]]) if tow_col else 0.0
        
        if line_no not in registry:
            registry[line_no] = {"speeds": [], "classes": []}
            
        registry[line_no]["speeds"].append({
            "track": tor,
            "km_start": km_start,
            "km_end": km_end,
            "vmax_pas": vmax_pas,
            "vmax_tow": vmax_tow
        })

    print("Reading line classes from", classes_file.name)
    xl_c = pd.ExcelFile(classes_file)
    sheet_c = [s for s in xl_c.sheet_names if 'dane' in s][0]
    df_c = pd.read_excel(classes_file, sheet_name=sheet_c)
    if 'Nr linii' not in str(df_c.columns):
        for i in range(10):
            if 'Nr linii' in str(df_c.iloc[i].values):
                df_c = pd.read_excel(classes_file, sheet_name=sheet_c, header=i+1)
                break

    for _, row in df_c.iterrows():
        line_no = str(row.get('Nr linii', '')).strip()
        if not line_no or line_no == 'nan':
            continue
            
        km_start = parse_km(row.get('Km pocz.', row.get('Km pocz. ')))
        km_end = parse_km(row.get('Km końca'))
        tor = str(row.get('Tor', '1')).strip()
        klasa = str(row.get('Klasa odcinka linii', '')).strip()
        
        if line_no not in registry:
            registry[line_no] = {"speeds": [], "classes": []}
            
        registry[line_no]["classes"].append({
            "track": tor,
            "km_start": km_start,
            "km_end": km_end,
            "class": klasa
        })
        
    return registry

def get_segment_vmax(line_no, from_m, to_m, registry):
    line_data = registry.get(line_no)
    if not line_data or not line_data.get("speeds"): return 40.0
    speeds = line_data["speeds"]
    start_km = min(from_m, to_m) / 1000.0
    end_km = max(from_m, to_m) / 1000.0
    total_v = 0.0
    total_l = 0.0
    for s in speeds:
        if s["track"] not in ["1", "N"]: continue
        skm_s = min(s["km_start"], s["km_end"])
        skm_e = max(s["km_start"], s["km_end"])
        overlap_start = max(start_km, skm_s)
        overlap_end = min(end_km, skm_e)
        if overlap_end > overlap_start:
            l = overlap_end - overlap_start
            v = s["vmax_pas"] if s["vmax_pas"] > 0 else 40.0
            total_v += v * l
            total_l += l
    if total_l > 0: return total_v / total_l
    return max([s["vmax_pas"] for s in speeds if s["vmax_pas"] > 0] + [40.0])

def get_segment_class(line_no, from_m, to_m, registry):
    line_data = registry.get(line_no)
    if not line_data or not line_data.get("classes"): return ""
    classes = line_data["classes"]
    start_km = min(from_m, to_m) / 1000.0
    end_km = max(from_m, to_m) / 1000.0
    class_l = {}
    for c in classes:
        if c["track"] not in ["1", "N"]: continue
        ckm_s = min(c["km_start"], c["km_end"])
        ckm_e = max(c["km_start"], c["km_end"])
        overlap_start = max(start_km, ckm_s)
        overlap_end = min(end_km, ckm_e)
        if overlap_end > overlap_start:
            l = overlap_end - overlap_start
            k = c["class"]
            class_l[k] = class_l.get(k, 0) + l
    if class_l:
        return max(class_l.items(), key=lambda x: x[1])[0]
    return ""

def main():
    registry = build_registry()
    connections_dir = ROOT / "data" / "timetable_connections"
    if not connections_dir.exists():
        print("No timetable_connections found!")
        return
        
    print("Enriching connections with PLK registry data...")
    count = 0
    for p in connections_dir.glob("*.json"):
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
            
        modified = False
        lines = obj.get("lines", [])
        for line in lines:
            lno = str(line.get("line_no", "999"))
            fm = line.get("from_meter", 0)
            tm = line.get("to_meter", 0)
            vmax = get_segment_vmax(lno, fm, tm, registry)
            klasa = get_segment_class(lno, fm, tm, registry)
            
            line["vmax"] = round(vmax, 1)
            line["class"] = klasa
            modified = True
            
        if modified:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2, ensure_ascii=False)
            count += 1
            
    print(f"Enriched {count} connection files.")

if __name__ == "__main__":
    main()
