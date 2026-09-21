#!/usr/bin/env python
"""Workflow (Fig. 1) and architecture (Fig. 2) diagrams that mirror the code in this repository."""
import argparse, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams.update({"font.size": 7.5, "savefig.dpi": 300})
FILL, EDGE, ACC = "#f1f0ec", "#52514e", "#dbe8f8"


def box(ax, x, y, w, h, text, fc=FILL, bold=False, fs=7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01,rounding_size=0.02", fc=fc, ec=EDGE, lw=0.8))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)


def arrow(ax, p, q, text=None, rad=0.0, off=(0, 0.03)):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, lw=0.9, color=EDGE, connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], text, ha="center", va="bottom", fontsize=6.5, style="italic")


def workflow(path):
    fig, ax = plt.subplots(figsize=(6.4, 3.1)); ax.set_xlim(-0.02, 1.02); ax.set_ylim(0, 1); ax.axis("off")
    w, h = 0.226, 0.26
    xs = [0.0, 0.258, 0.516, 0.774]
    top = ["Sample conditions\n(ID or OOD friction,\nstiffness, payload)",
           "Plant simulation\n(MuJoCo, random trot\nschedule, 200 Hz)",
           "Nominal twin step\nfrom the plant state;\ncontact flags c",
           "Residual target a$_{res}$\n(v$_{plant}$\u2019 \u2212 v$_{nom}$\u2019)/\u0394t"]
    bot = ["Train models\n(ensemble NLL, MSE,\ndata-only MLP)",
           "Multi-step rollouts\n(25 steps, ID + OOD):\nRMSE, coverage, ECE",
           "EnKF synchronisation\nwith noisy sensors:\nscaled state error",
           "Outputs: state,\ncontact flags,\nuncertainty"]
    for x, t in zip(xs, top):
        box(ax, x, 0.66, w, h, t)
    for x, t in zip(xs, bot):
        box(ax, x, 0.10, w, h, t, ACC)
    for i in range(3):
        arrow(ax, (xs[i] + w, 0.79), (xs[i + 1], 0.79)); arrow(ax, (xs[i] + w, 0.23), (xs[i + 1], 0.23))
    x4, x1 = xs[3] + w / 2, xs[0] + w / 2
    ax.plot([x4, x4, x1], [0.66, 0.50, 0.50], color=EDGE, lw=0.9)
    arrow(ax, (x1, 0.50), (x1, 0.36))
    ax.text(0.5, 0.52, "training data", ha="center", va="bottom", fontsize=6.5, style="italic")
    ax.text(0.0, 0.99, "Data generation", fontsize=7.5, fontweight="bold", va="top")
    ax.text(0.995, 0.44, "Learning and evaluation", fontsize=7.5, fontweight="bold", va="top", ha="right")
    fig.savefig(path, bbox_inches="tight", pad_inches=0.05); plt.close(fig)


def architecture(path):
    fig, ax = plt.subplots(figsize=(6.4, 3.4)); ax.set_xlim(-0.02, 1.02); ax.set_ylim(0, 1); ax.axis("off")
    w, h = 0.27, 0.20
    A, B = 0.74, 0.40
    box(ax, 0.02, A, w, h, "Twin state and torque\n(q, v, \u03c4)")
    box(ax, 0.365, A, w, h, "Nominal physics core\n(MuJoCo, nominal\nparameters)")
    box(ax, 0.71, A, w, h, "Nominal next state\n(q$_{nom}$\u2019, v$_{nom}$\u2019)")
    box(ax, 0.02, B, w, h, "Residual ensemble\n(M = 5): mean \u03bc$_m$,\nvariance \u03c3$_m^2$ of a", ACC)
    box(ax, 0.365, B, w, h, "Correction\nv\u2019 = v$_{nom}$\u2019 + a\u0394t\nq\u2019 = q$_{nom}$\u2019 + a\u0394t\u00b2/2")
    box(ax, 0.71, B, w, h, "Twin state (q\u2019, v\u2019)\nand predictive\nvariance", ACC)
    box(ax, 0.10, 0.03, 0.80, 0.20, "Ensemble Kalman filter (64 particles): propagate with the twin step;\nprocess noise = base + \u03ba \u00b7 ensemble variance; update with noisy\njoint positions/velocities, gravity direction and gyro", ACC)
    arrow(ax, (0.29, A + h / 2), (0.365, A + h / 2))
    arrow(ax, (0.635, A + h / 2), (0.71, A + h / 2))
    arrow(ax, (0.155, A), (0.155, B + h), "x, \u03c4", off=(0.03, -0.01))
    arrow(ax, (0.40, A), (0.29, B + h), "contact flags c", off=(0.03, 0.0))
    arrow(ax, (0.50, A), (0.50, B + h), "nominal state", off=(0.075, -0.01))
    arrow(ax, (0.29, B + h / 2), (0.365, B + h / 2), "a", off=(0, 0.01))
    arrow(ax, (0.635, B + h / 2), (0.71, B + h / 2))
    arrow(ax, (0.845, B), (0.75, 0.23), "twin step", off=(0.065, 0.0))
    fig.savefig(path, bbox_inches="tight", pad_inches=0.05); plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="results/summary"); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    workflow(f"{a.out}/fig1_workflow.png"); architecture(f"{a.out}/fig2_architecture.png")
