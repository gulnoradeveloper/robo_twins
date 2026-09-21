# Summary over 3 seeds (mean ± SD across seeds; descriptive, no significance tests)

| Method | ID RMSE (rad) | OOD RMSE (rad) | Agg. MAE | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | OOD ECE | ID width (rad) | ID NLL | OOD NLL | Sync ID | Sync OOD | EnKF ms/step |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 0.056 ± 0.007 | 0.124 ± 0.009 | 0.503 ± 0.014 | 93.5 ± 3.1 | 70.7 ± 2.6 | 0.051 ± 0.017 | 0.228 ± 0.025 | 0.146 ± 0.012 | -2.54 ± 0.15 | -0.34 ± 0.39 | 0.375 ± 0.019 | 1.078 ± 0.535 | 7.2 ± 0.1 |
| Data-only | 0.012 ± 0.003 | 0.036 ± 0.002 | 0.137 ± 0.007 | 95.1 ± 2.6 | 70.1 ± 5.1 | 0.096 ± 0.037 | 0.218 ± 0.046 | 0.039 ± 0.004 | -3.57 ± 0.21 | -0.54 ± 0.84 | 0.093 ± 0.002 | 0.180 ± 0.043 | 1.4 ± 0.0 |
| Hybrid without UQ | 0.023 ± 0.007 | 0.062 ± 0.010 | 0.161 ± 0.009 | 96.1 ± 2.2 | 67.5 ± 6.4 | 0.149 ± 0.036 | 0.230 ± 0.060 | 0.057 ± 0.008 | -3.20 ± 0.78 | 5.25 ± 4.30 | 0.231 ± 0.003 | 0.528 ± 0.291 | 9.1 ± 0.1 |
| Hybrid without Mode Awareness | 0.023 ± 0.012 | 0.073 ± 0.004 | 0.177 ± 0.014 | 72.5 ± 2.8 | 41.8 ± 2.3 | 0.209 ± 0.036 | 0.453 ± 0.020 | 0.016 ± 0.002 | -3.36 ± 0.30 | 9.12 ± 1.93 | 0.232 ± 0.011 | 0.426 ± 0.096 | 9.6 ± 0.1 |
| Proposed Framework | 0.022 ± 0.013 | 0.073 ± 0.006 | 0.176 ± 0.017 | 72.5 ± 2.6 | 39.3 ± 2.9 | 0.213 ± 0.026 | 0.473 ± 0.024 | 0.015 ± 0.003 | -3.40 ± 0.42 | 10.68 ± 3.81 | 0.233 ± 0.018 | 0.410 ± 0.098 | 9.5 ± 0.1 |

## Relative reduction of the proposed model vs. each baseline (percent; from seed means) and number of seeds (of 3) in which it is better

| Baseline | ID RMSE | OOD RMSE | Agg. MAE | Sync ID | Sync OOD | ID 95% cov. gain (pp) | wins ID RMSE | wins OOD RMSE | wins Sync ID | wins Sync OOD |
|---|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 61.4 | 41.2 | 65.1 | 37.8 | 62.0 | -21.0 | 3 | 3 | 3 | 3 |
| Data-only | -81.2 | -102.5 | -28.2 | -152.0 | -127.9 | -22.6 | 0 | 0 | 0 | 0 |
| Hybrid without UQ | 5.5 | -18.1 | -9.2 | -0.9 | 22.4 | -23.6 | 2 | 0 | 2 | 2 |
| Hybrid without Mode Awareness | 4.8 | 0.1 | 0.5 | -0.6 | 3.8 | -0.0 | 3 | 1 | 2 | 3 |

Single-state twin step latency (proposed): 0.82 ± 0.05 ms (CPU)
