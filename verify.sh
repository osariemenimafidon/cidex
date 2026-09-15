#!/usr/bin/env bash
# One command for the mechanical half of the verification gate.
# Rebuilds from the raw EPA files and diffs against the shipped reference.
set -uo pipefail
cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════"
echo " CIDEX verification — mechanical half"
echo "════════════════════════════════════════════════════════════"
echo
echo "▶ Rebuilding from data/raw/ ..."
for s in 01_provenance 02_harmonize_highway 03_harmonize_nonroad 04_carryover 05_combine_qa; do
  printf "  %-24s" "$s"
  if python3 "scripts/$s.py" >/dev/null 2>&1; then echo "ok"; else echo "FAILED"; exit 1; fi
done
echo
python3 scripts/10_check.py
