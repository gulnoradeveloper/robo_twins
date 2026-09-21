import sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ldt.gait import fk_check
from ldt.data import generate_episode, sample_condition
from ldt.env import Twin, model_input, reduced_state
from ldt.train import train_model
from ldt.rollout import rollout
from ldt.models import ResidualModel

CFG = dict(ensemble_size=2, hidden=32, layers=2, lr=2e-3, weight_decay=1e-4, batch_size=64, epochs=2)


def test_ik():
    fk_check()


def test_episode_shapes_and_residual_is_nonzero():
    cond = sample_condition(np.random.default_rng(0), "ood")
    ep = generate_episode(cond, 0, 300)
    assert ep is not None
    T = len(ep["tau"])
    assert ep["qpos"].shape == (T + 1, 19) and ep["a_res"].shape == (T, 18)
    assert np.abs(ep["a_res"]).mean() > 1e-3          # plant != nominal model


def test_nominal_twin_matches_itself():
    """With identical parameters the nominal model must reproduce a nominal plant exactly (zero residual)."""
    from ldt.env import Plant, NOMINAL
    cond = {k: NOMINAL[k] for k in NOMINAL}
    ep = generate_episode(cond, 1, 200)
    assert np.abs(ep["a_res"]).max() < 1e-6


def test_train_and_rollout():
    cond = sample_condition(np.random.default_rng(1), "id")
    eps = [generate_episode(cond, s, 300) for s in range(2)]
    m = train_model("proposed", eps, eps[:1], CFG, seed=0, log=lambda *_: None)
    out = rollout(Twin(), m, eps[0]["qpos"][0], eps[0]["qvel"][0], eps[0]["tau"][:5], S=3, rng=np.random.default_rng(0))
    assert out.shape == (3, 5, 34) and np.isfinite(out).all()
    out0 = rollout(Twin(), ResidualModel("physics"), eps[0]["qpos"][0], eps[0]["qvel"][0], eps[0]["tau"][:5])
    assert out0.shape == (1, 5, 34)
