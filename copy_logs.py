#!/usr/bin/env python3

import os
import shutil
from datetime import datetime

# -------------------------------
# SETTINGS
# -------------------------------
SRC_BASE = "/storage/research/aiub_u_camp/CK_ZDGNSS/MSC"
DST_DIR = "/storage/homefs/ck18y530/monitoring-plots/logs/latest"
N_LATEST = 4

os.makedirs(DST_DIR, exist_ok=True)

# -------------------------------
# Liste der Unterordner (MSC_*)
# -------------------------------
folders = []
for entry in os.listdir(SRC_BASE):
    full_path = os.path.join(SRC_BASE, entry)
    if os.path.isdir(full_path) and entry.startswith("MSC_"):
        # Datum aus Ordnername extrahieren
        yyddd = entry.split("_")[1]
        folders.append((yyddd, full_path))

# Sortieren nach Datum (neueste zuerst)
folders.sort(key=lambda x: x[0], reverse=True)

# -------------------------------
# Nur die neuesten N_LATEST Logs
# -------------------------------
latest_folders = folders[:N_LATEST]

# -------------------------------
# Kopieren & alte löschen
# -------------------------------
existing_files = set(os.listdir(DST_DIR))
latest_files = set()

for yyddd, folder in latest_folders:
    src_file = os.path.join(folder, f"PROCESSING_{yyddd}")
    dst_file = os.path.join(DST_DIR, f"PROCESSING_{yyddd}")
    if os.path.isfile(src_file):
        shutil.copy2(src_file, dst_file)
        latest_files.add(f"PROCESSING_{yyddd}")

# Lösche alte Dateien, die nicht in den neuesten 3 sind
for f in existing_files:
    if f not in latest_files:
        os.remove(os.path.join(DST_DIR, f))

print(f"Latest {N_LATEST} log files copied to {DST_DIR}.")
