#!/bin/bash
# Script: update_web.sh
# Zweck: Plots automatisch pushen (latest + comparisons + ppp)

cd ~/monitoring-plots || exit 1

# --- latest Plots ---
plots_folder_latest="plots/latest"
js_file_latest="plots_list.js"

echo "const latest_plots = [" > $js_file_latest
for f in "$plots_folder_latest"/*.png; do
    fname=$(basename "$f")
    echo "    \"$fname\"," >> $js_file_latest
done
echo "];" >> $js_file_latest

# --- comparison Plots ---
plots_folder_comp="plots/comparisons"
js_file_comp="comparisons_list.js"

echo "const comparison_plots = [" > $js_file_comp
for f in "$plots_folder_comp"/*.png; do
    fname=$(basename "$f")
    echo "    \"$fname\"," >> $js_file_comp
done
echo "];" >> $js_file_comp

# --- PPP Plots ---
plots_folder_ppp="plots/ppp"
js_file_ppp="ppp_list.js"

echo "const ppp_plots = [" > $js_file_ppp
for f in "$plots_folder_ppp"/*.png; do
    fname=$(basename "$f")
    echo "    \"$fname\"," >> $js_file_ppp
done
echo "];" >> $js_file_ppp

# --- Runtime Plots ---
plots_folder_runtime="plots/runtime"
js_file_runtime="runtime_list.js"

echo "const runtime_plots = [" > $js_file_runtime
for f in "$plots_folder_runtime"/*.png; do
    fname=$(basename "$f")
    echo "    \"$fname\"," >> $js_file_runtime
done
echo "];" >> $js_file_runtime


# Pfad zum Lockfile
LOCKFILE="/storage/homefs/ck18y530/monitoring-plots/.git/index.lock"

# Prüfen und löschen, falls vorhanden
if [ -f "$LOCKFILE" ]; then
    echo "Lockfile existiert, wird gelöscht..."
    rm -f "$LOCKFILE"
fi

# --- Git: alle neuen/überschriebenen Dateien hinzufügen ---
git add plots/latest/* plots/comparisons/* plots/ppp/* plots/runtime/* index.html plots_list.js comparisons_list.js ppp_list.js runtime_list.js status.json sq_output.txt cmp_lapack/cmp_lapack_summary_table.txt


if ! git diff --cached --quiet; then
    git commit -m "Auto update plots $(date '+%Y-%m-%d %H:%M')" >/dev/null 2>&1
    git push origin main >/dev/null 2>&1
fi

