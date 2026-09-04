import os
import json
import pandas as pd
from pathlib import Path
import argparse

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reg-dir", default=r"C:\Users\tymon\Desktop\reg", help="Directory with registry Excel files")
    parser.add_argument("--out-file", default=r"C:\Users\tymon\Desktop\SUSRK\symulator-data\data\plk_registry.json", help="Output JSON file")
    args = parser.parse_args()

    reg_dir = Path(args.reg_dir)
    speeds_file = reg_dir / "N_ZAL_2.1_20252026_20260825065748.xlsx"
    classes_file = reg_dir / "N_ZAL_2.4_20252026_20260825065756.xlsx"
    
    registry = {}
    
    print("Reading maximum speeds from", speeds_file.name)
    xl_v = pd.ExcelFile(speeds_file)
    sheet_v = [s for s in xl_v.sheet_names if 'dane' in s][0]
    df_v = pd.read_excel(speeds_file, sheet_name=sheet_v)
    # find header
    if 'Nr linii' not in str(df_v.columns):
        for i in range(10):
            if 'Nr linii' in str(df_v.iloc[i].values):
                df_v = pd.read_excel(speeds_file, sheet_name=sheet_v, header=i+1)
                break
                
    for idx, row in df_v.iterrows():
        line_no = str(row.get('Nr linii', '')).strip()
        if not line_no or line_no == 'nan':
            continue
            
        km_start = parse_km(row.get('Km pocz. ', row.get('Km pocz.')))
        km_end = parse_km(row.get('Km końca'))
        tor = str(row.get('Tor', '1')).strip()
        
        # Pasażerskie składy wagonowe i lokomotywy luzem
        pas_col = [c for c in df_v.columns if 'Pasażerskie' in str(c)]
        vmax_pas = parse_speed(row[pas_col[0]]) if pas_col else 0.0
        
        # Pociągi towarowe
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

    for idx, row in df_c.iterrows():
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
        
    print(f"Saving registry to {args.out_file}...")
    with open(args.out_file, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
        
    print("Done!")

if __name__ == "__main__":
    main()
