#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import numpy as np

DEBUG = False  # auf True setzen, um Debug-Ausgaben zu sehen

def dbg(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

# ------------------------------------------------------------
# Pfade
# ------------------------------------------------------------
MSC_PATH = "/storage/research/aiub_u_camp/CK_ZDGNSS/MSC"
OUTPUT_DIR = "/storage/homefs/ck18y530/monitoring-plots/cmp_lapack"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------
# Letzte N MSC-Ordner
# ------------------------------------------------------------
def get_last_n_folders(n=60):
    folders = [f for f in os.listdir(MSC_PATH) if f.startswith("MSC_")]
    folders.sort()
    return folders[-n:]

# ------------------------------------------------------------
# Folder → yy/ddd
# ------------------------------------------------------------
def folder_to_date(folder_name):
    yyddd = folder_name.split("_")[1]
    return f"{yyddd[:2]}/{yyddd[2:]}"

# ------------------------------------------------------------
# CMP_LAPACK Parser
# ------------------------------------------------------------
def parse_cmp_lapack_file(file_path):
    dbg(f"Parsing {file_path}")
    data = {
        "position": {},
        "velocity": {},
        "max_crd_dif": {},
        "erp_dif_perc": {}
    }

    with open(file_path, "r") as f:
        lines = [l.strip() for l in f]

    i = 0
    while i < len(lines):
        line = lines[i]

        # -----------------------
        # Position
        # -----------------------
        if line.startswith("Position"):
            # die nächsten Zeilen nach Position suchen
            j = i + 1
            while j < len(lines) and len(data["position"]) < 3:
                l = lines[j]
                dbg(f"Position line: {l}")
                match = re.match(r"(\w+)\s*:\s*([-+0-9.eE]+)\s*mm\s*\(SVN\s*(\d+)\)", l)
                if match:
                    comp, val, svn = match.groups()
                    data["position"][comp] = {"value": float(val), "svn": int(svn)}
                    dbg(f"  -> {comp}: {val} mm, SVN {svn}")
                j += 1
            i = j
            continue

        # -----------------------
        # Velocity
        # -----------------------
        if line.startswith("Velocity"):
            j = i + 1
            while j < len(lines) and len(data["velocity"]) < 3:
                l = lines[j]
                dbg(f"Velocity line: {l}")
                match = re.match(r"(\w+)\s*:\s*([-+0-9.eE]+)\s*mm/s\s*\(SVN\s*(\d+)\)", l)
                if match:
                    comp, val, svn = match.groups()
                    data["velocity"][comp] = {"value": float(val), "svn": int(svn)}
                    dbg(f"  -> {comp}: {val} mm/s, SVN {svn}")
                j += 1
            i = j
            continue

        # -----------------------
        # MAX CRD DIF
        # -----------------------
        if line.startswith("MAX CRD DIF"):
            j = i + 1
            while j < len(lines) and len(data["max_crd_dif"]) < 3:
                l = lines[j]
                dbg(f"MAX CRD DIF line: {l}")
                match = re.match(r"(\w+)\s*:\s*([-+0-9.eE]+)\s*mm\s*\(Station:\s*(\w+)\)", l)
                if match:
                    comp, val, station = match.groups()
                    data["max_crd_dif"][comp] = {"value": float(val), "station": station}
                    dbg(f"  -> {comp}: {val} mm, Station {station}")
                j += 1
            i = j
            continue

        # -----------------------
        # ERP DIF
        # -----------------------
        if line.startswith("ERP DIF"):
            # die nächsten Zeilen nach Header suchen
            j = i + 3  # Header + Trennlinien überspringen
            data_lines = []
            while j < len(lines):
                l = lines[j]
                if re.match(r"^\d{4}-\d{2}-\d{2}", l):  # Zeile beginnt mit Datum
                    dbg(f"ERP line found: {l}")
                    data_lines.append(l)
                j += 1

            if len(data_lines) >= 2:  # zweite Datenzeile nehmen
                l2 = data_lines[1]
                parts = l2.split()
                data["erp_dif_perc"] = {
                    "dX": float(parts[2]) * 1e6,
                    "dY": float(parts[4]) * 1e6,
                    "dUT1": float(parts[6]) * 1e6
                }
                dbg(f"  -> ERP (2nd line) dX: {parts[2]}, dY: {parts[4]}, dUT1: {parts[6]}")
            else:
                dbg("  -> ERP: nicht genug Datenzeilen")
            i = j
            continue

        i += 1

    return data

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    last_folders = get_last_n_folders()
    x_labels = [folder_to_date(f) for f in last_folders]

    all_data = {}

    for folder in last_folders:
        folder_path = os.path.join(MSC_PATH, folder)
        files = [f for f in os.listdir(folder_path) if f.startswith("CMP_LAPACK_")]
        if not files:
            all_data[folder] = None
            continue
        fpath = os.path.join(folder_path, files[0])
        all_data[folder] = parse_cmp_lapack_file(fpath)

    # --------------------------------------------------------
    # Speichere übersichtliches TXT File
    # --------------------------------------------------------
    output_txt = os.path.join(OUTPUT_DIR, "cmp_lapack_summary.txt")
    with open(output_txt, "w") as f:
        for folder in last_folders:
            f.write(f"=== Folder {folder} ({folder_to_date(folder)}) ===\n")
            data = all_data.get(folder)
            if not data:
                f.write("No CMP_LAPACK file found\n\n")
                continue

            f.write("Position (mm, SVN):\n")
            for comp in ["Radial", "Along", "Cross"]:
                val = data["position"].get(comp)
                if val:
                    f.write(f"  {comp}: {val['value']:.4f} mm (SVN {val['svn']})\n")

            f.write("Velocity (mm/s, SVN):\n")
            for comp in ["Radial", "Along", "Cross"]:
                val = data["velocity"].get(comp)
                if val:
                    f.write(f"  {comp}: {val['value']:.4f} mm/s (SVN {val['svn']})\n")

            f.write("MAX CRD DIF (mm, Station):\n")
            for comp in ["North", "East", "Up"]:
                val = data["max_crd_dif"].get(comp)
                if val:
                    f.write(f"  {comp}: {val['value']:.4f} mm (Station {val['station']})\n")

            f.write("ERP DIF % (erste Datenzeile):\n")
            erp = data.get("erp_dif_perc")
            if erp:
                f.write(f"  dX: {erp['dX']:.6e} %, dY: {erp['dY']:.6e} %, dUT1: {erp['dUT1']:.6e} %\n")

            f.write("\n")

    #print(f"Summary saved to {output_txt}")
