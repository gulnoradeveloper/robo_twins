"""Training of residual-dynamics networks (one-step, teacher-forced) and the baselines."""
from __future__ import annotations
import copy, time
import numpy as np
import torch
from .env import model_input
from .models import EnsMLP, ResidualModel, SPEC


def build_xy(episodes, kind):
    spec = SPEC[kind]
    X, Y = [], []
    for ep in episodes:
        T = len(ep["tau"])
        c = ep["c"] if spec["mode"] else None
        X.append(model_input(ep["qpos"][:T], ep["qvel"][:T], ep["tau"], c))
        Y.append(ep[spec["target"]])
    return np.concatenate(X).astype(np.float32), np.concatenate(Y).astype(np.float32)


def train_model(kind, train_eps, val_eps, cfg, seed, log=print) -> ResidualModel:
    spec = SPEC[kind]
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    X, Y = build_xy(train_eps, kind)
    Xv, Yv = build_xy(val_eps, kind)
    xm, xs = X.mean(0), X.std(0) + 1e-6
    ym, ys = Y.mean(0), Y.std(0) + 1e-6
    Xn, Yn = torch.as_tensor((X - xm) / xs), torch.as_tensor((Y - ym) / ys)
    Xvn, Yvn = torch.as_tensor((Xv - xm) / xs), torch.as_tensor((Yv - ym) / ys)
    M = cfg["ensemble_size"] if spec["ens"] else 1
    net = EnsMLP(M, X.shape[1], Y.shape[1], cfg["hidden"], cfg["layers"], spec["hetero"], cfg.get("dropout", 0.0))
    opt = torch.optim.AdamW(net.parameters(), lr=cfg["lr"], weight_decay=cfg["weight_decay"])
    N, B, E = Xn.shape[0], cfg["batch_size"], cfg["epochs"]
    steps = E * (N // B)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps)

    def loss_fn(mu, lv, y):
        if spec["hetero"]:
            return (0.5 * (lv + (y - mu) ** 2 * torch.exp(-lv))).mean()
        return ((y - mu) ** 2).mean()

    t0 = time.time()
    best_val, best_state, best_ep = float('inf'), None, -1
    for ep in range(E):
        net.train()
        perm = torch.argsort(torch.rand(M, N), dim=1)       # independent shuffling per member
        for b in range(N // B):
            idx = perm[:, b * B:(b + 1) * B]
            xb, yb = Xn[idx], Yn[idx]                          # [M,B,d]
            mu, lv = net(xb)
            loss = loss_fn(mu, lv, yb)
            opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        net.eval()
        with torch.no_grad():                                   # validation loss every epoch -> keep the best epoch
            mu, lv = net(Xvn.unsqueeze(0).expand(M, -1, -1))
            vl = loss_fn(mu, lv, Yvn.unsqueeze(0).expand(M, -1, -1)).item()
        if vl < best_val:
            best_val, best_state, best_ep = vl, copy.deepcopy(net.state_dict()), ep
        if ep % max(1, E // 5) == 0 or ep == E - 1:
            log(f"  [{kind}] epoch {ep + 1}/{E}  train {loss.item():.4f}  val {vl:.4f}  ({time.time() - t0:.0f}s)")
    net.load_state_dict(best_state)
    log(f"  [{kind}] restored best validation epoch {best_ep + 1} (val {best_val:.4f})")
    return ResidualModel(kind, net, xm, xs, ym, ys, spec["hetero"])
