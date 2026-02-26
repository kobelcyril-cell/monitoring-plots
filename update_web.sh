#!/bin/bash
# Script: update_web_with_satclk.sh
# Zweck: Plots + Satellite Clock Completeness automatisch pushen

# ---------------------------------------------
# Basis-Ordner
MSC_BASE="/storage/research/aiub_u_camp/CK_ZDGNSS/MSC"
GIT_BASE="$HOME/monitoring-plots"
SATCLK_FOLDER="$GIT_BASE/satclk"

mkdir -p "$SATCLK_FOLDER"

# ---------------------------------------------
# 1) SAT_CLOCK_COMPLETENESS files kopieren
echo "Copying sat_clock_completeness files..."
for folder in "$MSC_BASE"/MSC_*; do
    if [ -d "$folder" ]; then
        cp "$folder"/sat_clock_completeness_*.txt "$SATCLK_FOLDER/" 2>/dev/null
    fi
done
echo "Copy complete."

# ---------------------------------------------
# 2) JS-Datei für HTML erstellen
JS_FILE="$GIT_BASE/satclk_list.js"
echo "Generating JS file for HTML links..."
echo "const satclk_files = [" > "$JS_FILE"
for f in "$SATCLK_FOLDER"/*.txt; do
    fname=$(basename "$f")
    echo "    \"$fname\"," >> "$JS_FILE"
done
echo "];" >> "$JS_FILE"
echo "JS file generated: $JS_FILE"

# ---------------------------------------------
# 3) Alte JS/Plots generieren (bestehendes update_web.sh)
cd "$GIT_BASE" || exit 1

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

# ---------------------------------------------
# 4) Git Lockfile prüfen
LOCKFILE="$GIT_BASE/.git/index.lock"
if [ -f "$LOCKFILE" ]; then
    echo "Lockfile exists, removing..."
    rm -f "$LOCKFILE"
fi

# ---------------------------------------------
# 5) Git add/commit/push
git add plots/latest/* plots/comparisons/* plots/ppp/* plots/runtime/* \
    index.html plots_list.js comparisons_list.js ppp_list.js runtime_list.js \
    status.json sq_output.txt cmp_lapack/cmp_lapack_summary_table.txt \
    icpu_aiub_stats.txt satclk/* satclk_list.js

if ! git diff --cached --quiet; then
    git commit -m "Auto update plots + satclk $(date '+%Y-%m-%d %H:%M')" >/dev/null 2>&1
    git push origin main >/dev/null 2>&1
    echo "Git push complete."
else
    echo "No changes to commit."
fi
