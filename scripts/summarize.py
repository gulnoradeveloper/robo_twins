#!/usr/bin/env python
"""Aggregate several seeds (mean +- SD across seeds) and draw the figures.

    python scripts/summarize.py --runs results/seed0 results/seed1 results/seed2 --out results/summary
Every number in the tables/figures comes from the results.json files written by scripts/run_all.py.
"""
import argparse, json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["pdf.fonttype"] = 42  # embed TrueType fonts in vector output
from _hsave import hsave
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ldt.models import KINDS, LABELS
from ldt.data import ID_RANGES

COL = {"physics": "#0072B2", "data": "#E69F00", "hybrid_nouq": "#4D4D4D", "hybrid_nomode": "#CC79A7", "proposed": "#D55E00"}  # CVD-safe, no red-green pairing (Heliyon)
MRK = {"physics": "o", "data": "s", "hybrid_nouq": "^", "hybrid_nomode": "D", "proposed": "v"}
LS = {"physics": "-", "data": "--", "hybrid_nouq": "-.", "hybrid_nomode": ":", "proposed": "-"}
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 150, "savefig.dpi": 300, "legend.frameon": False})


def shift_magnitude(cond):
    """RMS over (friction, stiffness, payload) of the distance outside the ID range in units of the ID range width."""
    if cond["split"] == "id":
        return 0.0
    s = []
    for k, (lo, hi) in ID_RANGES.items():
        s.append(max(lo - cond[k], cond[k] - hi, 0.0) / (hi - lo))
    return float(np.sqrt(np.mean(np.square(s))))


def ms(x):
    x = np.asarray(x, float)
    return float(x.mean()), float(x.std(ddof=1)) if len(x) > 1 else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", default="results/summary")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    R = [json.load(open(f"{d}/results.json")) for d in a.runs]
    D = [json.load(open(f"{d}/dataset_summary.json")) for d in a.runs]
    n = len(R)
    get = lambda k, sp, key: [r[k][sp][key] for r in R]
    S = {}
    for k in KINDS:
        s = {}
        for sp, tag in (("test_id", "id"), ("test_ood", "ood")):
            for key, name in (("rmse", "rmse"), ("mae_std", "mae"), ("cov95", "cov95"), ("cov90", "cov90"), ("ece", "ece"),
                              ("width95", "width95"), ("nll", "nll"), ("sync_error", "sync"), ("sync_joint_rmse", "sync_joint"),
                              ("enkf_ms_per_step", "enkf_ms")):
                s[f"{name}_{tag}"] = ms(get(k, sp, key))
        s["mae_pooled"] = ms([0.5 * (r[k]["test_id"]["mae_std"] + r[k]["test_ood"]["mae_std"]) for r in R])
        s["degradation_pct"] = ms([100 * (r[k]["test_ood"]["rmse"] / r[k]["test_id"]["rmse"] - 1) for r in R])
        s["per_seed"] = {key: [r[k]["test_id"]["rmse"] for r in R] for key in ("id_rmse",)}
        s["per_seed"]["ood_rmse"] = [r[k]["test_ood"]["rmse"] for r in R]
        S[k] = s
    S["latency_ms"] = ms([r["latency_ms_single_twin_step"] for r in R])
    S["n_seeds"] = n
    S["dataset_samples"] = {sp: ms([d["stats"][sp]["samples"] for d in D]) for sp in D[0]["stats"]}

    # ---- relative improvements of the proposed model (from seed-mean values) and per-seed win counts
    rel = {}
    for k in KINDS[:-1]:
        row = {}
        for name, key in (("id_rmse", "rmse_id"), ("ood_rmse", "rmse_ood"), ("mae", "mae_pooled"), ("sync_id", "sync_id"), ("sync_ood", "sync_ood")):
            b, p = S[k][key][0], S["proposed"][key][0]
            row[name] = 100 * (b - p) / b
        row["cov95_id_pp"] = 100 * (S["proposed"]["cov95_id"][0] - S[k]["cov95_id"][0])
        row["wins"] = {name: int(sum(pv < bv for pv, bv in zip(
            [r["proposed"]["test_id" if "id" in name else "test_ood"][mk] for r in R],
            [r[k]["test_id" if "id" in name else "test_ood"][mk] for r in R])))
            for name, mk in (("id_rmse", "rmse"), ("ood_rmse", "rmse"), ("sync_id", "sync_error"), ("sync_ood", "sync_error"))}
        rel[k] = row
    S["relative_improvement_of_proposed"] = rel
    json.dump(S, open(f"{a.out}/summary.json", "w"), indent=1)

    fmt = lambda t, d=3: f"{t[0]:.{d}f} ± {t[1]:.{d}f}"
    md = f"# Summary over {n} seeds (mean ± SD across seeds; paired seed-level CIs are in results/paired_stats.json)\n\n"
    md += "| Method | ID RMSE (rad) | OOD RMSE (rad) | Agg. MAE | ID 95% cov. (%) | OOD 95% cov. (%) | ID ECE | OOD ECE | ID width (rad) | ID NLL | OOD NLL | Sync ID | Sync OOD | EnKF ms/step |\n|" + "---|" * 14 + "\n"
    for k in KINDS:
        s = S[k]
        md += (f"| {LABELS[k]} | {fmt(s['rmse_id'])} | {fmt(s['rmse_ood'])} | {fmt(s['mae_pooled'])} | {100*s['cov95_id'][0]:.1f} ± {100*s['cov95_id'][1]:.1f} "
               f"| {100*s['cov95_ood'][0]:.1f} ± {100*s['cov95_ood'][1]:.1f} | {fmt(s['ece_id'])} | {fmt(s['ece_ood'])} | {fmt(s['width95_id'])} "
               f"| {fmt(s['nll_id'],2)} | {fmt(s['nll_ood'],2)} | {fmt(s['sync_id'])} | {fmt(s['sync_ood'])} | {fmt(s['enkf_ms_id'],1)} |\n")
    md += f"\n## Relative reduction of the proposed model vs. each baseline (percent; from seed means) and number of seeds (of {n}) in which it is better\n\n"
    md += "| Baseline | ID RMSE | OOD RMSE | Agg. MAE | Sync ID | Sync OOD | ID 95% cov. gain (pp) | wins ID RMSE | wins OOD RMSE | wins Sync ID | wins Sync OOD |\n|" + "---|" * 11 + "\n"
    for k in KINDS[:-1]:
        r = rel[k]
        md += (f"| {LABELS[k]} | {r['id_rmse']:.1f} | {r['ood_rmse']:.1f} | {r['mae']:.1f} | {r['sync_id']:.1f} | {r['sync_ood']:.1f} | {r['cov95_id_pp']:+.1f} "
               f"| {r['wins']['id_rmse']} | {r['wins']['ood_rmse']} | {r['wins']['sync_id']} | {r['wins']['sync_ood']} |\n")
    md += f"\nSingle-state twin step latency (proposed): {S['latency_ms'][0]:.2f} ± {S['latency_ms'][1]:.2f} ms (CPU)\n"
    open(f"{a.out}/summary.md", "w").write(md)

    def legend(ax_or_fig, **kw):
        h = [plt.Line2D([], [], color=COL[k], ls=LS[k], marker=MRK[k], ms=4, lw=1.4) for k in KINDS]
        ax_or_fig.legend(h, [LABELS[k] for k in KINDS], **kw)

    # ---- Fig. 3: RMSE vs horizon
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, sp, t in zip(axs, ("test_id", "test_ood"), ("(a) In-distribution", "(b) Out-of-distribution")):
        for k in KINDS:
            H = np.array([r[k][sp]["rmse_by_horizon"] for r in R]); x = np.arange(1, H.shape[1] + 1) * 5
            ax.plot(x, H.mean(0), color=COL[k], ls=LS[k], marker=MRK[k], ms=2.5, lw=1.3, markevery=3)
            ax.fill_between(x, H.mean(0) - H.std(0), H.mean(0) + H.std(0), color=COL[k], alpha=0.12, lw=0)
        ax.set_title(t, fontsize=8.5); ax.set_xlabel("Prediction horizon (ms)")
    axs[0].set_ylabel("Joint-position RMSE (rad)"); axs[0].set_yscale("log")
    fig.tight_layout(rect=(0, 0.13, 1, 1)); legend(fig, loc="lower center", ncol=5, fontsize=7.5)
    hsave(fig, f"{a.out}/fig3_rollout_horizon.png"); plt.close(fig)

    # ---- Fig. 4: contact-transition analysis (ID test episodes)
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9))
    T = {k: [r[k]["test_id"]["transition"] for r in R] for k in ("physics", "hybrid_nouq", "hybrid_nomode", "proposed")}
    bins = T["physics"][0]["bins"]; x = np.arange(len(bins))
    tv = np.array([t["true_rms"] for t in T["physics"]])
    axs[0].bar(x, tv.mean(0), yerr=tv.std(0), color="#8a8985", width=0.6, capsize=2, error_kw=dict(lw=0.8))
    axs[0].axhline(1.0, color="k", lw=0.6, ls=":")
    axs[0].set_xticks(x, bins); axs[0].set_xlabel("Control steps to nearest contact-mode switch"); axs[0].set_ylabel("RMS of true residual acceleration\n(relative to overall RMS)")
    axs[0].set_title("(a) Model mismatch by proximity to a switch", fontsize=8.5)
    for k in ("hybrid_nouq", "hybrid_nomode", "proposed"):
        e = np.array([t["rel_err"] for t in T[k]])
        axs[1].errorbar(x, e.mean(0), yerr=e.std(0), color=COL[k], ls=LS[k], marker=MRK[k], ms=3.5, lw=1.3, capsize=2, label=LABELS[k])
    axs[1].plot(x, tv.mean(0), color=COL["physics"], marker=MRK["physics"], ms=3.5, lw=1.3, label=LABELS["physics"] + " (predicts zero)")
    axs[1].set_xticks(x, bins); axs[1].set_xlabel("Control steps to nearest contact-mode switch"); axs[1].set_ylabel("One-step residual error (relative)")
    axs[1].set_title("(b) Residual prediction error", fontsize=8.5); axs[1].set_ylim(0, 2.4); axs[1].legend(fontsize=6.5, loc="upper right", ncol=1)
    fig.tight_layout(); hsave(fig, f"{a.out}/fig4_contact_transitions.png"); plt.close(fig)

    # ---- Fig. 5: domain shift (per-episode RMSE vs shift magnitude)
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    per = {k: [] for k in KINDS}
    for r, d in zip(R, D):
        for k in KINDS:
            for sp, key in (("test_id", "test_id"), ("test_ood", "test_ood")):
                w_ep = np.array(r[k][sp]["window_episode"]); w_r = np.array(r[k][sp]["window_rmse"])
                for e, cond in enumerate(d["conditions"][key]):
                    m = w_ep == e
                    if m.any():
                        per[k].append((shift_magnitude(cond), float(np.sqrt(np.mean(w_r[m] ** 2)))))
    edges = [-1e-9, 1e-9, 1.4, 1.8, 2.3, 10]
    labels_x = []
    for k in KINDS:
        p = np.array(per[k]); xs, ys = [], []
        for lo, hi in zip(edges[:-1], edges[1:]):
            m = (p[:, 0] > lo) & (p[:, 0] <= hi)
            if m.any():
                xs.append(p[m, 0].mean()); ys.append(p[m, 1].mean())
        ax.scatter(p[:, 0], p[:, 1], s=5, color=COL[k], alpha=0.25, lw=0)
        ax.plot(xs, ys, color=COL[k], ls=LS[k], marker=MRK[k], ms=4, lw=1.4)
    ax.set_yscale("log"); ax.set_xlabel("Shift magnitude (RMS distance outside ID range, in range widths)")
    ax.set_ylabel("Episode joint-position RMSE (rad)")
    fig.tight_layout(rect=(0, 0.16, 1, 1)); legend(fig, loc="lower center", ncol=3, fontsize=7)
    hsave(fig, f"{a.out}/fig5_domain_shift.png"); plt.close(fig)
    json.dump({k: v for k, v in per.items()}, open(f"{a.out}/domain_shift_points.json", "w"))

    # ---- Fig. 6: calibration curves
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.3), sharey=True)
    lv = [float(x) for x in R[0]["proposed"]["test_id"]["coverage"]]
    for ax, sp, t in zip(axs, ("test_id", "test_ood"), ("(a) In-distribution", "(b) Out-of-distribution")):
        ax.plot([0.45, 1], [0.45, 1], color="k", lw=0.8, ls="--")
        for k in KINDS:
            c = np.array([[v for v in r[k][sp]["coverage"].values()] for r in R])
            ax.errorbar(lv, c.mean(0), yerr=c.std(0), color=COL[k], ls=LS[k], marker=MRK[k], ms=3.5, lw=1.3, capsize=1.5, elinewidth=0.7)
        ax.set_title(t, fontsize=8.5); ax.set_xlabel("Nominal coverage"); ax.set_xlim(0.45, 1); ax.set_ylim(0.0, 1.0)
    axs[0].set_ylabel("Empirical coverage")
    fig.tight_layout(rect=(0, 0.13, 1, 1)); legend(fig, loc="lower center", ncol=5, fontsize=7.5)
    hsave(fig, f"{a.out}/fig6_calibration.png"); plt.close(fig)

    # ---- Fig. 7: synchronisation error over time
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, sp, t in zip(axs, ("test_id", "test_ood"), ("(a) In-distribution", "(b) Out-of-distribution")):
        for k in KINDS:
            L = min(len(r[k][sp]["sync_series"]) for r in R)
            H = np.array([r[k][sp]["sync_series"][:L] for r in R])
            W_ = 50  # moving average over 50 control steps (0.25 s) removes the gait-cycle ripple
            ker = np.ones(W_) / W_
            H = np.array([np.convolve(h, ker, mode="valid") for h in H]); x = (np.arange(H.shape[1]) + W_) * 5e-3
            ax.plot(x, H.mean(0), color=COL[k], ls=LS[k], lw=1.3)
            ax.fill_between(x, H.min(0), H.max(0), color=COL[k], alpha=0.10, lw=0)
        ax.set_title(t, fontsize=8.5); ax.set_xlabel("Time (s)")
    axs[0].set_ylabel("Scaled state error"); axs[0].set_yscale("log")
    fig.tight_layout(rect=(0, 0.13, 1, 1)); legend(fig, loc="lower center", ncol=5, fontsize=7.5)
    hsave(fig, f"{a.out}/fig7_sync.png"); plt.close(fig)

    # ---- Fig. 8: ablation summary
    fig, axs = plt.subplots(1, 4, figsize=(7.4, 2.7))
    panels = [("rmse_id", "(a) ID RMSE (rad)"), ("rmse_ood", "(b) OOD RMSE (rad)"), ("sync_id", "(c) Sync. error (ID)"), ("ece_id", "(d) ECE (ID)")]
    for ax, (key, t) in zip(axs, panels):
        for i, k in enumerate(KINDS):
            m, s = S[k][key]
            ax.bar(i, m, yerr=s, color=COL[k], width=0.7, capsize=2, error_kw=dict(lw=0.8))
        ax.set_xticks([]); ax.set_title(t, fontsize=8); ax.grid(axis="x", visible=False)
    fig.tight_layout(rect=(0, 0.13, 1, 1))
    h = [plt.Rectangle((0, 0), 1, 1, color=COL[k]) for k in KINDS]
    fig.legend(h, [LABELS[k] for k in KINDS], loc="lower center", ncol=5, fontsize=7.5, frameon=False)
    hsave(fig, f"{a.out}/fig8_ablation.png"); plt.close(fig)
    print(md)


if __name__ == "__main__":
    main()
