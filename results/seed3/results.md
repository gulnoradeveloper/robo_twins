# Results (auto-generated)

Config: `default`, seed 3. Single training/evaluation run per method; no statistical tests. Values are simulation-only.

## Table 2 analogue

| Method | ID RMSE (rad) | OOD RMSE (rad) | Aggregate MAE (scaled) | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | ID 95% width (rad) | Sync. error ID | Sync. error OOD |
|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 0.065 | 0.128 | 0.552 | 91.9 | 67.5 | 0.020 | 0.148 | 0.455 | 2.064 |
| Data-only | 0.014 | 0.044 | 0.160 | 94.5 | 64.2 | 0.069 | 0.039 | 0.109 | 0.156 |
| Hybrid without UQ | 0.031 | 0.069 | 0.175 | 94.5 | 60.3 | 0.114 | 0.047 | 0.268 | 17.612 |
| Hybrid without mode awareness | 0.032 | 0.076 | 0.189 | 72.9 | 42.9 | 0.215 | 0.018 | 0.268 | 0.396 |
| Proposed configuration | 0.032 | 0.076 | 0.194 | 69.5 | 39.2 | 0.241 | 0.017 | 0.254 | 0.394 |

## Table 3 analogue (proposed vs. each baseline)

| Baseline | ID RMSE red. (%) | OOD RMSE red. (%) | Agg. MAE red. (%) | Sync. error red. (%, ID) | ID 95% cov. gain (pp) |
|---|---|---|---|---|---|
| Physics-only | 50.6 | 40.3 | 64.8 | 44.3 | -22.4 |
| Data-only | -135.5 | -71.4 | -21.3 | -132.5 | -24.9 |
| Hybrid without UQ | -4.5 | -11.3 | -10.8 | 5.4 | -24.9 |
| Hybrid without mode awareness | -0.5 | -0.1 | -2.4 | 5.4 | -3.4 |

Single-state twin step latency (proposed, CPU): 0.70 ms
