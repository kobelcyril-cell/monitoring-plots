#!/usr/bin/env python3

import os
import re
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt

# ==========================
# SETTINGS
# ==========================
DATA_DIR = "/storage/homefs/ck18y530/monitoring-plots/satclk"
OUTPUT_FILE = "/storage/homefs/ck18y530/monitoring-plots/plots/latest/clock_completeness_heatmap.png"
N_LATEST = 40
PATTERN = r"sat_clock_completeness_(\d{5})\.txt"

# ==========================
# yyddd -> datetime
# ==========================
def yyddd_to_date(yyddd):
    yy = int(yyddd[:2])
    ddd = int(yyddd[2:])
    year = 2000 + yy
    return datetime(year, 1, 1) + timedelta(days=ddd - 1)

# ==========================
# Find and sort files
# ==========================
files = []
for fname in os.listdir(DATA_DIR):
    match = re.match(PATTERN, fname)
    if match:
        date = yyddd_to_date(match.group(1))
        files.append((fname, date))

if not files:
    raise RuntimeError("Keine passenden Files gefunden.")

files.sort(key=lambda x: x[1])
latest_files = files[-N_LATEST:]

# ==========================
# Parse data
# ==========================
all_sats = set()
date_list = []
data_dict = {}

for fname, date in latest_files:
    fullpath = os.path.join(DATA_DIR, fname)
    date_list.append(date)

    with open(fullpath, "r") as f:
        lines = f.readlines()

    # Header überspringen
    data_start = None
    for i, line in enumerate(lines):
        if "-----" in line:
            data_start = i + 1
            break

    if data_start is None:
        continue

    for line in lines[data_start:]:
        parts = line.split()
        if len(parts) != 2:
            continue

        sat = int(parts[0])
        comp = float(parts[1])

        all_sats.add(sat)
        data_dict[(sat, date)] = comp

# ==========================
# Build matrix
# ==========================
all_sats = sorted(all_sats)
date_list = sorted(date_list)

matrix = np.full((len(all_sats), len(date_list)), 100.0)

for i, sat in enumerate(all_sats):
    for j, date in enumerate(date_list):
        if (sat, date) in data_dict:
            matrix[i, j] = data_dict[(sat, date)]

# ==========================
# Plot heatmap
# ==========================
# ==========================
# Plot heatmap mit Annotation
# ==========================
plt.figure(figsize=(14, 8))

im = plt.imshow(matrix, aspect="auto", origin="lower")

cbar = plt.colorbar(im)
cbar.set_label("Completeness [%]")

plt.clim(90, 100)  # Fokus auf kritischen Bereich

plt.xticks(
    ticks=np.arange(len(date_list)),
    labels=[d.strftime("%y%j") for d in date_list],
    rotation=90
)

plt.yticks(
    ticks=np.arange(len(all_sats)),
    labels=all_sats
)

plt.xlabel("Date")
plt.ylabel("Satellite")
plt.title(f"Clock Completeness – last {N_LATEST} days")

# ==========================
# Annotation nur <100%
# ==========================
for i in range(matrix.shape[0]):
    for j in range(matrix.shape[1]):
        value = matrix[i, j]
        if value < 100.0:
            plt.text(
                j, i,
                f"{value:.1f}",
                ha="center",
                va="center",
                fontsize=8,
                color="white"
            )

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300)
plt.close()

print(f"Heatmap gespeichert als {OUTPUT_FILE}")

