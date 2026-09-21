"""Simulated data generation: plant trajectories + nominal-model residual targets."""
from __future__ import annotations
import numpy as np
from .env import Plant, Twin, DT, NV, reduced_state
from .gait import GaitSchedule, pd_torque

ID_RANGES = dict(mu=(0.6, 1.0), k_scale=(0.8, 1.25), payload=(0.0, 1.5))
# OOD: every factor is drawn from outside the ID range (two-sided where possible)
OOD_SETS = dict(mu=[(0.2, 0.45), (1.3, 1.6)], k_scale=[(0.4, 0.6), (1.8, 2.4)], payload=[(3.0, 5.0)])


def sample_condition(rng: np.random.Generator, split: str) -> dict:
    """split in {'id','ood'}. Actuator/joint mismatch is present in both (it is what the residual must learn)."""
    c = dict(joint_damping=rng.uniform(0.02, 0.10), joint_frictionloss=rng.uniform(0.01, 0.05),
             act_gain=rng.uniform(0.88, 0.97))
    if split == "id":
        for k, (lo, hi) in ID_RANGES.items():
            c[k] = rng.uniform(lo, hi)
    else:
        for k, sets in OOD_SETS.items():
            lo, hi = sets[rng.integers(len(sets))]
            c[k] = rng.uniform(lo, hi)
    c["split"] = split
    return c


def fell(qpos, qvel) -> bool:
    z = reduced_state(qpos, qvel)
    return bool(qpos[2] < 0.14 or z[26] > -0.6)


def generate_episode(cond: dict, seed: int, n_steps: int, twin: Twin | None = None) -> dict | None:
    """Roll the plant under a random trot schedule; for each step also compute the nominal-model prediction
    from the *plant* state, giving the residual acceleration target a_res = (v_plant' - v_nominal')/dt."""
    rng = np.random.default_rng(seed)
    twin = twin or Twin()
    plant = Plant(cond)
    sched = GaitSchedule(rng, n_steps, DT)
    Q, V, TAU, C, ARES, ATOT = [], [], [], [], [], []
    Q.append(plant.qpos); V.append(plant.qvel)
    for k in range(n_steps):
        q, v = plant.qpos, plant.qvel
        tau = pd_torque(sched.targets(k), q[7:], v[6:])
        qn, vn, c = twin.prepare_step(q, v, tau)      # nominal next state + contact mode at x_t
        plant.step(tau)
        q2, v2 = plant.qpos, plant.qvel
        if not (np.all(np.isfinite(q2)) and np.all(np.isfinite(v2))) or fell(q2, v2):
            break
        TAU.append(tau); C.append(c); ARES.append((v2 - vn) / DT); ATOT.append((v2 - v) / DT)
        Q.append(q2); V.append(v2)
    T = len(TAU)
    if T < 100:
        return None
    return dict(qpos=np.array(Q), qvel=np.array(V), tau=np.array(TAU), c=np.array(C),
                a_res=np.array(ARES), a_tot=np.array(ATOT), cond=cond, seed=seed)


def generate_split(n_episodes: int, split: str, n_steps: int, base_seed: int) -> list[dict]:
    twin = Twin()
    eps, s = [], 0
    rng = np.random.default_rng(base_seed)
    while len(eps) < n_episodes and s < 20 * n_episodes:
        cond = sample_condition(rng, split)
        ep = generate_episode(cond, base_seed * 100003 + s, n_steps, twin)
        s += 1
        if ep is not None:
            eps.append(ep)
    return eps
