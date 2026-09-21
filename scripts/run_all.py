#!/usr/bin/env python
"""End-to-end pipeline: simulate -> train -> evaluate -> report.

    python scripts/run_all.py --config configs/default.json --out results/default
"""
import argparse, json, os, sys, time
import numpy as np
import torch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ldt.data import generate_split
from ldt.models import ResidualModel, KINDS, SPEC
from ldt.train import train_model
from ldt.evaluate import evaluate_all
from ldt.report import write_reports
from ldt.gait import fk_check


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/default.json")
    ap.add_argument("--out", default="results/default")
    ap.add_argument("--seed", type=int, default=None, help="override the seed in the config")
    ap.add_argument("--save-data", action="store_true", help="also store the generated trajectories as .npz")
    a = ap.parse_args()
    cfg = json.load(open(a.config))
    if a.seed is not None:
        cfg["seed"] = a.seed
    os.makedirs(a.out, exist_ok=True)
    seed = cfg["seed"]
    np.random.seed(seed); torch.manual_seed(seed); torch.set_num_threads(max(1, os.cpu_count() or 1))
    fk_check()
    t0 = time.time()

    print("[1/4] generating simulated data (MuJoCo plant vs nominal twin) ...")
    n = cfg["episode_steps"]
    splits = dict(
        train=generate_split(cfg["n_train"], "id", n, 1000 + seed),
        val=generate_split(cfg["n_val"], "id", n, 2000 + seed),
        test_id=generate_split(cfg["n_test"], "id", n, 3000 + seed),
        test_ood=generate_split(cfg["n_test"], "ood", n, 4000 + seed))
    stats = {k: dict(episodes=len(v), samples=int(sum(len(e["tau"]) for e in v)),
                     hours=sum(len(e["tau"]) for e in v) * 0.005 / 3600) for k, v in splits.items()}
    print("   ", json.dumps(stats))
    json.dump(dict(stats=stats, conditions={k: [e["cond"] for e in v] for k, v in splits.items()}),
              open(f"{a.out}/dataset_summary.json", "w"), indent=1)
    if a.save_data:
        for k, v in splits.items():
            np.savez_compressed(f"{a.out}/data_{k}.npz", **{f"ep{i}_{key}": e[key] for i, e in enumerate(v)
                                for key in ("qpos", "qvel", "tau", "c", "a_res", "a_tot")})

    print("[2/4] training ...")
    models = {"physics": ResidualModel("physics")}
    for i, kind in enumerate(k for k in KINDS if k != "physics"):
        models[kind] = train_model(kind, splits["train"], splits["val"], cfg, seed * 10 + i)
        m = models[kind]
        torch.save(dict(state=m.net.state_dict(), xm=m.xm, xs=m.xs, ym=m.ym, ys=m.ys, kind=kind, cfg=cfg),
                   f"{a.out}/model_{kind}.pt")

    print("[3/4] evaluating ...")
    res = evaluate_all(models, splits, cfg)
    json.dump(res, open(f"{a.out}/results.json", "w"), indent=1)
    print("[4/4] writing report ...")
    write_reports(res, a.out, cfg)
    print(open(f"{a.out}/results.md").read())
    print(f"done in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
