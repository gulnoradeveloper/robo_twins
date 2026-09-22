# Results (auto-generated)

Config: `default`, seed 6. Single training/evaluation run per method; no statistical tests. Values are simulation-only.

## Table 2 analogue

| Method | ID RMSE (rad) | OOD RMSE (rad) | Aggregate MAE (scaled) | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | ID 95% width (rad) | Sync. error ID | Sync. error OOD |
|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 0.056 | 0.127 | 0.480 | 90.5 | 70.0 | 0.045 | 0.136 | 0.743 | 1.445 |
| Data-only | 0.020 | 0.034 | 0.134 | 93.5 | 68.0 | 0.076 | 0.037 | 0.101 | 0.223 |
| Hybrid without UQ | 0.022 | 0.084 | 0.170 | 94.7 | 62.5 | 0.111 | 0.044 | 0.245 | 0.377 |
| Hybrid without mode awareness | 0.020 | 0.093 | 0.190 | 71.5 | 43.0 | 0.219 | 0.017 | 0.681 | 0.391 |
| Proposed configuration | 0.020 | 0.092 | 0.186 | 73.2 | 41.6 | 0.207 | 0.016 | 0.259 | 0.372 |

## Table 3 analogue (proposed vs. each baseline)

| Baseline | ID RMSE red. (%) | OOD RMSE red. (%) | Agg. MAE red. (%) | Sync. error red. (%, ID) | ID 95% cov. gain (pp) |
|---|---|---|---|---|---|
| Physics-only | 64.1 | 27.4 | 61.2 | 65.1 | -17.3 |
| Data-only | 0.4 | -169.3 | -38.7 | -156.5 | -20.3 |
| Hybrid without UQ | 10.5 | -9.4 | -9.2 | -5.7 | -21.5 |
| Hybrid without mode awareness | 0.3 | 0.5 | 2.1 | 61.9 | +1.7 |

Single-state twin step latency (proposed, CPU): 0.85 ms
