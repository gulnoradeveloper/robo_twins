# Results (auto-generated)

Config: `default`, seed 5. Single training/evaluation run per method; no statistical tests. Values are simulation-only.

## Table 2 analogue

| Method | ID RMSE (rad) | OOD RMSE (rad) | Aggregate MAE (scaled) | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | ID 95% width (rad) | Sync. error ID | Sync. error OOD |
|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 0.049 | 0.110 | 0.452 | 97.9 | 82.6 | 0.096 | 0.171 | 0.442 | 0.804 |
| Data-only | 0.013 | 0.042 | 0.135 | 97.5 | 83.7 | 0.157 | 0.056 | 0.101 | 0.160 |
| Hybrid without UQ | 0.014 | 0.066 | 0.146 | 97.1 | 75.5 | 0.172 | 0.063 | 0.285 | 1.136 |
| Hybrid without mode awareness | 0.016 | 0.074 | 0.167 | 74.9 | 45.7 | 0.199 | 0.016 | 0.245 | 0.379 |
| Proposed configuration | 0.016 | 0.074 | 0.163 | 75.7 | 41.9 | 0.190 | 0.016 | 0.244 | 0.353 |

## Table 3 analogue (proposed vs. each baseline)

| Baseline | ID RMSE red. (%) | OOD RMSE red. (%) | Agg. MAE red. (%) | Sync. error red. (%, ID) | ID 95% cov. gain (pp) |
|---|---|---|---|---|---|
| Physics-only | 67.1 | 33.1 | 63.8 | 44.8 | -22.2 |
| Data-only | -20.8 | -75.9 | -20.9 | -141.8 | -21.8 |
| Hybrid without UQ | -17.8 | -11.2 | -11.8 | 14.6 | -21.4 |
| Hybrid without mode awareness | 1.1 | 0.8 | 2.4 | 0.4 | +0.8 |

Single-state twin step latency (proposed, CPU): 0.86 ms
