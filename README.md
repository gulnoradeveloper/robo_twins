# legged-digital-twin

Reference implementation of a **simulation-only, physics-informed digital twin for a legged robot**:
nominal rigid-body dynamics (MuJoCo) + learned, contact-mode-conditioned residual dynamics, heteroscedastic
deep-ensemble uncertainty quantification, and Ensemble-Kalman-filter (EnKF) synchronisation with
uncertainty-adaptive process noise. Everything runs on a CPU; no robot hardware is involved.

> **Scope and honesty note.** All results produced by this repository come from a MuJoCo simulation of a simple
> 12-DoF quadruped defined in `ldt/model_xml.py`. No physical-robot experiment is included. The numbers in
> `results/` are whatever this code produces on the stated seed/config; they are **not** copied from any paper
> and should not be assumed to equal numbers reported elsewhere. The tables and figures of the accompanying
> manuscript are generated from the released results with `scripts/summarize.py`.

## What is simulated

* **Plant ("real system")**: MuJoCo quadruped with terrain friction, contact stiffness, payload mass, joint damping
  and dry friction, and actuator gain error plus soft torque saturation.
* **Twin physics core**: the *same* robot with nominal parameters (mu = 0.8, stiffness scale 1, no payload, ideal
  actuators). The plant-vs-nominal difference is the systematic model mismatch the residual must learn.
* **In-distribution (ID)** vs **out-of-distribution (OOD)** conditions: friction, contact stiffness and payload are drawn
  from disjoint ranges (`ldt/data.py`: `ID_RANGES`, `OOD_SETS`). OOD episodes never appear in training/validation.
* **Data**: random trot schedules (frequency, step length, clearance, turning, standing phases) tracked by a joint PD
  controller; 200 Hz sampling (5 ms = 5 MuJoCo sub-steps). Episodes end early if the robot falls.
* **Residual target**: `a_res = (v_plant' - v_nominal') / dt`, where `v_nominal'` is the nominal model's one-step
  prediction *from the plant state*.

## Models compared (`ldt/models.py`)

| Key | Physics core | Learned part | UQ | Contact-mode input |
|---|---|---|---|---|
| `physics` | nominal MuJoCo | none | interval from validation RMS error | - |
| `data` | none | MLP predicts total acceleration | interval from validation RMS error | no |
| `hybrid_nouq` | nominal MuJoCo | single MLP residual (MSE) | interval from validation RMS error | yes |
| `hybrid_nomode` | nominal MuJoCo | heteroscedastic ensemble residual | ensemble | no |
| `proposed` | nominal MuJoCo | heteroscedastic ensemble residual | ensemble | yes (4 binary foot-contact flags) |

Models without native UQ receive a homoscedastic Gaussian interval whose per-(horizon, joint) width is the RMS error on
the ID validation rollouts, so that every method has a coverage number. Ensembles use member disagreement (epistemic) plus
predicted variance (aleatoric), sampled stochastically over the rollout.

## Metrics (`ldt/evaluate.py`)

* **RMSE (rad)**: joint positions, 25-step (125 ms) open-loop rollouts under recorded torque commands.
* **Aggregate MAE**: mean absolute error over the 34-d body-frame state, each component divided by a fixed physical
  scale (`ldt.env.Z_SCALE`), i.e. dimensionless.
* **Coverage / ECE / width / NLL** of Gaussian intervals on joint positions at levels 0.5-0.95 (empirical coverage of the
  *nominal* level is reported as is; nothing is recalibrated).
* **Synchronisation error**: closed-loop EnKF (default 64 particles, sensor update every 4th step) with noisy joint
  positions/velocities, IMU gravity direction and gyro; error is the RMS of the scaled state error (including
  unobserved base velocity and height) of the particle mean vs. the plant.
* **Latency**: wall-clock of one twin step on the machine that ran the code.

Each run is one training/evaluation pass with a fixed seed; the summary reports mean ± SD over three seeds. No confidence
intervals or significance tests are computed, so differences between methods should be read as descriptive.

## Released results (config `default`, seeds 0, 1, 2)

`results/seed{0,1,2}/` hold the raw outputs of three independent runs (`results.json`, `results.md`, model weights,
`dataset_summary.json`); `results/summary/` holds the aggregated tables (`summary.md`, `summary.json`) and the eight
manuscript figures, all produced by `scripts/summarize.py` and `scripts/make_diagrams.py`. Values are mean ± SD over the
three runs (0.17 h of training data per run, 5-member ensembles, 64 particles). In plain terms:

* Relative to the physics-only twin, the proposed model lowers rollout RMSE by about 61 % (ID) and 41 % (OOD) and the
  synchronisation error by about 38 % / 62 %.
* The **data-only baseline is more accurate** than all hybrid variants on rollout RMSE and on synchronisation error, so
  the proposed model is *not* uniformly best.
* Contact-flag conditioning and ensemble uncertainty give **no measurable accuracy gain** (differences are within the
  run-to-run spread).
* The heteroscedastic ensembles are **overconfident** (nominal 95 % intervals cover about 73 % ID and 39 % OOD).
* Model mismatch is concentrated within a few control steps of contact switches.

These are properties of this implementation (one-step training, small data set, hand-set filter noise) and of three runs;
they are reported as they came out, without tuning towards any method.

## Quick start

```bash
pip install -r requirements.txt
pytest -q tests                                              # ~10 s sanity checks
python scripts/run_all.py --config configs/quick.json   --out results/quick     # ~15 s smoke test
python scripts/run_all.py --config configs/default.json --seed 0 --out results/seed0   # ~10 min on 2 CPU cores
bash scripts/run_seeds.sh 0 1 2                                                       # seeds 0-2 -> results/seed{0,1,2}
python scripts/summarize.py --runs results/seed0 results/seed1 results/seed2 --out results/summary
python scripts/make_diagrams.py --out results/summary                                 # Fig. 1 and Fig. 2
```

Outputs in `--out`: `results.json` (all metrics), `results.md` (tables), `calibration_curve.png`,
`dataset_summary.json` (conditions of every episode), `model_*.pt` (weights + normalisers).
Add `--save-data` to also store the generated trajectories as `.npz`.

## Reproducibility

* Randomness is controlled by `seed` in the config: episode conditions and gait schedules (NumPy generators seeded per split
  and per episode), network initialisation/shuffling (PyTorch), rollout sampling and EnKF noise (fixed streams).
* The plant, twin, data generation and evaluation are deterministic given the seed on the same software versions;
  multi-threaded PyTorch on different hardware can change floating-point summation order slightly.
* Tested with Python 3.11, MuJoCo 3.13, PyTorch 2.14 (CPU).

## Layout

```
ldt/model_xml.py   MJCF of the quadruped          ldt/env.py      plant, nominal twin, features, sensors
ldt/gait.py        trot generator + PD            ldt/data.py     conditions, episodes, residual targets
ldt/models.py      ensemble MLP + baselines       ldt/train.py    one-step training
ldt/rollout.py     twin step / rollouts           ldt/enkf.py     EnKF synchronisation
ldt/evaluate.py    protocol and metrics           ldt/report.py   per-run tables + calibration figure
scripts/run_all.py end-to-end pipeline            scripts/run_seeds.sh   several seeds
scripts/summarize.py  3-seed tables + figures 3-8  scripts/make_diagrams.py  figures 1-2
configs/           quick + default configurations
```

## Deviations from a "full" formulation (read before citing)

* The epoch with the lowest validation loss (validation = ID episodes only) is kept for every learned model.
* Residual networks are trained **one-step, teacher-forced** (MuJoCo is not differentiable), not with a multi-step
  rollout loss; there is no temporal-smoothness or mode-consistency loss and no residual bound; no dropout by default.
* Contact is MuJoCo's own soft-contact model with binary foot-contact flags read from the contact set; there is no
  hysteresis/dwell-time logic and no separate implicit-integrator ablation (MuJoCo `implicitfast` is used throughout).
* The robot is a simple procedurally defined quadruped, not a specific commercial model. The data set is much smaller than
  hours-scale collections (see `dataset_summary.json`).
* The EnKF uses safeguards that are not part of a textbook EnKF: foot-floor penetration projection after
  each analysis step, a cap on the analysis increment of the unobserved base velocity, and replacement of numerically
  exploded particles (`ldt/enkf.py`). Process-noise magnitudes and the adaptation gain `adapt_kappa` were set by hand
  (not tuned per method).
* Latency numbers are for single-process Python on CPU and are not comparable to GPU/embedded figures.

## License

MIT (see `LICENSE`).
