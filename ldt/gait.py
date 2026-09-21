"""Open-loop trot generator (foot-space trajectory -> analytic 2-link IK) + joint PD controller."""
from __future__ import annotations
import numpy as np
from .env import STAND_Q, TAU_MAX
from .model_xml import L_THIGH as L1, L_CALF as L2

KP, KD = 120.0, 3.0
_H0 = L1 * np.cos(0.8) + L2 * np.cos(0.8)          # nominal standing leg length (vertical)


def leg_ik(x, z):
    """Foot position (x fwd, z up, z<0) relative to the hip -> (thigh, knee) angles, knee pointing backwards.
    Kinematics: p = -L1 (sin t1, cos t1) - L2 (sin t2, cos t2), t2 = t1 + knee."""
    d = np.clip(np.hypot(x, z), 0.05, L1 + L2 - 1e-3)
    knee = -np.arccos(np.clip((d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2), -1, 1))
    psi = np.arctan2(-x, -z)                         # direction of foot measured from straight down (+ = backward)
    beta = np.arccos(np.clip((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
    return psi + beta, knee


def fk_check():
    for x, z in [(0.0, -0.29), (0.05, -0.27), (-0.06, -0.26)]:
        t1, kn = leg_ik(x, z)
        px = -L1 * np.sin(t1) - L2 * np.sin(t1 + kn)
        pz = -L1 * np.cos(t1) - L2 * np.cos(t1 + kn)
        assert abs(px - x) < 1e-6 and abs(pz - z) < 1e-6, (x, z, px, pz)


class GaitSchedule:
    """Piece-wise constant gait commands (frequency, step length, clearance, turn) -> gait transitions."""

    def __init__(self, rng: np.random.Generator, n_steps: int, dt: float, seg_seconds=(1.5, 3.0)):
        self.dt = dt
        self.segments = []
        t = 0
        while t < n_steps:
            L = int(rng.uniform(*seg_seconds) / dt)
            standing = rng.random() < 0.12
            self.segments.append(dict(
                start=t, end=t + L,
                f=rng.uniform(1.6, 3.0),
                step=0.0 if standing else rng.uniform(0.05, 0.13),
                clear=rng.uniform(0.04, 0.07),
                turn=rng.uniform(-0.12, 0.12) if rng.random() < 0.4 else 0.0,
                height=rng.uniform(-0.01, 0.01),
            ))
            t += L
        self.phase = rng.uniform(0, 2 * np.pi)
        self._seg = 0

    def command(self, k: int):
        while k >= self.segments[self._seg]["end"] and self._seg < len(self.segments) - 1:
            self._seg += 1
        s = self.segments[self._seg]
        self.phase += 2 * np.pi * s["f"] * self.dt
        return s

    def targets(self, k: int) -> np.ndarray:
        s = self.command(k)
        q = np.zeros(12)
        offs = [0.0, np.pi, np.pi, 0.0]              # trot: FL & RR in phase, FR & RL in anti-phase
        ramp = min(1.0, k * self.dt / 0.6)           # smooth start from the standing pose
        for i in range(4):
            ph = self.phase + offs[i]
            x = ramp * 0.5 * s["step"] * np.cos(ph)
            z = -(_H0 + s["height"]) + ramp * s["clear"] * max(0.0, -np.sin(ph)) * (s["step"] > 0)
            t1, kn = leg_ik(x, z)
            sy = 1.0 if i % 2 == 0 else -1.0
            q[3 * i:3 * i + 3] = [sy * s["turn"] * ramp * (1 if i < 2 else -1), t1, kn]
        return q


def pd_torque(q_target, q, qd):
    return np.clip(KP * (q_target - q) - KD * qd, -TAU_MAX, TAU_MAX)
