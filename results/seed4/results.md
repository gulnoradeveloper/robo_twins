# Results (auto-generated)

Config: `default`, seed 4. Single training/evaluation run per method; no statistical tests. Values are simulation-only.

## Table 2 analogue

| Method | ID RMSE (rad) | OOD RMSE (rad) | Aggregate MAE (scaled) | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | ID 95% width (rad) | Sync. error ID | Sync. error OOD |
|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 0.057 | 0.102 | 0.455 | 94.9 | 76.8 | 0.060 | 0.154 | 0.359 | 0.951 |
| Data-only | 0.019 | 0.034 | 0.140 | 93.7 | 75.6 | 0.090 | 0.043 | 0.091 | 0.202 |
| Hybrid without UQ | 0.044 | 0.041 | 0.157 | 92.9 | 66.6 | 0.098 | 0.036 | 0.414 | 0.429 |
| Hybrid without mode awareness | 0.032 | 0.050 | 0.159 | 72.4 | 44.4 | 0.219 | 0.018 | 0.237 | 0.404 |
| Proposed configuration | 0.032 | 0.049 | 0.155 | 75.6 | 43.1 | 0.180 | 0.018 | 0.250 | 0.400 |

## Table 3 analogue (proposed vs. each baseline)

| Baseline | ID RMSE red. (%) | OOD RMSE red. (%) | Agg. MAE red. (%) | Sync. error red. (%, ID) | ID 95% cov. gain (pp) |
|---|---|---|---|---|---|
| Physics-only | 43.9 | 51.8 | 66.0 | 30.2 | -19.2 |
| Data-only | -71.7 | -44.3 | -10.3 | -174.6 | -18.0 |
| Hybrid without UQ | 27.8 | -20.4 | 1.5 | 39.6 | -17.3 |
| Hybrid without mode awareness | 0.9 | 2.0 | 2.8 | -5.6 | +3.2 |

Single-state twin step latency (proposed, CPU): 0.69 ms
