#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
from datetime import datetime
import os

# Absoluter Pfad zum Output-File
output_file = "/storage/homefs/ck18y530/monitoring-plots/sq_output.txt"

try:
    # squeue über eine Login-Shell ausführen, wie im Terminal
    result = subprocess.run(
        '/bin/bash -l -c "squeue -u ck18y530"',
        shell=True,
        capture_output=True,
        text=True,
        check=True
    )
    output_text = result.stdout
    marker = "tstdsk skipped for non-interactive shells"
    if marker in output_text:
        output_text = output_text.split(marker, 1)[1].lstrip()

except subprocess.CalledProcessError as e:
    output_text = f"Error running squeue: {e}\n{e.stdout}\n{e.stderr}"

except FileNotFoundError as e:
    output_text = f"Error running squeue: {e}"

# Zeitstempel hinzufügen
timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

with open(output_file, "w") as f:
    f.write(f"[{timestamp}]\n")
    f.write(output_text)
