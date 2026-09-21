# Results (auto-generated)

Config: `default`, seed 1. Single training/evaluation run per method; no statistical tests. Values are simulation-only.

## Table 2 analogue

| Method | ID RMSE (rad) | OOD RMSE (rad) | Aggregate MAE (scaled) | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | ID 95% width (rad) | Sync. error ID | Sync. error OOD |
|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 0.053 | 0.117 | 0.490 | 95.1 | 73.7 | 0.047 | 0.147 | 0.371 | 0.837 |
| Data-only | 0.010 | 0.034 | 0.131 | 97.5 | 74.5 | 0.134 | 0.043 | 0.095 | 0.190 |
| Hybrid without UQ | 0.017 | 0.053 | 0.155 | 97.7 | 73.5 | 0.179 | 0.063 | 0.228 | 0.382 |
| Hybrid without Mode Awareness | 0.013 | 0.071 | 0.181 | 74.1 | 43.4 | 0.186 | 0.016 | 0.225 | 0.388 |
| Proposed Framework | 0.012 | 0.069 | 0.168 | 73.0 | 42.6 | 0.203 | 0.014 | 0.221 | 0.367 |

## Table 3 analogue (proposed vs. each baseline)

| Baseline | ID RMSE red. (%) | OOD RMSE red. (%) | Agg. MAE red. (%) | Sync. error red. (%, ID) | ID 95% cov. gain (pp) |
|---|---|---|---|---|---|
| Physics-only | 78.0 | 41.5 | 65.7 | 40.4 | -22.1 |
| Data-only | -13.0 | -104.3 | -28.5 | -132.3 | -24.6 |
| Hybrid without UQ | 31.4 | -30.5 | -8.4 | 3.0 | -24.7 |
| Hybrid without Mode Awareness | 6.0 | 3.5 | 7.3 | 1.7 | -1.1 |

Single-state twin step latency (proposed, CPU): 0.80 ms
