#!/bin/bash
# Script: update_web.sh
# Zweck: Plots automatisch pushen

cd ~/monitoring-plots || exit 1

# Generiere plots_list.js automatisch
plots_folder="plots/latest"
js_file="plots_list.js"

echo "const plots = [" > $js_file
for f in "$plots_folder"/*.png; do
    fname=$(basename "$f")
    echo "    \"$fname\"," >> $js_file
done
echo "];" >> $js_file


# Alle neuen/überschriebenen Dateien hinzufügen
git add plots/latest/* index.html plots_list.js

# Commit mit Datum/Uhrzeit
git commit -m "Auto update plots $(date '+%Y-%m-%d %H:%M')"

# Push zum Remote-Repository
git push origin main
