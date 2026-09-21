# Results (auto-generated)

Config: `default`, seed 0. Single training/evaluation run per method; no statistical tests. Values are simulation-only.

## Table 2 analogue

| Method | ID RMSE (rad) | OOD RMSE (rad) | Aggregate MAE (scaled) | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | ID 95% width (rad) | Sync. error ID | Sync. error OOD |
|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 0.051 | 0.133 | 0.518 | 95.5 | 69.0 | 0.069 | 0.157 | 0.358 | 1.691 |
| Data-only | 0.010 | 0.037 | 0.137 | 95.4 | 64.6 | 0.093 | 0.035 | 0.092 | 0.217 |
| Hybrid without UQ | 0.021 | 0.060 | 0.156 | 97.1 | 60.7 | 0.159 | 0.048 | 0.232 | 0.863 |
| Hybrid without Mode Awareness | 0.020 | 0.069 | 0.162 | 74.2 | 39.2 | 0.191 | 0.013 | 0.226 | 0.535 |
| Proposed Framework | 0.017 | 0.070 | 0.164 | 74.9 | 37.6 | 0.193 | 0.013 | 0.225 | 0.522 |

## Table 3 analogue (proposed vs. each baseline)

| Baseline | ID RMSE red. (%) | OOD RMSE red. (%) | Agg. MAE red. (%) | Sync. error red. (%, ID) | ID 95% cov. gain (pp) |
|---|---|---|---|---|---|
| Physics-only | 65.9 | 47.4 | 68.4 | 37.1 | -20.6 |
| Data-only | -71.3 | -90.0 | -19.5 | -145.8 | -20.5 |
| Hybrid without UQ | 16.8 | -16.3 | -4.7 | 3.2 | -22.2 |
| Hybrid without Mode Awareness | 11.0 | -1.1 | -1.3 | 0.3 | +0.6 |

Single-state twin step latency (proposed, CPU): 0.87 ms
