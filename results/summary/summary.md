# Summary over 7 seeds (mean ± SD across seeds; paired seed-level CIs are in results/paired_stats.json)

| Method | ID RMSE (rad) | OOD RMSE (rad) | Agg. MAE | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | OOD ECE | ID width (rad) | ID NLL | OOD NLL | Sync ID | Sync OOD | EnKF ms/step |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 0.057 ± 0.006 | 0.120 ± 0.011 | 0.493 ± 0.035 | 93.7 ± 2.9 | 72.7 ± 5.4 | 0.053 ± 0.025 | 0.213 ± 0.052 | 0.149 ± 0.013 | -2.55 ± 0.12 | -0.42 ± 0.56 | 0.446 ± 0.137 | 1.214 ± 0.523 | 6.9 ± 0.5 |
| Data-only | 0.015 ± 0.004 | 0.038 ± 0.004 | 0.140 ± 0.010 | 94.9 ± 2.0 | 71.7 ± 6.9 | 0.097 ± 0.036 | 0.200 ± 0.068 | 0.042 ± 0.007 | -3.39 ± 0.25 | -0.63 ± 0.91 | 0.097 ± 0.007 | 0.183 ± 0.034 | 1.4 ± 0.2 |
| Hybrid without UQ | 0.026 ± 0.010 | 0.064 ± 0.014 | 0.162 ± 0.011 | 95.3 ± 1.9 | 66.8 ± 6.1 | 0.135 ± 0.034 | 0.236 ± 0.057 | 0.051 ± 0.010 | -2.98 ± 0.75 | 6.87 ± 4.42 | 0.272 ± 0.066 | 3.020 ± 6.442 | 8.6 ± 0.9 |
| Hybrid without mode awareness | 0.024 ± 0.009 | 0.073 ± 0.013 | 0.177 ± 0.014 | 72.8 ± 1.9 | 43.0 ± 2.0 | 0.211 ± 0.022 | 0.446 ± 0.015 | 0.016 ± 0.002 | -3.37 ± 0.20 | 12.57 ± 7.37 | 0.304 ± 0.167 | 0.407 ± 0.059 | 9.4 ± 1.0 |
| Proposed configuration | 0.024 ± 0.010 | 0.073 ± 0.013 | 0.175 ± 0.017 | 73.1 ± 2.6 | 40.5 ± 2.3 | 0.208 ± 0.025 | 0.465 ± 0.019 | 0.016 ± 0.002 | -3.38 ± 0.37 | 12.87 ± 4.93 | 0.244 ± 0.015 | 0.393 ± 0.061 | 9.4 ± 0.7 |

## Relative reduction of the proposed model vs. each baseline (percent; from seed means) and number of seeds (of 7) in which it is better

| Baseline | ID RMSE | OOD RMSE | Agg. MAE | Sync ID | Sync OOD | ID 95% cov. gain (pp) | wins ID RMSE | wins OOD RMSE | wins Sync ID | wins Sync OOD |
|---|---|---|---|---|---|---|---|---|---|---|
| Physics-only | 58.2 | 39.2 | 64.5 | 45.4 | 67.6 | -20.6 | 7 | 7 | 7 | 7 |
| Data-only | -62.8 | -94.1 | -24.9 | -151.0 | -114.8 | -21.8 | 1 | 0 | 0 | 0 |
| Hybrid without UQ | 8.1 | -14.6 | -8.3 | 10.5 | 87.0 | -22.3 | 4 | 0 | 5 | 6 |
| Hybrid without mode awareness | 2.2 | 0.4 | 0.9 | 19.7 | 3.5 | +0.3 | 6 | 4 | 5 | 7 |

Single-state twin step latency (proposed): 0.79 ± 0.08 ms (CPU)
