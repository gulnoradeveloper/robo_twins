# Results (auto-generated)

Config: `default`, seed 2. Single training/evaluation run per method; no statistical tests. Values are simulation-only.

## Table 2 analogue

| Method | ID RMSE (rad) | OOD RMSE (rad) | Aggregate MAE (scaled) | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | ID 95% width (rad) | Sync. error ID | Sync. error OOD |
|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 0.064 | 0.120 | 0.502 | 90.0 | 69.4 | 0.036 | 0.133 | 0.395 | 0.706 |
| Data-only | 0.015 | 0.037 | 0.144 | 92.3 | 71.2 | 0.060 | 0.040 | 0.091 | 0.132 |
| Hybrid without UQ | 0.031 | 0.072 | 0.172 | 93.5 | 68.2 | 0.110 | 0.059 | 0.233 | 0.340 |
| Hybrid without Mode Awareness | 0.037 | 0.078 | 0.188 | 69.3 | 42.7 | 0.251 | 0.018 | 0.245 | 0.356 |
| Proposed Framework | 0.036 | 0.079 | 0.196 | 69.7 | 37.6 | 0.243 | 0.019 | 0.253 | 0.341 |

## Table 3 analogue (proposed vs. each baseline)

| Baseline | ID RMSE red. (%) | OOD RMSE red. (%) | Agg. MAE red. (%) | Sync. error red. (%, ID) | ID 95% cov. gain (pp) |
|---|---|---|---|---|---|
| Physics-only | 44.0 | 34.0 | 61.0 | 35.9 | -20.3 |
| Data-only | -133.5 | -113.1 | -36.1 | -178.8 | -22.6 |
| Hybrid without UQ | -16.5 | -10.5 | -14.0 | -8.7 | -23.9 |
| Hybrid without Mode Awareness | 1.0 | -1.8 | -4.4 | -3.6 | +0.4 |

Single-state twin step latency (proposed, CPU): 0.77 ms
