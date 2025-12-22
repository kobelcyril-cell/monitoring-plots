#!/usr/bin/env python3
import os
import re
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

# Pfad zu den MSC-Dateien
MSC_PATH = "/storage/research/aiub_u_camp/CK_ZDGNSS_2025/MSC"
OUTPUT_DIR = "/storage/homefs/ck18y530/monitoring-plots/plots/latest"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Hilfsfunktion, um die letzten 5 Ordner nach Datum zu sortieren
def get_last_n_folders(n=10):
    folders = [f for f in os.listdir(MSC_PATH) if f.startswith("MSC_")]
    folders.sort()
    return folders[-n:]


# Funktion, um Daten aus einer PROCESSING-Datei zu extrahieren
def parse_processing_file(file_path):
    data = {
        "num_obs_files": None,
        "deleted_files": None,
        "large_obs_files": None,
        "gpsxtr_rms": None,
        "gpsxtr_obs": None,
        "gpsxtr_par": None,
        "obsxtr_stats": {},
        "amb_stats": {}
    }

    with open(file_path, "r") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        # Number of observation files
        if "Number of observation files:" in line:
            data["num_obs_files"] = int(line.split(":")[1].strip())

        # Deleted files without matching entries
        if "Deleted " in line and "files without matching entries" in line:
            m = re.search(r"Deleted (\d+) files without matching entries", line)
            if m:
                data["deleted_files"] = int(m.group(1))

        # Large obs files (No stations with >50% bad observations found / Total deleted files)
        if "Total deleted files:" in line:
            m = re.search(r"Total deleted files:\s*(\d+)", line)
            if m:
                data["large_obs_files"] = int(m.group(1))

        # GPSXTR STATISTICS
        if "==== GPSXTR STATISTICS ====" in line:
            # Nächste Zeile mit Überschriften überspringen
            j = i + 3
            gps_line = lines[j].strip()
            parts = gps_line.split()
            data["gpsxtr_rms"] = float(parts[0])
            data["gpsxtr_obs"] = int(parts[2])
            data["gpsxtr_par"] = int(parts[3])

        # OBSXTR STATISTICS
        if "==== OBSXTR STATISTICS ====" in line:
            j = i + 1  # eine Zeile nach dem Header
            while j < len(lines) and lines[j].strip() != "===============================================":
                parts = lines[j].split()
                if len(parts) >= 5:
                    try:
                        sys = parts[0]
                        total = int(parts[2])
                        usable = int(parts[3])
                        bad = float(parts[4].replace("%", ""))
                        data["obsxtr_stats"][sys] = {
                            "total": total,
                            "usable": usable,
                            "bad": bad
                        }
                    except ValueError:
                        pass  # Zeile enthält keine gültigen Zahlen, ignorieren
                j += 1


        # Ambiguity resolution statistics
        if "==== Ambiguity resolution statistics ====" in line:
            j = i + 4
            while lines[j].strip() != "=============================================================":
                parts = lines[j].split()
                if len(parts) >= 4:
                    total = int(parts[0])
                    perc = float(parts[1])
                    sys = parts[2]
                    amb_type = parts[3]
                    if sys not in data["amb_stats"]:
                        data["amb_stats"][sys] = []
                    data["amb_stats"][sys].append({
                        "total": total,
                        "perc": perc,
                        "type": amb_type
                    })
                j += 1

    return data

# Hilfsfunktion: MSC_Ordnername → yy/ddd
def folder_to_date(folder_name):
    # Beispiel: MSC_25347 → 25/347
    yyddd = folder_name.split('_')[1]
    yy = yyddd[:2]
    ddd = yyddd[2:]
    return f"{yy}/{ddd}"

if __name__ == "__main__":
    last_folders = get_last_n_folders()
    print("Letzte 5 Ordner:", last_folders)

    all_data = {}
    for folder in last_folders:
        file_name = f"PROCESSING_{folder.split('_')[1]}"
        file_path = os.path.join(MSC_PATH, folder, file_name)
        if os.path.exists(file_path):
            all_data[folder] = parse_processing_file(file_path)
        else:
            all_data[folder] = None  # Keine Daten für diesen Tag

    x_labels = [folder_to_date(f) for f in last_folders]

    def safe_values(key, subkey=None, fill_nan=True, fill_zero=False):
        vals = []
        for folder in last_folders:
            data = all_data.get(folder)
            if not data:
                vals.append(np.nan if fill_nan else 0)
                continue
            val = data.get(key, None)
            if subkey:
                val = val.get(subkey, None) if val else (0 if fill_zero else np.nan)
            if val is None:
                if fill_zero:
                    vals.append(0)
                else:
                    vals.append(np.nan)
            else:
                vals.append(val)
        return vals

    # 1️⃣ Number of Observation Files
    y = safe_values("num_obs_files")
    plt.figure(figsize=(8,5))
    plt.bar(x_labels, y)
    plt.ylabel("#")
    plt.title("Number of Observation Files")
    plt.xticks(rotation=45)
    plt.ylim(np.nanmin(y)-5, np.nanmax(y)+5)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "num_obs_files.png"))
    plt.close()

    # 2️⃣ Deleted files
    # 2️⃣ Deleted files
    y = []
    for folder in last_folders:
        data = all_data.get(folder)
        if not data:
            y.append(np.nan)           # Keine Daten
        else:
            deleted = data.get("deleted_files")
            if deleted is None:
                y.append(0)            # Tatsächlich 0 gelöschte Dateien
            else:
                y.append(deleted)
    plt.figure(figsize=(8,5))
    plt.bar(x_labels, y)
    plt.ylabel("#")
    plt.title("Files without matching entries")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "deleted_files.png"))
    plt.close()

    # 3️⃣ Large observation files (0 für fehlende Werte)
    y = safe_values("large_obs_files", fill_nan=False, fill_zero=True)
    plt.figure(figsize=(8,5))
    plt.bar(x_labels, y)
    plt.ylabel("#")
    plt.title("CODXTR - files with >50% bad observations")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "large_obs_files.png"))
    plt.close()

    # 4️⃣ GPSXTR RMS
    y_rms = safe_values("gpsxtr_rms")
    plt.figure(figsize=(8,5))
    plt.plot(x_labels, y_rms, marker='o')
    plt.ylabel("RMS")
    plt.title("GPSXTR RMS")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "gpsxtr_rms.png"))
    plt.close()

    # 5️⃣ GPSXTR #Observations
    y_obs = safe_values("gpsxtr_obs")
    plt.figure(figsize=(8,5))
    plt.plot(x_labels, y_obs, marker='o')
    plt.ylabel("# Observations")
    plt.title("GPSXTR Observations")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "gpsxtr_obs.png"))
    plt.close()

    # 6️⃣ GPSXTR #Parameters
    y_par = safe_values("gpsxtr_par")
    plt.figure(figsize=(8,5))
    plt.plot(x_labels, y_par, marker='o')
    plt.ylabel("# Parameters")
    plt.title("GPSXTR Parameters")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "gpsxtr_par.png"))
    plt.close()

    # 7️⃣ OBSXTR bad %
    systems = ["GPS", "GLO", "GAL", "tot"]
    plt.figure(figsize=(10,6))
    for sys in systems:
        y_bad = []
        for folder in last_folders:
            data = all_data.get(folder)
            stats = data.get("obsxtr_stats", {}).get(sys) if data else None
            y_bad.append(stats["bad"] if stats else np.nan)
        plt.plot(x_labels, y_bad, marker='o', label=f"{sys} bad %")
    plt.ylabel("OBSXTR bad Observations")
    plt.title("%")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "obsxtr_bad.png"))
    plt.close()

    # 8️⃣ AMB Resolution Statistics
    amb_types = ["AR_WL", "AR_NL", "AR_NLR"]
    systems = ["G", "E", "G E"]
    plt.figure(figsize=(10,6))
    for sys in systems:
        for amb in amb_types:
            y = []
            for folder in last_folders:
                data = all_data.get(folder)
                if not data:
                    y.append(np.nan)
                    continue
                if sys != "G E":
                    entries = data.get("amb_stats", {}).get(sys, [])
                    val = next((e["perc"] for e in entries if e["type"] == amb), np.nan)
                else:
                    entries_G = data.get("amb_stats", {}).get("G", [])
                    entries_E = data.get("amb_stats", {}).get("E", [])
                    val_G = next((e["perc"] for e in entries_G if e["type"] == amb), 0)
                    val_E = next((e["perc"] for e in entries_E if e["type"] == amb), 0)
                    val = val_G + val_E if (entries_G or entries_E) else np.nan
                y.append(val)
            plt.plot(x_labels, y, marker='o', label=f"{sys} {amb}")
    plt.ylabel("%")
    plt.title("Ambiguity Resolution Statistics")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "amb_stats.png"))
    plt.close()
