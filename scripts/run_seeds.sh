#!/usr/bin/env bash
# Run the default configuration for several seeds (results/seed0, seed1, ...). ~10 min per seed on 2 CPU cores.
set -e
cd "$(dirname "$0")/.."
seeds=${*:-"0 1 2"}
for s in $seeds; do
  python scripts/run_all.py --config configs/default.json --seed "$s" --out "results/seed${s}" > "results/seed${s}.log" 2>&1
done
