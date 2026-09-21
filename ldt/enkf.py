"""Ensemble Kalman filter for online twin synchronisation with (optionally) uncertainty-adaptive process noise."""
from __future__ import annotations
import time
import numpy as np
from .env import DT, NQ, NV, Z_SCALE, measurement, reduced_state, integrate_pos, Twin
from .rollout import twin_step

_LOCALISE_ROWS = {"none": [], "base_pos": [0, 1, 2], "base_lin": [0, 1, 2, NQ, NQ + 1, NQ + 2]}
R_STD = np.concatenate([np.full(12, 0.01), np.full(12, 0.10), np.full(3, 0.02), np.full(3, 0.05)])


def _noise_scales(cfg, var_total, adaptive):
    """Per-particle process-noise std in dof space. Adaptive: base + kappa * propagated residual variance."""
    N = var_total.shape[0]
    # dof order: base lin(3), base ang(3), 12 joints
    base_q = np.concatenate([np.full(6, cfg["q_base_pos"]), np.full(12, cfg["q_joint_pos"])])
    base_v = np.concatenate([np.full(3, cfg["q_vel_lin"]), np.full(3, cfg["q_vel_ang"]), np.full(12, cfg["q_vel_joint"])])
    if not adaptive:
        return np.tile(base_q, (N, 1)), np.tile(base_v, (N, 1))
    k = cfg["adapt_kappa"]
    sq = np.sqrt(base_q ** 2 + k * (DT ** 2 / 2) ** 2 * var_total)
    sv = np.sqrt(base_v ** 2 + k * DT ** 2 * var_total)
    return sq, sv


def _project_and_guard(twin: Twin, qp, vp, rng):
    """Keep analysis particles physically admissible: lift the base out of foot-floor penetration (the linear
    Kalman update does not know about contact constraints) and replace numerically exploded particles."""
    import mujoco
    r = 0.02
    for i in range(qp.shape[0]):
        twin.d.qpos[:] = qp[i]
        mujoco.mj_kinematics(twin.m, twin.d)
        pen = min(twin.d.geom_xpos[fid][2] for fid in twin.foot_ids) - r
        if pen < 0:
            qp[i, 2] -= pen
    ok = (np.isfinite(qp).all(1) & np.isfinite(vp).all(1) & (np.abs(vp).max(1) < 30.0) & (qp[:, 2] > 0.05) & (qp[:, 2] < 0.8))
    if ok.any() and not ok.all():
        src = rng.choice(np.flatnonzero(ok), size=int((~ok).sum()))
        qp[~ok], vp[~ok] = qp[src], vp[src]
    return qp, vp


def run_enkf(model, twin: Twin, ep: dict, cfg: dict, rng, adaptive: bool):
    """Assimilate noisy sensor data from the plant trajectory `ep` with the twin `model`.
    Returns per-step scaled state error, joint-position error (rad) and wall-clock per step."""
    N, T = cfg["n_particles"], min(cfg["sync_steps"], len(ep["tau"]))
    q_true, v_true = ep["qpos"], ep["qvel"]
    # initial particles: perturbed truth (same initial uncertainty for every method)
    qp = np.stack([integrate_pos(twin.m, q_true[0], np.concatenate([rng.normal(0, 0.03, 3), rng.normal(0, 0.03, 3), rng.normal(0, 0.05, 12)]))
                   for _ in range(N)])
    vp = v_true[0] + rng.normal(0, 0.2, (N, NV))
    err_z, err_q, t_wall = [], [], []
    for t in range(T):
        tau = np.repeat(ep["tau"][t][None], N, 0)
        t0 = time.perf_counter()
        qp, vp, epi, ale = twin_step(twin, model, qp, vp, tau, "mean", return_var=True)
        sq, sv = _noise_scales(cfg, epi + ale, adaptive and model.is_ensemble)
        qp = np.stack([integrate_pos(twin.m, qp[i], sq[i] * rng.standard_normal(NV)) for i in range(N)])
        vp = vp + sv * rng.standard_normal((N, NV))
        if (t + 1) % cfg["obs_every"] == 0:
            y = measurement(q_true[t + 1], v_true[t + 1]) + R_STD * rng.standard_normal(R_STD.shape)
            X = np.concatenate([qp, vp], 1)
            mean = X.mean(0); X = mean + cfg["inflation"] * (X - mean)
            Y = measurement(X[:, :NQ], X[:, NQ:])
            Xm, Ym = X - X.mean(0), Y - Y.mean(0)
            Cxy, Cyy = Xm.T @ Ym / (N - 1), Ym.T @ Ym / (N - 1)
            K = Cxy @ np.linalg.inv(Cyy + np.diag(R_STD ** 2))
            K[_LOCALISE_ROWS[cfg.get("localise", "none")]] *= 0.0      # covariance localisation (see README)
            innov = y[None] + R_STD * rng.standard_normal((N, len(y))) - Y
            inc = innov @ K.T
            lim = cfg.get("max_base_vel_increment")
            if lim:                                                     # gate implausible analysis jumps of unobserved base velocity
                inc[:, NQ:NQ + 3] = np.clip(inc[:, NQ:NQ + 3], -lim, lim)
            X = X + inc
            qp, vp = X[:, :NQ], X[:, NQ:]
            qp[:, 3:7] /= np.linalg.norm(qp[:, 3:7], axis=1, keepdims=True)
            qp, vp = _project_and_guard(twin, qp, vp, rng)
        t_wall.append(time.perf_counter() - t0)
        qm = qp.mean(0); qm[3:7] /= np.linalg.norm(qm[3:7])
        z_hat, z_true = reduced_state(qm, vp.mean(0)), reduced_state(q_true[t + 1], v_true[t + 1])
        err_z.append(np.sqrt(np.mean(((z_hat - z_true) / Z_SCALE) ** 2)))
        err_q.append(np.sqrt(np.mean((z_hat[:12] - z_true[:12]) ** 2)))
    return np.array(err_z), np.array(err_q), np.array(t_wall)
