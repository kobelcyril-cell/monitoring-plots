#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime

# --------------------------------------------------
# Zu überwachende Prozesse
# --------------------------------------------------
process_files = {
    "1 day solution": "/storage/research/aiub_u_camp/CK_ZDGNSS/BPE/ZDGNSS.RUN",
    "3 day solution": "/storage/research/aiub_u_camp/CK_ZDGNSS/BPE/ZD3D.RUN",
    "Clock densification": "/storage/research/aiub_u_camp/CK_ZDGNSS/BPE/CLKDEN.RUN",
    "Comparison": "/storage/research/aiub_u_camp/CK_ZDGNSS/BPE/CMPSOL.RUN",
    "PPP": "/storage/research/aiub_u_camp/CK_ZDGNSS/BPE/PPP.RUN",
    "Station Network test": "/storage/research/aiub_u_camp/CK_ZDGNSS_TEST/BPE/ZDGNSS.RUN",
}

status = {"updated": datetime.now().isoformat()}

# --------------------------------------------------
# Dateien parsen
# --------------------------------------------------
for proc_name, path in process_files.items():
    proc_status = []

    # --------------------------------------------------
    # Prozessfile fehlt
    # --------------------------------------------------
    if not os.path.exists(path):
        proc_status.append({
            "session_id": "N/A",
            "status": "missing",
            "tasks": [],
            "progress": 0
        })
        status[proc_name] = proc_status
        continue

    with open(path, "r") as f:
        lines = f.readlines()

    session_id = None
    session_status = None
    tasks = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # --------------------------------------------------
        # Neue Session
        # --------------------------------------------------
        if line.startswith("Session"):

            # vorherige Session abschliessen
            if session_id is not None:
                if session_status in ("finished", "error"):
                    progress = 100
                else:
                    total = len(tasks)
                    done = sum(1 for t in tasks if t["status"] == "finished")
                    progress = int(100 * done / total) if total else 0

                proc_status.append({
                    "session_id": session_id,
                    "status": session_status,
                    "tasks": tasks,
                    "progress": progress
                })
                tasks = []

            # neue Session parsen
            parts = line.replace(":", "").split()
            session_id = parts[1]
            session_status = "running"  # default

            # explizite Session-Endzustände erkennen
            if len(parts) >= 3:
                st = parts[2].lower()
                if st in ("error", "finished"):
                    session_status = st

        # --------------------------------------------------
        # Task-Zeilen (nur wenn Session NICHT error)
        # --------------------------------------------------
        elif session_status != "error" \
             and not line.startswith("Status of") \
             and not line.startswith("-"):

            parts = line.split()
            if len(parts) >= 4:
                tasks.append({
                    "id": parts[0],
                    "name": parts[1],
                    "extra": parts[2],
                    "status": parts[3]
                })

    # --------------------------------------------------
    # Letzte Session abschliessen
    # --------------------------------------------------
    if session_id is not None:
        if session_status in ("finished", "error"):
            progress = 100
        else:
            total = len(tasks)
            done = sum(1 for t in tasks if t["status"] == "finished")
            progress = int(100 * done / total) if total else 0

        proc_status.append({
            "session_id": session_id,
            "status": session_status,
            "tasks": tasks,
            "progress": progress
        })

    status[proc_name] = proc_status

# --------------------------------------------------
# JSON schreiben
# --------------------------------------------------
out_file = "/storage/homefs/ck18y530/monitoring-plots/status.json"
with open(out_file, "w") as f:
    json.dump(status, f, indent=2)
