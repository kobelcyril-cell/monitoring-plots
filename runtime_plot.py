#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import AutoMinorLocator

# ------------------------------------------------------------
# Konfiguration
# ------------------------------------------------------------
LOG_DIR = "/storage/homefs/ck18y530/perl/LOG"
OUTPUT_DIR = "/storage/homefs/ck18y530/monitoring-plots/plots/runtime"
OUTPUT_FILE = "bpe_runtime_last30days.png"

# Debug ein/aus
DEBUG = False

# Prozess-IDs und gewünschte Legendenbeschriftung
PROCESSES = {
    "ZDG":    "1-Day solution",
    "ZD3D":   "3-Day solution",
    "CLKDEN": "Clock densification",
    "CMP":    "Comparison",
    "PPP":    "PPP",
}

PLOT_GROUPS = {
    "solutions": {
        "title": "GNSS processing",
        "processes": ["ZDG", "ZD3D", "CLKDEN"],
        "outfile": "runtime_solutions.png",
    },
    "comparison": {
        "title": "Comparison / PPP",
        "processes": ["CMP", "PPP"],
        "outfile": "runtime_comparison.png",
    },
}


FONT_SIZE = 14
DAYS_BACK = 30


def dbg(msg):
    if DEBUG:
        print(msg)


# ------------------------------------------------------------
# Hilfsfunktionen
# ------------------------------------------------------------
def parse_start_time(line, fname=None):
    """ Extrahiert den Zeitstempel aus der ersten Zeile: [YYYY-MM-DD HH:MM:SS] """
    m = re.search(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
    if not m:
        dbg(f"[DEBUG][{fname}] Keine Startzeit gefunden in Zeile: {line.strip()}")
        return None
    ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
    dbg(f"[DEBUG][{fname}] Startzeit aus Zeile: {line.strip()}")
    dbg(f"[DEBUG][{fname}] → Startzeit = {ts}")
    return ts

def parse_end_time(lines, fname=None):
    """
    Sucht die letzte relevante Zeile vor der Trennlinie.
    Nur 'BPE finished at ...' ist gültig.
    """
    for line in reversed(lines):
        line = line.strip()

        if line.startswith("----") or not line:
            continue

        if "BPE finished at" in line:
            dbg(f"[DEBUG][{fname}] Endzeit aus Zeile: {line}")
            m = re.search(
                r"BPE finished at (\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2})",
                line,
            )
            if not m:
                dbg(f"[DEBUG][{fname}] Regex für Endzeit fehlgeschlagen")
                return None

            ts = datetime.strptime(m.group(1), "%d-%b-%Y %H:%M:%S")
            dbg(f"[DEBUG][{fname}] → Endzeit = {ts}")
            return ts

        if "BPE error" in line or "User script error" in line:
            dbg(f"[DEBUG][{fname}] Fehler erkannt in Zeile: {line}")
            return None

        dbg(f"[DEBUG][{fname}] Letzte relevante Zeile ist kein Finish/Error: {line}")
        break

    dbg(f"[DEBUG][{fname}] Keine gültige Endzeit gefunden")
    return None


def yyddd_to_date(yyddd):
    """
    Wandelt YYDDD → datetime
    """
    yy = int(yyddd[:2])
    ddd = int(yyddd[2:])
    year = 2000 + yy
    return datetime(year, 1, 1) + timedelta(days=ddd - 1)


# ------------------------------------------------------------
# 1. Alle Files je Prozess einsammeln
# ------------------------------------------------------------
files_by_proc = {pid: {} for pid in PROCESSES}

pattern = re.compile(r"^([A-Z0-9]+)(\d{5})\.log$")

for fname in os.listdir(LOG_DIR):
    m = pattern.match(fname)
    if not m:
        continue

    pid, yyddd = m.groups()
    if pid not in PROCESSES:
        continue

    files_by_proc[pid][yyddd] = os.path.join(LOG_DIR, fname)

# ------------------------------------------------------------
# 2. Global neustes Datum bestimmen
# ------------------------------------------------------------
all_dates = []
for proc_files in files_by_proc.values():
    for yyddd in proc_files:
        all_dates.append(yyddd_to_date(yyddd))

if not all_dates:
    raise RuntimeError("Keine passenden Logfiles gefunden.")

latest_date = max(all_dates)
start_date = latest_date - timedelta(days=DAYS_BACK)

date_axis = [
    start_date + timedelta(days=i)
    for i in range((latest_date - start_date).days + 1)
]

x_labels = [d.strftime("%y/%j") for d in date_axis]

# ------------------------------------------------------------
# 3. Laufzeiten extrahieren
# ------------------------------------------------------------
runtime = {pid: {} for pid in PROCESSES}

for pid, proc_files in files_by_proc.items():
    for yyddd, path in proc_files.items():
        day = yyddd_to_date(yyddd)
        if not (start_date <= day <= latest_date):
            continue

        fname = os.path.basename(path)
        dbg(f"\n[DEBUG] Verarbeite File: {fname}")

        try:
            with open(path, "r") as f:
                lines = f.readlines()
        except OSError as e:
            dbg(f"[DEBUG][{fname}] Datei konnte nicht gelesen werden: {e}")
            continue

        if not lines:
            dbg(f"[DEBUG][{fname}] Datei ist leer")
            continue

        start_time = parse_start_time(lines[0], fname=fname)
        end_time = parse_end_time(lines, fname=fname)

        if start_time and end_time:
            if end_time > start_time:
                duration = (end_time - start_time).total_seconds() / 60.0
                runtime[pid][day] = duration
                dbg(f"[DEBUG][{fname}] Laufzeit = {duration:.2f} Minuten")
            else:
                dbg(f"[DEBUG][{fname}] Endzeit < Startzeit → ignoriert")
        else:
            dbg(f"[DEBUG][{fname}] Keine Laufzeit bestimmt")

# ------------------------------------------------------------
# 4. Plot
# ------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

for group_name, cfg in PLOT_GROUPS.items():
    plt.figure(figsize=(14, 6))

    for pid in cfg["processes"]:
        if pid not in PROCESSES:
            continue

        label = PROCESSES[pid]

        x = []
        y = []
        missing_x = []
        missing_y = []

        for d in date_axis:
            x.append(d)

            if d in runtime[pid]:
                y.append(runtime[pid][d])
            else:
                y.append(np.nan)
                missing_x.append(d)
                missing_y.append(0)

        # Linie
        plt.plot(x, y, marker="o", label=label)

        # Marker für fehlende Werte
        plt.scatter(missing_x, missing_y, marker="x")

    # X-Achse formatieren
    plt.xticks(
        ticks=date_axis,
        labels=[d.strftime("%y/%j") for d in date_axis],
        rotation=45,
        fontsize=FONT_SIZE
    )

    plt.xlabel("Day", fontsize=FONT_SIZE)
    plt.ylabel("[minutes]", fontsize=FONT_SIZE)
    plt.title(cfg["title"], fontsize=FONT_SIZE)
    plt.yticks(fontsize=FONT_SIZE)
    plt.legend(fontsize=FONT_SIZE)
    ax = plt.gca()

    # Major grid (wie bisher)
    ax.grid(True, which="major", linewidth=0.8)

    # Minor ticks aktivieren
    ax.yaxis.set_minor_locator(AutoMinorLocator(4))   # feinere Y-Auflösung

    # Minor grid (feiner, heller)
    ax.grid(True, which="minor", linewidth=0.4, linestyle="--", alpha=0.6)

    plt.tight_layout()

    out_path = os.path.join(OUTPUT_DIR, cfg["outfile"])
    plt.savefig(out_path, dpi=150)
    plt.close()

    dbg(f"[DEBUG] Plot gespeichert: {out_path}")

# ------------------------------------------------------------
# DEBUG: geplottete Datenreihen ausgeben
# ------------------------------------------------------------
if DEBUG:
    print("\n[DEBUG] Geplottete Datenreihen:")

    for pid, label in PROCESSES.items():
        print(f"\n[DEBUG] Prozess {pid} ({label})")
        print("Date (YY/DDD) | datetime           | Runtime [min]")
        print("-" * 55)

        for d in date_axis:
            if d in runtime[pid]:
                rt = runtime[pid][d]
                rt_str = f"{rt:.2f}"
            else:
                rt = np.nan
                rt_str = "NaN"

            print(
                f"{d.strftime('%y/%j')}       | "
                f"{d.strftime('%Y-%m-%d')} | "
                f"{rt_str}"
            )

