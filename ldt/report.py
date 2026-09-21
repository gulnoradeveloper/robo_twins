"""Turn results.json into markdown tables (Table-2 / Table-3 analogues) and a calibration figure."""
from __future__ import annotations
import json
import numpy as np
from .models import KINDS, LABELS


def _pooled(r, key):
    return 0.5 * (r["test_id"][key] + r["test_ood"][key])


def table2(res) -> str:
    hdr = ("| Method | ID RMSE (rad) | OOD RMSE (rad) | Aggregate MAE (scaled) | ID 95% cov. (%) | OOD 95% cov. (%) "
           "| ID ECE | ID 95% width (rad) | Sync. error ID | Sync. error OOD |\n|---|---|---|---|---|---|---|---|---|---|\n")
    rows = ""
    for k in KINDS:
        r = res[k]
        rows += (f"| {LABELS[k]} | {r['test_id']['rmse']:.3f} | {r['test_ood']['rmse']:.3f} | {_pooled(r, 'mae_std'):.3f} "
                 f"| {100 * r['test_id']['cov95']:.1f} | {100 * r['test_ood']['cov95']:.1f} | {r['test_id']['ece']:.3f} "
                 f"| {r['test_id']['width95']:.3f} | {r['test_id']['sync_error']:.3f} | {r['test_ood']['sync_error']:.3f} |\n")
    return hdr + rows


def table3(res) -> str:
    p = res["proposed"]
    def red(base, get):
        b, a = get(res[base]), get(p)
        return 100 * (b - a) / b
    hdr = ("| Baseline | ID RMSE red. (%) | OOD RMSE red. (%) | Agg. MAE red. (%) | Sync. error red. (%, ID) | ID 95% cov. gain (pp) |\n"
           "|---|---|---|---|---|---|\n")
    rows = ""
    for k in KINDS[:-1]:
        rows += (f"| {LABELS[k]} | {red(k, lambda r: r['test_id']['rmse']):.1f} | {red(k, lambda r: r['test_ood']['rmse']):.1f} "
                 f"| {red(k, lambda r: _pooled(r, 'mae_std')):.1f} | {red(k, lambda r: r['test_id']['sync_error']):.1f} "
                 f"| {100 * (p['test_id']['cov95'] - res[k]['test_id']['cov95']):+.1f} |\n")
    return hdr + rows


def write_reports(res, out_dir, cfg):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    md = ("# Results (auto-generated)\n\n"
          f"Config: `{cfg.get('name', '?')}`, seed {cfg['seed']}. Single training/evaluation run per method; "
          "no statistical tests. Values are simulation-only.\n\n## Table 2 analogue\n\n" + table2(res) +
          "\n## Table 3 analogue (proposed vs. each baseline)\n\n" + table3(res) +
          f"\nSingle-state twin step latency (proposed, CPU): {res['latency_ms_single_twin_step']:.2f} ms\n")
    open(f"{out_dir}/results.md", "w").write(md)
    fig, ax = plt.subplots(figsize=(5, 4.5))
    L = [float(k) for k in res["proposed"]["test_id"]["coverage"]]
    ax.plot([0.45, 1], [0.45, 1], "--", label="Ideal")
    for split, lab in (("test_id", "Empirical (ID)"), ("test_ood", "Empirical (OOD)")):
        ax.plot(L, list(res["proposed"][split]["coverage"].values()), "o-", label=lab)
    ax.set_xlabel("Nominal coverage"); ax.set_ylabel("Empirical coverage"); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(f"{out_dir}/calibration_curve.png", dpi=150)
