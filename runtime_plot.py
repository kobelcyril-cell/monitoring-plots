#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime
import matplotlib.pyplot as plt

# ============================================================
# Konfiguration
# ============================================================

OUT_DIR = "/storage/research/aiub_u_camp/CK_ZDGNSS/BPE"

OUT_FILES = {
    "ZDGNSS": "ZDGNSS.OUT",
    "ZD3D":   "ZD3D.OUT",
    "CLKDEN": "CLKDEN.OUT",
    "PPP":    "PPP.OUT",
    "CMPSOL": "CMPSOL.OUT",
}

# frei anpassbare Plot-Namen
PROCESS_LABELS = {
    "ZDGNSS": "1-Day solution",
    "ZD3D":   "3-Day solution",
    "CLKDEN": "Clock densification",
    "PPP":    "PPP",
    "CMPSOL": "Comparison",
}

PLOT_GROUPS = {
    "solutions": {
        "title": "GNSS processing",
        "processes": ["ZDGNSS", "ZD3D", "CLKDEN"],
        "outfile": "runtime_solutions.png",
    },
    "comparison": {
        "title": "Comparison / PPP",
        "processes": ["PPP", "CMPSOL"],
        "outfile": "runtime_comparison.png",
    },
}

DATA_FILE = "/storage/homefs/ck18y530/monitoring-plots/tmp/runtime_history.txt"
PLOT_DIR  = "/storage/homefs/ck18y530/monitoring-plots/plots/runtime"

MAX_DAYS  = 60
FONT_SIZE = 13

# ============================================================
# Regex
# ============================================================

RE_TOTAL_TIME = re.compile(r"Total Time:\s+(\d{2}):(\d{2}):(\d{2})")
RE_DATE       = re.compile(r"(\d{2}-[A-Za-z]{3}-\d{4})")

# ============================================================
# Parsing
# ============================================================

def parse_out_file(path):
    """
    Liefert (date, duration_seconds) oder (None, None)
    """
    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except OSError:
        return None, None

    duration = None
    date = None

    for line in lines:
        if duration is None:
            m = RE_TOTAL_TIME.search(line)
            if m:
                h, m_, s = map(int, m.groups())
                duration = h * 3600 + m_ * 60 + s

        if date is None:
            m = RE_DATE.search(line)
            if m:
                date = datetime.strptime(m.group(1), "%d-%b-%Y").date()

        if duration is not None and date is not None:
            break

    return date, duration

# ============================================================
# Persistenz
# ============================================================

def load_existing_entries():
    """
    Set mit (date_str, proc)
    """
    entries = set()
    if not os.path.exists(DATA_FILE):
        return entries

    with open(DATA_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 2:
                entries.add((parts[0], parts[1]))
    return entries


def append_entry(date, proc, duration):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "a") as f:
        f.write(f"{date},{proc},{duration}\n")

# ============================================================
# Plot
# ============================================================

def plot_history():
    if not os.path.exists(DATA_FILE):
        return

    data = {}
    with open(DATA_FILE, "r") as f:
        for line in f:
            date_str, proc, duration = line.strip().split(",")
            d = datetime.strptime(date_str, "%Y-%m-%d").date()
            data.setdefault(proc, []).append((d, int(duration)))

    os.makedirs(PLOT_DIR, exist_ok=True)

    for cfg in PLOT_GROUPS.values():
        plt.figure(figsize=(14, 5))

        for proc in cfg["processes"]:
            if proc not in data:
                continue

            values = sorted(data[proc])[-MAX_DAYS:]
            x = [v[0] for v in values]
            y = [v[1] / 60.0 for v in values]  # Minuten

            label = PROCESS_LABELS.get(proc, proc)
            plt.plot(x, y, marker="o", label=label)

        plt.xlabel("Date", fontsize=FONT_SIZE)
        plt.ylabel("Runtime [min]", fontsize=FONT_SIZE)
        plt.title(cfg["title"], fontsize=FONT_SIZE)
        plt.legend(fontsize=FONT_SIZE)
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        out_path = os.path.join(PLOT_DIR, cfg["outfile"])
        plt.savefig(out_path, dpi=150)
        plt.close()

# ============================================================
# Main
# ============================================================

def main():
    existing = load_existing_entries()

    for proc, fname in OUT_FILES.items():
        path = os.path.join(OUT_DIR, fname)

        date, duration = parse_out_file(path)
        if date is None or duration is None:
            continue

        key = (str(date), proc)
        if key in existing:
            continue

        append_entry(date, proc, duration)

    plot_history()


if __name__ == "__main__":
    main()
