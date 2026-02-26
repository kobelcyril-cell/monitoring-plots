#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
from datetime import datetime, timedelta
import os
from collections import defaultdict
from statistics import mean

# ------------------------------------------------------------
# Konfiguration
# ------------------------------------------------------------

BASE_DIR = "/storage/homefs/ck18y530/monitoring-plots"
OUTPUT_FILE = os.path.join(BASE_DIR, "icpu_aiub_stats.txt")
HISTORY_FILE = os.path.join(BASE_DIR, "icpu_aiub_history.txt")

ALIASES = {
    "ck18y530": "Cyril",
    "l_code_f": "Code (final)",
    "l_hpfaiu": "Daniel",
    "et25m288": "Edgar",
    "l_code"  : "Code",
    "l_code_s": "Code (SLR)",
    "l_code_r": "Code (rapid)",
    "ml18j210": "Martin",
    "lg19a108": "Linda",
    "dach"    : "Rolf",
    "am25w016": "Alexandra",
    "l_ggsp"  : "ggsp",
}

BAR_WIDTH = 40
WEEK_DELTA = timedelta(days=7)

# ------------------------------------------------------------
# squeue ausführen
# ------------------------------------------------------------

try:
    result = subprocess.run(
        '/bin/bash -l -c "squeue --partition=icpu-aiub"',
        shell=True,
        capture_output=True,
        text=True,
        check=True
    )
    raw_output = result.stdout

    marker = "tstdsk skipped for non-interactive shells"
    if marker in raw_output:
        raw_output = raw_output.split(marker, 1)[1].lstrip()

except Exception as e:
    raw_output = f"Error running squeue: {e}"

# ------------------------------------------------------------
# Aktuellen Stand parsen
# ------------------------------------------------------------

running = defaultdict(int)
pending = defaultdict(int)

lines = raw_output.strip().split("\n")

if len(lines) > 1:
    lines = lines[1:]

filtered_lines = []

for line in lines:
    stripped = line.strip()

    # Leere Zeilen überspringen
    if not stripped:
        continue

    # Befehlsecho überspringen
    if stripped.startswith("squeue"):
        continue

    # Header-Zeile überspringen
    if stripped.startswith("JOBID"):
        continue

    filtered_lines.append(line)

lines = filtered_lines

for line in lines:
    parts = line.split()
    if len(parts) < 8:
        continue

    user = parts[3]
    nodelist = parts[-1]

    if nodelist.startswith("bnode"):
        running[user] += 1
    else:
        pending[user] += 1

now = datetime.now()

# ------------------------------------------------------------
# History laden
# ------------------------------------------------------------

history = defaultdict(list)

if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(";")
            if len(parts) != 4:
                continue
            ts, user, r, p = parts
            dt = datetime.fromisoformat(ts)
            history[user].append((dt, int(r), int(p)))

# Neue Messung anhängen
for user in set(running.keys()) | set(pending.keys()):
    history[user].append((now, running[user], pending[user]))

# ------------------------------------------------------------
# Auf letzte 7 Tage begrenzen
# ------------------------------------------------------------

cutoff = now - WEEK_DELTA

for user in list(history.keys()):
    history[user] = [e for e in history[user] if e[0] >= cutoff]
    if not history[user]:
        del history[user]

# History neu schreiben
os.makedirs(BASE_DIR, exist_ok=True)

with open(HISTORY_FILE, "w") as f:
    for user in history:
        for dt, r, p in history[user]:
            f.write(f"{dt.isoformat()};{user};{r};{p}\n")

# ------------------------------------------------------------
# Stundenaggregation
# ------------------------------------------------------------

def hourly_aggregate(entries):
    buckets = defaultdict(list)

    for dt, r, p in entries:
        hour = dt.replace(minute=0, second=0, microsecond=0)
        buckets[hour].append((r, p))

    hours_sorted = sorted(buckets.keys())

    result = []
    for h in hours_sorted:
        rs = [x[0] for x in buckets[h]]
        ps = [x[1] for x in buckets[h]]
        result.append((h, mean(rs), mean(ps)))

    return result

def bar(value, max_value):
    if max_value == 0:
        return ""
    length = int((value / max_value) * BAR_WIDTH)
    return "█" * length

# ------------------------------------------------------------
# Output schreiben
# ------------------------------------------------------------

with open(OUTPUT_FILE, "w") as f:

    # ========================================================
    # 1) AKTUELLER STATUS
    # ========================================================

    f.write("icpu-aiub Partition – CURRENT STATUS\n")
    f.write(f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("=" * 80 + "\n\n")

    total_running = sum(running.values())
    total_pending = sum(pending.values())

    f.write(f"TOTAL RUNNING: {total_running}\n")
    f.write(f"TOTAL PENDING: {total_pending}\n\n")

    f.write("Per User:\n")
    f.write("-" * 80 + "\n")

    all_users = sorted(set(running.keys()) | set(pending.keys()))

    for user in all_users:
        alias = ALIASES.get(user, user)
        f.write(
            f"{alias:12s} ({user:10s})  "
            f"RUNNING: {running[user]:2d}   "
            f"PENDING: {pending[user]:2d}\n"
        )

    # ========================================================
    # 2) WOCHENSTATISTIK
    # ========================================================

    f.write("\n\n")
    f.write("Weekly statistics (last 7 days, 1h mean values)\n")
    f.write("=" * 80 + "\n\n")

    for user in sorted(history.keys()):
        alias = ALIASES.get(user, user)
        hourly = hourly_aggregate(history[user])

        if not hourly:
            continue

        runs = [x[1] for x in hourly]
        pends = [x[2] for x in hourly]

        max_run = max(runs)
        max_pen = max(pends)

        f.write(f"{alias} ({user})\n")
        f.write("-" * 80 + "\n")
        f.write(f"Ø RUNNING: {mean(runs):.2f}\n")
        f.write(f"Ø PENDING: {mean(pends):.2f}\n")
        f.write(f"MAX RUNNING: {max_run:.2f}\n")
        f.write(f"MAX PENDING: {max_pen:.2f}\n\n")

        f.write("RUNNING history:\n")
        for h, r, _ in hourly[-168:]:
            f.write(f"{h.strftime('%d.%m %Hh')} | {bar(r, max_run)} ({r:.1f})\n")

        f.write("\nPENDING history:\n")
        for h, _, p in hourly[-168:]:
            f.write(f"{h.strftime('%d.%m %Hh')} | {bar(p, max_pen)} ({p:.1f})\n")

        f.write("\n\n")
