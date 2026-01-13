#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import pandas as pd
import math

# -----------------------------
# Datei einlesen
# -----------------------------
input_file = "/storage/homefs/ck18y530/monitoring-plots/cmp_lapack/cmp_lapack_summary.txt"
output_file = "/storage/homefs/ck18y530/monitoring-plots/cmp_lapack/cmp_lapack_summary_table.txt"

with open(input_file, "r") as f:
    lines = f.readlines()

# -----------------------------
# Regex Patterns vorbereiten
# -----------------------------
folder_pattern = re.compile(r"=== Folder MSC_(\d+) \((\d+)/(\d+)\) ===")
position_pattern = re.compile(r"\s*(Radial|Along|Cross):\s*([-\d.eE]+)\s*mm \(SVN (\d+)\)")
velocity_pattern = re.compile(r"\s*(Radial|Along|Cross):\s*([-\d.eE]+)\s*mm/s \(SVN (\d+)\)")
max_crd_pattern = re.compile(r"\s*(North|East|Up):\s*([-\d.eE]+)\s*mm \(Station (\S+)\)")
erp_pattern = re.compile(r"dX:\s*([+\-\d.eE]+) %, dY:\s*([+\-\d.eE]+) %, dUT1:\s*([+\-\d.eE]+) %")
# -----------------------------
# Daten parsen
# -----------------------------
data = []
current = {}

for line in lines:
    # Folder
    m = folder_pattern.match(line)
    if m:
        if current:
            data.append(current)
        current = {
            "YY": int(m.group(2)),
            "DDD": int(m.group(3))
        }
        continue

    # Position
    m = position_pattern.match(line)
    if m:
        current[f"Pos_{m.group(1)}"] = float(m.group(2))
        current[f"Pos_SVN_{m.group(1)}"] = int(m.group(3))
        continue

    # Velocity
    m = velocity_pattern.match(line)
    if m:
        current[f"Vel_{m.group(1)}"] = float(m.group(2))
        current[f"Vel_SVN_{m.group(1)}"] = int(m.group(3))
        continue

    # MAX CRD DIF
    m = max_crd_pattern.match(line)
    if m:
        current[f"MAX_{m.group(1)}"] = float(m.group(2))
        current[f"MAX_Station_{m.group(1)}"] = m.group(3)
        continue

    # ERP DIF %
    m = erp_pattern.search(line)
    if m:
        current["ERP_X"] = float(m.group(1))
        current["ERP_Y"] = float(m.group(2))
        current["ERP_UT1"] = float(m.group(3))
        continue

# Letztes Element hinzufügen
if current:
    data.append(current)

# -----------------------------
# DataFrame erstellen
# -----------------------------
columns_order = [
    "YY", "DDD",
    "Pos_Radial", "Pos_SVN_Radial",
    "Pos_Along", "Pos_SVN_Along",
    "Pos_Cross", "Pos_SVN_Cross",
    "Vel_Radial", "Vel_SVN_Radial",
    "Vel_Along", "Vel_SVN_Along",
    "Vel_Cross", "Vel_SVN_Cross",
    "MAX_North", "MAX_Station_North",
    "MAX_East", "MAX_Station_East",
    "MAX_Up", "MAX_Station_Up",
    "ERP_X", "ERP_Y", "ERP_UT1"
]

df = pd.DataFrame(data)

# Fehlende Spalten auffüllen
for col in columns_order:
    if col not in df.columns:
        df[col] = float('nan')

df = df[columns_order]

# -----------------------------
# Formatfunktionen
# -----------------------------
def format_int_or_nan(value):
    if isinstance(value, float) and math.isnan(value):
        return "---"
    try:
        return f"{int(value)}"
    except:
        return str(value)

def format_float_or_nan(value):
    if isinstance(value, float) and math.isnan(value):
        return "---"
    try:
        return f"{float(value):.2f}"
    except:
        return str(value)

def format_erp_or_nan(value):
    if isinstance(value, float) and math.isnan(value):
        return "---"
    try:
        return f"{float(value):.2e}"
    except:
        return str(value)

def format_station(value):
    """Gibt '---' zurück, wenn der Stationseintrag fehlt oder NaN ist."""
    if pd.isna(value) or value is None:
        return "---"
    return str(value)
# -----------------------------
# Header-Spaltennamen
# -----------------------------
header_cols = [
    'YY','DDD',
    'Pos-R [mm]','SVN','Pos-A [mm]','SVN','Pos-C [mm]','SVN',
    'Vel-R [mm/s]','SVN','Vel-A [mm/s]','SVN','Vel-C [mm/s]','SVN',
    'North [mm]','Station','East [mm]','Station','Up [mm]','Station',
    'ERP-X [μas]','ERP-Y [μas]','ERP-LOD [μs]'
]

# -----------------------------
# Berechne Spaltenbreiten dynamisch
# -----------------------------
col_widths = []
for i, col in enumerate(header_cols):
    max_len = len(col)
    for _, row in df.iterrows():
        try:
            if 'SVN' in col:
                val = format_int_or_nan(row[df.columns[i-1]])
            elif 'Station' in col:
                val = str(row[df.columns[i-1]])
            elif 'ERP' in col:
                val = format_erp_or_nan(row[df.columns[i-1]])
            else:
                val = format_float_or_nan(row[df.columns[i-1]])
            max_len = max(max_len, len(val))
        except:
            continue
    col_widths.append(max_len + 1)  # +1 für Abstand

# -----------------------------
# Tabelle schreiben
# -----------------------------
with open(output_file, "w") as f:
    # Header
    header_line = " | ".join(f"{c:>{w}}" for c,w in zip(header_cols, col_widths))
    f.write(header_line + "\n")
    f.write("-" * len(header_line) + "\n")

    # Zeilen
    for _, row in df.iterrows():
        row_cells = [
            format_int_or_nan(row['YY']),
            format_int_or_nan(row['DDD']),
            format_float_or_nan(row['Pos_Radial']),
            format_int_or_nan(row['Pos_SVN_Radial']),
            format_float_or_nan(row['Pos_Along']),
            format_int_or_nan(row['Pos_SVN_Along']),
            format_float_or_nan(row['Pos_Cross']),
            format_int_or_nan(row['Pos_SVN_Cross']),
            format_float_or_nan(row['Vel_Radial']),
            format_int_or_nan(row['Vel_SVN_Radial']),
            format_float_or_nan(row['Vel_Along']),
            format_int_or_nan(row['Vel_SVN_Along']),
            format_float_or_nan(row['Vel_Cross']),
            format_int_or_nan(row['Vel_SVN_Cross']),
            format_float_or_nan(row['MAX_North']),
            format_station(row['MAX_Station_North']),
            format_float_or_nan(row['MAX_East']),
            format_station(row['MAX_Station_East']),
            format_float_or_nan(row['MAX_Up']),
            format_station(row['MAX_Station_Up']),
            format_erp_or_nan(row['ERP_X']),
            format_erp_or_nan(row['ERP_Y']),
            format_erp_or_nan(row['ERP_UT1'])
        ]
        f.write(" | ".join(f"{c:>{w}}" for c,w in zip(row_cells, col_widths)) + "\n")

#print(f"Formatiertes Tabellen-File gespeichert unter: {output_file}")
