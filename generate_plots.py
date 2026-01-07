#!/usr/bin/env python3
import os
import re
import numpy as np
import matplotlib.pyplot as plt

DEBUG = False

def dbg(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

# ------------------------------------------------------------
# Pfade
# ------------------------------------------------------------
MSC_PATH = "/storage/research/aiub_u_camp/CK_ZDGNSS/MSC"
OUTPUT_DIR = "/storage/homefs/ck18y530/monitoring-plots/plots/latest"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------------------------------------
# Letzte N MSC-Ordner
# ------------------------------------------------------------
def get_last_n_folders(n=40):
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
# PROCESSING-File Parser
# ------------------------------------------------------------
def parse_processing_file(file_path):
    dbg(f"Parse {file_path}")

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

        # Deleted files
        if "Deleted " in line and "files without matching entries" in line:
            m = re.search(r"Deleted (\d+) files without matching entries", line)
            if m:
                data["deleted_files"] = int(m.group(1))

        # Removed files from campaign
        if "Total deleted files:" in line:
            m = re.search(r"Total deleted files:\s*(\d+)", line)
            if m:
                data["large_obs_files"] = int(m.group(1))

        # GPSXTR STATISTICS
        if "==== GPSXTR STATISTICS ====" in line:
            parts = lines[i + 3].split()
            data["gpsxtr_rms"] = float(parts[0])
            data["gpsxtr_obs"] = int(parts[2])
            data["gpsxtr_par"] = int(parts[3])

        # OBSXTR STATISTICS
        if "==== OBSXTR STATISTICS ====" in line:
            j = i + 1
            while j < len(lines) and "====" not in lines[j]:
                parts = lines[j].split()
                if len(parts) >= 5:
                    try:
                        sys = parts[0]
                        data["obsxtr_stats"][sys] = {
                            "total": int(parts[2]),
                            "usable": int(parts[3]),
                            "bad": float(parts[4].replace("%", ""))
                        }
                    except ValueError:
                        pass
                j += 1

        # Ambiguity resolution statistics
        if "==== Ambiguity resolution statistics ====" in line:
            dbg("Ambiguity resolution block gefunden")
            j = i + 4
            while lines[j].strip() != "=============================================================":
                parts = lines[j].split()
                if len(parts) >= 4:
                    total = int(parts[0])
                    perc = float(parts[1])
                    sys = parts[2]
                    amb_type = parts[3]

                    # nur AR_ Typen aufnehmen
                    if amb_type.startswith("AR_"):
                        if sys not in data["amb_stats"]:
                            data["amb_stats"][sys] = []
                        data["amb_stats"][sys].append({
                            "total": total,
                            "perc": perc,
                            "type": amb_type
                        })
                        dbg(f"  AMB {sys} {amb_type}: {perc}")
                j += 1

    return data

# ------------------------------------------------------------
# NaN-sichere Extraktion
# ------------------------------------------------------------
def safe_values(extractor, label=""):
    vals = []
    dbg(f"--- {label} ---")
    for folder in last_folders:
        data = all_data.get(folder)
        if not data:
            dbg(f"{folder}: NaN (kein File)")
            vals.append(np.nan)
            continue
        try:
            v = extractor(data)
            dbg(f"{folder}: {v}")
            vals.append(v if v is not None else np.nan)
        except Exception as e:
            dbg(f"{folder}: FEHLER {e}")
            vals.append(np.nan)
    return np.array(vals, dtype=float)

# ------------------------------------------------------------
# NaN-Markierung
# ------------------------------------------------------------
def mark_nan_days(x, y):
    ymin, ymax = plt.ylim()
    nan_idx = np.isnan(y)
    if np.any(nan_idx):
        plt.scatter(
            np.array(x)[nan_idx],
            np.full(np.sum(nan_idx), ymin),
            marker="x",
            color="gray",
            zorder=5
        )
        plt.ylim(ymin, ymax)

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
if __name__ == "__main__":

    last_folders = get_last_n_folders()
    x_labels = [folder_to_date(f) for f in last_folders]

    all_data = {}
    for folder in last_folders:
        fname = f"PROCESSING_{folder.split('_')[1]}"
        fpath = os.path.join(MSC_PATH, folder, fname)
        all_data[folder] = parse_processing_file(fpath) if os.path.exists(fpath) else None

    # --------------------------------------------------------
    # 1 Number of observation files (dynamisch skaliert)
    # --------------------------------------------------------
    y = safe_values(lambda d: d["num_obs_files"], "num_obs_files")
    plt.figure(figsize=(8,5))
    plt.bar(x_labels, y)
    mark_nan_days(x_labels, y)

    if np.any(~np.isnan(y)):
        ymin = np.nanmin(y)
        ymax = np.nanmax(y)
        pad = max(5, 0.05 * (ymax - ymin))
        plt.ylim(ymin - pad, ymax + pad)

    plt.title("Number of Observation Files")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "num_obs_files.png"))
    plt.close()

    # --------------------------------------------------------
    # 2 Deleted files
    # --------------------------------------------------------
    y = safe_values(lambda d: d["deleted_files"] or 0, "deleted_files")
    plt.figure(figsize=(8,5))
    plt.bar(x_labels, y)
    mark_nan_days(x_labels, y)
    plt.title("Files without matching entries")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "deleted_files.png"))
    plt.close()

    # --------------------------------------------------------
    # 3 Large observation files
    # --------------------------------------------------------
    y = safe_values(lambda d: d["large_obs_files"] or 0, "large_obs_files")
    plt.figure(figsize=(8,5))
    plt.bar(x_labels, y)
    mark_nan_days(x_labels, y)
    plt.title("Campaign clean: # deleted files")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "large_obs_files.png"))
    plt.close()

    # --------------------------------------------------------
    # 4–6 GPSXTR
    # --------------------------------------------------------
    gps_plots = [
        ("gpsxtr_rms", "GPSXTR: RMS [mm]", "gpsxtr_rms.png"),
        ("gpsxtr_obs", "GPSXTR: Observations", "gpsxtr_obs.png"),
        ("gpsxtr_par", "GPSXTR: Parameters", "gpsxtr_par.png"),
    ]

    for key, title, fname in gps_plots:
        y = safe_values(lambda d, k=key: d[k], key)
        plt.figure(figsize=(8,5))
        plt.plot(x_labels, y, marker="o")
        mark_nan_days(x_labels, y)
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, fname))
        plt.close()

    # --------------------------------------------------------
    # 7 OBSXTR bad % (fixe Skala 0-20)
    # --------------------------------------------------------
    plt.figure(figsize=(10,6))
    for sys in ["GPS", "GLO", "GAL", "tot"]:
        y = safe_values(lambda d, s=sys: d["obsxtr_stats"].get(s, {}).get("bad"),
                        f"OBSXTR bad {sys}")
        plt.plot(x_labels, y, marker="o", label=sys)
        mark_nan_days(x_labels, y)

    plt.ylim(0, 20)
    plt.ylabel("%")
    plt.title("OBSXTR: bad Observations")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "obsxtr_bad.png"))
    plt.close()

    # --------------------------------------------------------
    # 8 Ambiguity resolution statistics
    # --------------------------------------------------------
    amb_types = ["AR_WL", "AR_NL", "AR_NLR"]
    systems = ["G", "E"]

    plt.figure(figsize=(10, 6))

    for sys in systems:
        for amb in amb_types:
            y_vals = []

            for folder in last_folders:
                data = all_data.get(folder)
                if not data:
                    y_vals.append(np.nan)
                    continue

                entries = data.get("amb_stats", {}).get(sys, [])
                val = next((e["perc"] for e in entries if e["type"] == amb), np.nan)
                y_vals.append(val)

            plt.plot(
                x_labels,
                y_vals,
                marker="o",
                label=f"{sys} {amb}"
            )
            mark_nan_days(x_labels, np.array(y_vals))

    plt.ylabel("Resolved ambiguities [%]")
    plt.ylim(0, 100)
    plt.title("Ambiguity Resolution Statistics")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "amb_stats.png"))
    plt.close()
