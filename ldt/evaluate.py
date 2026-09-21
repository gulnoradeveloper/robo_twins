"""Evaluation protocol: multi-step rollouts (RMSE/MAE/coverage/ECE/width/NLL) and closed-loop EnKF synchronisation."""
from __future__ import annotations
import time
import numpy as np
from scipy.stats import norm
from .env import reduced_state, Twin, Z_SCALE
from .models import KINDS
from .rollout import rollout
from .enkf import run_enkf

LEVELS = np.array([0.5, 0.6, 0.7, 0.8, 0.9, 0.95])


def make_windows(eps, H, stride, rng, max_windows):
    w = [(i, s) for i, ep in enumerate(eps) for s in range(0, len(ep["tau"]) - H, stride)]
    if len(w) > max_windows:
        w = [w[j] for j in rng.choice(len(w), max_windows, replace=False)]
    return w


def truth_z(eps, windows, H):
    return np.stack([reduced_state(eps[i]["qpos"][s + 1:s + H + 1], eps[i]["qvel"][s + 1:s + H + 1]) for i, s in windows])


def predict_windows(model, twin, eps, windows, H, S, rng):
    """Returns predicted mean z [W,H,34] and per-sample std of joint positions [W,H,12] (None if not stochastic)."""
    mean, std = [], []
    stochastic = model.is_ensemble and model.hetero
    for i, s in windows:
        ep = eps[i]
        out = rollout(twin, model, ep["qpos"][s], ep["qvel"][s], ep["tau"][s:s + H], S if stochastic else 1, rng)
        mean.append(out.mean(0))
        if stochastic:
            std.append(out[:, :, :12].std(0, ddof=1))
    return np.stack(mean), (np.stack(std) if stochastic else None)


def calibrate_sigma(pred, truth):
    """Homoscedastic interval for models without UQ: per-(horizon, joint) RMS error on validation rollouts."""
    return np.sqrt(np.mean((pred[:, :, :12] - truth[:, :, :12]) ** 2, axis=0))


def rollout_metrics(pred, sigma, truth):
    e = pred[:, :, :12] - truth[:, :, :12]
    sigma = np.maximum(sigma, 1e-4)
    res = dict(rmse=float(np.sqrt(np.mean(e ** 2))),
               mae_std=float(np.mean(np.abs(pred - truth) / Z_SCALE)),
               nll=float(np.mean(0.5 * (np.log(2 * np.pi * sigma ** 2) + e ** 2 / sigma ** 2))),
               width95=float(np.mean(2 * 1.96 * sigma)))
    cov = np.array([np.mean(np.abs(e) <= norm.ppf(0.5 + L / 2) * sigma) for L in LEVELS])
    res["coverage"] = {f"{L:.2f}": float(c) for L, c in zip(LEVELS, cov)}
    res["rmse_by_horizon"] = np.sqrt(np.mean(e ** 2, axis=(0, 2))).tolist()          # [H]
    res["window_rmse"] = np.sqrt(np.mean(e ** 2, axis=(1, 2))).tolist()              # [W]
    res["cov95"], res["cov90"] = float(cov[-1]), float(cov[-2])
    res["ece"] = float(np.mean(np.abs(cov - LEVELS)))
    return res


TRANS_BINS = [(0, 0), (1, 2), (3, 5), (6, 10), (11, 10 ** 9)]      # |steps to nearest contact switch|


def transition_analysis(model, eps):
    """Relative one-step residual prediction error, by distance (in control steps) to the nearest contact-mode switch.
    Error is RMS(a_pred - a_res) / RMS(a_res over all samples); the physics-only twin predicts a_res = 0.
    Also returns the true residual magnitude per bin, and its stance/swing split for the four legs' joints."""
    from .env import model_input
    dist_all, true_all, pred_all, c_all = [], [], [], []
    for ep in eps:
        T = len(ep["tau"]); c = ep["c"]
        sw = np.flatnonzero(np.any(c[1:] != c[:-1], axis=1)) + 1           # indices where the mode changes
        idx = np.arange(T)
        d = np.abs(idx[:, None] - sw[None, :]).min(1) if len(sw) else np.full(T, 10 ** 6)
        if model.kind == "physics":
            pred = np.zeros((T, 18))
        else:
            x = model_input(ep["qpos"][:T], ep["qvel"][:T], ep["tau"], c if model.uses_mode else None)
            pred = model.mean_and_var(x)[0]
        dist_all.append(d); true_all.append(ep["a_res"]); pred_all.append(pred); c_all.append(c)
    d, y, p, c = (np.concatenate(a) for a in (dist_all, true_all, pred_all, c_all))
    ref = np.sqrt(np.mean(y ** 2))
    out = dict(bins=[f"{lo}" if lo == hi else (f"{lo}-{hi}" if hi < 10 ** 8 else f">{lo - 1}") for lo, hi in TRANS_BINS],
               true_rms=[], rel_err=[], n=[])
    for lo, hi in TRANS_BINS:
        m = (d >= lo) & (d <= hi)
        out["n"].append(int(m.sum()))
        out["true_rms"].append(float(np.sqrt(np.mean(y[m] ** 2)) / ref) if m.any() else None)
        out["rel_err"].append(float(np.sqrt(np.mean((p[m] - y[m]) ** 2)) / ref) if m.any() else None)
    # stance vs swing: joint-acceleration residual of each leg (dofs 6+3i .. 6+3i+2), grouped by that leg's contact flag
    st, sw_ = [], []
    for i in range(4):
        cols = slice(6 + 3 * i, 9 + 3 * i)
        st.append(y[c[:, i] > 0.5][:, cols].ravel()); sw_.append(y[c[:, i] < 0.5][:, cols].ravel())
    st, sw_ = np.concatenate(st), np.concatenate(sw_)
    out["true_rms_stance"] = float(np.sqrt(np.mean(st ** 2)) / ref)
    out["true_rms_swing"] = float(np.sqrt(np.mean(sw_ ** 2)) / ref)
    out["overall_rel_err"] = float(np.sqrt(np.mean((p - y) ** 2)) / ref)
    return out


def evaluate_all(models, splits, cfg, log=print):
    twin = Twin()
    rng = np.random.default_rng(cfg["seed"] + 7)
    H = cfg["horizon"]
    W = {k: make_windows(splits[k], H, cfg["window_stride"], rng, cfg["max_windows"]) for k in ("val", "test_id", "test_ood")}
    T = {k: truth_z(splits[k], W[k], H) for k in W}
    results = {k: {} for k in KINDS}
    for kind in KINDS:
        m = models[kind]
        t0 = time.time()
        pv, sv = predict_windows(m, twin, splits["val"], W["val"], H, cfg["n_samples"], rng)
        sigma_val = sv if sv is not None else None
        sig_const = calibrate_sigma(pv, T["val"]) if sv is None else None
        for split in ("test_id", "test_ood"):
            p, s = predict_windows(m, twin, splits[split], W[split], H, cfg["n_samples"], rng)
            sigma = s if s is not None else np.broadcast_to(sig_const, (p.shape[0],) + sig_const.shape)
            results[kind][split] = rollout_metrics(p, sigma, T[split])
            results[kind][split]["window_episode"] = [int(i) for i, _ in W[split]]
        log(f"  rollouts [{kind}] done ({time.time() - t0:.0f}s): ID RMSE {results[kind]['test_id']['rmse']:.4f}  "
            f"OOD RMSE {results[kind]['test_ood']['rmse']:.4f}")
    # ---- closed-loop synchronisation
    log("  EnKF synchronisation ...")
    for kind in KINDS:
        m = models[kind]
        adaptive = kind in ("proposed", "hybrid_nomode")
        for split in ("test_id", "test_ood"):
            es, eq, tw, series = [], [], [], []
            for j, ep in enumerate(splits[split][:cfg["n_sync_episodes"]]):
                r = np.random.default_rng(cfg["seed"] * 1000 + j)          # same noise stream for all methods
                a, b, c = run_enkf(m, twin, ep, cfg, r, adaptive)
                es.append(a.mean()); eq.append(b.mean()); tw.append(c.mean()); series.append(a)
            L = min(len(s) for s in series)
            results[kind][split]["sync_series"] = np.mean([s[:L] for s in series], axis=0).tolist()
            results[kind][split]["sync_error"] = float(np.mean(es))
            results[kind][split]["sync_joint_rmse"] = float(np.mean(eq))
            results[kind][split]["enkf_ms_per_step"] = float(np.mean(tw) * 1e3)
        log(f"  sync [{kind}]: ID {results[kind]['test_id']['sync_error']:.4f}  OOD {results[kind]['test_ood']['sync_error']:.4f}")
    # ---- contact-mode analysis of the learned residual (one-step, teacher-forced)
    log("  contact-transition analysis ...")
    for kind in ("physics", "hybrid_nouq", "hybrid_nomode", "proposed"):
        for split in ("test_id", "test_ood"):
            results[kind][split]["transition"] = transition_analysis(models[kind], splits[split])
    # ---- single-state twin latency (proposed)
    from .rollout import twin_step
    m = models["proposed"]; ep = splits["test_id"][0]
    q, v, tau = ep["qpos"][100][None], ep["qvel"][100][None], ep["tau"][100][None]
    twin_step(twin, m, q, v, tau, "mean")
    t0 = time.perf_counter()
    for _ in range(50):
        twin_step(twin, m, q, v, tau, "mean")
    results["latency_ms_single_twin_step"] = (time.perf_counter() - t0) / 50 * 1e3
    return results
