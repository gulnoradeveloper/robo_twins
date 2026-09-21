"""Simulated plant ("true" system) and nominal physics model (the twin's physics core)."""
from __future__ import annotations
import numpy as np
import mujoco
from .model_xml import build_xml

DT_SUB, N_SUB = 0.001, 5
DT = DT_SUB * N_SUB          # control / sampling period: 5 ms -> 200 Hz
NQ, NV, NJ = 19, 18, 12
TAU_MAX = 33.5
STAND_Q = np.array([0, 0.8, -1.6] * 4)
Q0 = np.concatenate([[0, 0, 0.32, 1, 0, 0, 0], STAND_Q])
FOOT_NAMES = ["FL_foot", "FR_foot", "RL_foot", "RR_foot"]

# Nominal (twin) parameters. The plant differs from these -> systematic model mismatch.
NOMINAL = dict(mu=0.8, k_scale=1.0, payload=0.0, joint_damping=0.0, joint_frictionloss=0.0, act_gain=1.0, act_sat=False)


def make_model(mu=0.8, k_scale=1.0, payload=0.0, joint_damping=0.0, joint_frictionloss=0.0) -> mujoco.MjModel:
    m = mujoco.MjModel.from_xml_string(build_xml())
    m.geom_friction[:, 0] = mu
    # contact stiffness ~ 1/timeconst^2  (solref[0] = timeconst)
    m.geom_solref[:, 0] = 0.02 / np.sqrt(k_scale)
    trunk = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "trunk")
    scale = (m.body_mass[trunk] + payload) / m.body_mass[trunk]
    m.body_mass[trunk] += payload
    m.body_inertia[trunk] *= scale
    m.dof_damping[6:] = joint_damping
    m.dof_frictionloss[6:] = joint_frictionloss
    return m


class _Base:
    def __init__(self, model):
        self.m = model
        self.d = mujoco.MjData(model)
        self.foot_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, n) for n in FOOT_NAMES]
        self.floor_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "floor")
        self._f6 = np.zeros(6)

    def set_state(self, qpos, qvel):
        self.d.qpos[:] = qpos
        self.d.qvel[:] = qvel
        self.d.qacc_warmstart[:] = 0
        self.d.ctrl[:] = 0

    def contact_mode(self) -> np.ndarray:
        """Binary foot-contact vector c in {0,1}^4 from the current contact set (normal force > 0.5 N)."""
        c = np.zeros(4)
        d, m = self.d, self.m
        for i in range(d.ncon):
            con = d.contact[i]
            g1, g2 = con.geom1, con.geom2
            for k, fid in enumerate(self.foot_ids):
                if (g1 == fid and g2 == self.floor_id) or (g2 == fid and g1 == self.floor_id):
                    mujoco.mj_contactForce(m, d, i, self._f6)
                    if self._f6[0] > 0.5:
                        c[k] = 1.0
        return c


class Plant(_Base):
    """The 'real' system: perturbed physical parameters + nonlinear actuators."""

    def __init__(self, cond: dict):
        super().__init__(make_model(cond["mu"], cond["k_scale"], cond["payload"],
                                    cond["joint_damping"], cond["joint_frictionloss"]))
        self.cond = cond
        self.reset()

    def reset(self):
        self.set_state(Q0, np.zeros(NV))
        mujoco.mj_forward(self.m, self.d)

    def step(self, tau_cmd):
        g = self.cond["act_gain"]
        tau = np.asarray(tau_cmd, dtype=float)
        if self.cond.get("act_sat", True):
            tau = TAU_MAX * np.tanh(tau / TAU_MAX)                     # soft saturation (nominal model: hard clip only)
        tau = g * tau                                                   # gain error
        self.d.ctrl[:] = tau
        for _ in range(N_SUB):
            mujoco.mj_step(self.m, self.d)

    @property
    def qpos(self): return self.d.qpos.copy()
    @property
    def qvel(self): return self.d.qvel.copy()


class Twin(_Base):
    """Nominal rigid-body model used as the physics core of the digital twin."""

    def __init__(self):
        super().__init__(make_model(**{k: NOMINAL[k] for k in ("mu", "k_scale", "payload", "joint_damping", "joint_frictionloss")}))

    def prepare_step(self, qpos, qvel, tau_cmd):
        """From state (qpos,qvel): contact mode c_t, then nominal next state after one control period."""
        self.set_state(qpos, qvel)
        mujoco.mj_forward(self.m, self.d)
        c = self.contact_mode()
        self.d.ctrl[:] = np.clip(tau_cmd, -TAU_MAX, TAU_MAX)
        for _ in range(N_SUB):
            mujoco.mj_step(self.m, self.d)
        return self.d.qpos.copy(), self.d.qvel.copy(), c


def integrate_pos(model, qpos, dq, dt=1.0):
    """qpos + dq*dt on the manifold (handles the floating-base quaternion). Returns new array."""
    out = np.array(qpos, dtype=float, copy=True)
    mujoco.mj_integratePos(model, out, np.ascontiguousarray(dq, dtype=float), dt)
    return out


# ---------------------------------------------------------------- features
def quat_to_rot(q):
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    R = np.empty(q.shape[:-1] + (3, 3))
    R[..., 0, 0] = 1 - 2 * (y * y + z * z); R[..., 0, 1] = 2 * (x * y - z * w); R[..., 0, 2] = 2 * (x * z + y * w)
    R[..., 1, 0] = 2 * (x * y + z * w); R[..., 1, 1] = 1 - 2 * (x * x + z * z); R[..., 1, 2] = 2 * (y * z - x * w)
    R[..., 2, 0] = 2 * (x * z - y * w); R[..., 2, 1] = 2 * (y * z + x * w); R[..., 2, 2] = 1 - 2 * (x * x + y * y)
    return R


def reduced_state(qpos, qvel):
    """34-d body-frame state: joint pos(12), joint vel(12), gravity dir(3), base lin vel(3), gyro(3), height(1)."""
    qpos, qvel = np.asarray(qpos), np.asarray(qvel)
    q = qpos[..., 3:7] / np.linalg.norm(qpos[..., 3:7], axis=-1, keepdims=True)
    R = quat_to_rot(q)
    g_b = -R[..., 2, :]
    v_b = np.einsum("...ji,...j->...i", R, qvel[..., 0:3])
    return np.concatenate([qpos[..., 7:], qvel[..., 6:], g_b, v_b, qvel[..., 3:6], qpos[..., 2:3]], axis=-1)


# Fixed physical scales used to make heterogeneous state components comparable in reported aggregate metrics
Z_SCALE = np.array([0.1] * 12 + [2.0] * 12 + [0.05] * 3 + [0.2] * 3 + [0.5] * 3 + [0.02])


def model_input(qpos, qvel, tau, c=None):
    """Network input: reduced state, normalised torque command, optionally the contact mode."""
    parts = [reduced_state(qpos, qvel), np.asarray(tau) / TAU_MAX]
    if c is not None:
        parts.append(np.asarray(c))
    return np.concatenate(parts, axis=-1)


def measurement(qpos, qvel):
    """Sensor model h(x): joint pos, joint vel, gravity direction (IMU), gyro -> 30-d."""
    z = reduced_state(qpos, qvel)
    return np.concatenate([z[..., 0:12], z[..., 12:24], z[..., 24:27], z[..., 30:33]], axis=-1)
