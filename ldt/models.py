"""Residual-dynamics models and baselines.

kind            physics core   learned part                     UQ                      contact-mode input
physics         nominal MuJoCo none                             -                       -
data            none           MLP -> total acceleration        -                       no
hybrid_nouq     nominal MuJoCo single MLP residual (MSE)        -                       yes
hybrid_nomode   nominal MuJoCo heteroscedastic ensemble         yes                     no
proposed        nominal MuJoCo heteroscedastic ensemble         yes                     yes
"""
from __future__ import annotations
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

KINDS = ["physics", "data", "hybrid_nouq", "hybrid_nomode", "proposed"]
LABELS = {"physics": "Physics-only", "data": "Data-only", "hybrid_nouq": "Hybrid without UQ",
          "hybrid_nomode": "Hybrid without mode awareness", "proposed": "Proposed configuration"}
SPEC = {  # uses_mode, ensemble size key, heteroscedastic, target
    "data": dict(mode=False, ens=False, hetero=False, target="a_tot"),
    "hybrid_nouq": dict(mode=True, ens=False, hetero=False, target="a_res"),
    "hybrid_nomode": dict(mode=False, ens=True, hetero=True, target="a_res"),
    "proposed": dict(mode=True, ens=True, hetero=True, target="a_res"),
}


class EnsLinear(nn.Module):
    def __init__(self, M, din, dout):
        super().__init__()
        self.w = nn.Parameter(torch.randn(M, din, dout) * (1.0 / np.sqrt(din)))
        self.b = nn.Parameter(torch.zeros(M, 1, dout))

    def forward(self, x):  # x [M,B,din]
        return torch.baddbmm(self.b, x, self.w)


class EnsMLP(nn.Module):
    """M independent MLPs evaluated in parallel: [M,B,din] -> mean, logvar [M,B,dout]."""

    def __init__(self, M, din, dout, hidden=256, layers=3, hetero=True, dropout=0.0):
        super().__init__()
        dims = [din] + [hidden] * layers
        self.lin = nn.ModuleList([EnsLinear(M, a, b) for a, b in zip(dims[:-1], dims[1:])])
        self.ln_w = nn.ParameterList([nn.Parameter(torch.ones(M, 1, hidden)) for _ in range(layers)])
        self.ln_b = nn.ParameterList([nn.Parameter(torch.zeros(M, 1, hidden)) for _ in range(layers)])
        self.mu = EnsLinear(M, hidden, dout)
        self.lv = EnsLinear(M, hidden, dout) if hetero else None
        self.drop = nn.Dropout(dropout)
        self.hidden = hidden

    def forward(self, x):
        for lin, w, b in zip(self.lin, self.ln_w, self.ln_b):
            x = F.layer_norm(lin(x), (self.hidden,)) * w + b
            x = self.drop(F.gelu(x))
        mu = self.mu(x)
        lv = self.lv(x).clamp(-8.0, 2.0) if self.lv is not None else torch.zeros_like(mu)
        return mu, lv


class ResidualModel:
    """Wraps a trained EnsMLP with input/output normalisation. kind='physics' has no network."""

    def __init__(self, kind, net=None, xm=None, xs=None, ym=None, ys=None, hetero=False):
        self.kind, self.net, self.hetero = kind, net, hetero
        self.uses_mode = SPEC.get(kind, {}).get("mode", False)
        self.is_ensemble = net is not None and net.mu.w.shape[0] > 1
        self.total_dynamics = kind == "data"      # network replaces the physics core
        self.xm, self.xs, self.ym, self.ys = xm, xs, ym, ys
        self.M = net.mu.w.shape[0] if net is not None else 0

    @torch.no_grad()
    def moments(self, x: np.ndarray):
        """x [N,din] raw -> per-member (mu [M,N,18], var [M,N,18]) in physical acceleration units."""
        xt = torch.as_tensor((x - self.xm) / self.xs, dtype=torch.float32)
        xt = xt.unsqueeze(0).expand(self.M, -1, -1).contiguous()
        self.net.eval()
        mu, lv = self.net(xt)
        mu = mu.numpy() * self.ys + self.ym
        var = np.exp(lv.numpy()) * self.ys ** 2 if self.hetero else np.zeros_like(mu)
        return mu, var

    def mean_and_var(self, x):
        """Ensemble-mean acceleration and (epistemic, aleatoric) variance."""
        mu, var = self.moments(x)
        return mu.mean(0), (mu.var(0) if self.M > 1 else np.zeros_like(mu[0])), var.mean(0)

    def sample(self, x, member_idx, rng):
        """One stochastic acceleration sample per row: member = member_idx[i], aleatoric noise ~ N(0, sigma_m^2)."""
        mu, var = self.moments(x)
        n = np.arange(x.shape[0])
        m = mu[member_idx, n]
        return m + np.sqrt(var[member_idx, n]) * rng.standard_normal(m.shape)
