"""Reference implementation of a physics-informed digital twin for a simulated quadruped.

Components: MuJoCo plant/twin (env), trot gait generator (gait), data generation (data),
residual-dynamics ensembles and baselines (models, train), rollout/EnKF (rollout, enkf),
and the evaluation protocol (evaluate).
"""
__version__ = "0.2.0"
