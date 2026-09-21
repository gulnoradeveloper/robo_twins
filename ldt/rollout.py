"""One-step twin propagation (nominal MuJoCo + learned correction) and multi-step rollouts."""
from __future__ import annotations
import numpy as np
from .env import DT, model_input, integrate_pos, reduced_state, Twin


def twin_step(twin: Twin, model, qpos, qvel, tau, mode="mean", member_idx=None, rng=None, return_var=False):
    """Advance S states by one control period (5 ms).
    qpos [S,19], qvel [S,18], tau [S,12].  mode: 'mean' (ensemble-mean residual) or 'sample' (member+aleatoric draw).
    Returns qpos', qvel' (and, if return_var, epistemic/aleatoric acceleration variance [S,18])."""
    S = qpos.shape[0]
    zeros = np.zeros((S, 18))
    if model.kind == "data":
        a, ep, al = model.mean_and_var(model_input(qpos, qvel, tau, None))
        v2 = qvel + a * DT
        q2 = np.stack([integrate_pos(twin.m, qpos[s], v2[s], DT) for s in range(S)])
        return (q2, v2, ep, al) if return_var else (q2, v2)
    qn = np.empty_like(qpos); vn = np.empty_like(qvel); c = np.empty((S, 4))
    for s in range(S):
        qn[s], vn[s], c[s] = twin.prepare_step(qpos[s], qvel[s], tau[s])
    if model.kind == "physics":
        return (qn, vn, zeros, zeros) if return_var else (qn, vn)
    x = model_input(qpos, qvel, tau, c if model.uses_mode else None)
    if mode == "sample":
        a = model.sample(x, member_idx, rng); ep = al = zeros
        if return_var:
            _, ep, al = model.mean_and_var(x)
    else:
        a, ep, al = model.mean_and_var(x)
    v2 = vn + a * DT
    q2 = np.stack([integrate_pos(twin.m, qn[s], a[s] * DT / 2, DT) for s in range(S)])   # + a dt^2 / 2
    return (q2, v2, ep, al) if return_var else (q2, v2)


def rollout(twin, model, q0, v0, taus, S=1, rng=None):
    """Open-loop rollout under recorded torque commands taus [H,12].
    Deterministic (S=1, mean residual) for non-UQ models; S stochastic member/aleatoric samples for ensembles.
    Returns predicted reduced states [S,H,34]."""
    H = taus.shape[0]
    q = np.repeat(q0[None], S, 0); v = np.repeat(v0[None], S, 0)
    stochastic = model.is_ensemble and model.hetero and S > 1
    midx = np.arange(S) % max(model.M, 1)
    out = np.empty((S, H, 34))
    for h in range(H):
        tau = np.repeat(taus[h][None], S, 0)
        q, v = twin_step(twin, model, q, v, tau, "sample" if stochastic else "mean", midx, rng)
        out[:, h] = reduced_state(q, v)
    return out
