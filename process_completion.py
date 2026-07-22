#!/usr/bin/env python3

import os
import re
from datetime import datetime, timedelta

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches

# ==========================
# SETTINGS
# ==========================
DATA_DIR = "/storage/research/aiub_u_camp/CK_ZDGNSS/BPE"
OUTPUT_FILE = "/storage/homefs/ck18y530/monitoring-plots/plots/completion/process_completion.png"

PATTERN = r"([A-Z0-9]+)(\d{5})0\.FINISHED"

PROCESS_NAMES = {
    "PPP": "PPP",
    "CLKDEN": "Clock densification",
    "ZD3D": "3 day solution",
    "ZDGNSS": "1 day solution",
    "CMPSOL": "Comparison"
}

# ==========================
# yyddd -> datetime
# ==========================
def yyddd_to_date(yyddd):
    yy = int(yyddd[:2])
    ddd = int(yyddd[2:])
    year = 2000 + yy
    return datetime(year, 1, 1) + timedelta(days=ddd - 1)

# ==========================
# Parse directory
# ==========================
process_set = set()
date_set = set()
data = {}

for fname in os.listdir(DATA_DIR):

    match = re.match(PATTERN, fname)
    if not match:
        continue

    process = match.group(1)
    date = yyddd_to_date(match.group(2))

    process_set.add(process)
    date_set.add(date)

    data[(process, date)] = 1

processes = sorted(process_set)
dates = sorted(date_set)

# ==========================
# Build matrix
# ==========================
matrix = np.zeros((len(processes), len(dates)))

for i, p in enumerate(processes):
    for j, d in enumerate(dates):
        if (p, d) in data:
            matrix[i, j] = 1

# ==========================
# Plot
# ==========================
plt.figure(figsize=(14, 6))

cmap = ListedColormap(["red", "green"])

im = plt.imshow(
    matrix,
    aspect="auto",
    origin="lower",
    cmap=cmap,
    vmin=0,
    vmax=1
)

plt.xticks(
    np.arange(len(dates)),
    [d.strftime("%y%j") for d in dates],
    rotation=90
)

plt.yticks(
    np.arange(len(processes)),
    [PROCESS_NAMES.get(p, p) for p in processes]
)

plt.xlabel("Date")
plt.ylabel("Process")

ax = plt.gca()
ax.set_axisbelow(True)

# horizontale Linien (zwischen Prozessen)
ax.set_yticks(np.arange(len(processes)+1) - 0.5, minor=True)

# vertikale Linien (zwischen Tagen)
ax.set_xticks(np.arange(len(dates)+1) - 0.5, minor=True)

ax.grid(which="minor", color="lightgray", linestyle="-", linewidth=0.5)

ax.tick_params(which="minor", bottom=False, left=False)

# Legende
red_patch = mpatches.Patch(color="red", label="missing")
green_patch = mpatches.Patch(color="green", label="finished")
plt.legend(handles=[green_patch, red_patch], loc="upper right")

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=300)
plt.close()

print("Plot gespeichert:", OUTPUT_FILE)
