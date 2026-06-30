import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pr2_controller.disruption_degradation import monotonic_degradation, exponential_degradation

# ---- experiment json thresholds ----------------------------------------
THETA_CRIT = 0.8
THETA_BASE = 0.72
ALPHA_CRIT = 0.15
ALPHA_BASE = 0.2

# ---- psi function selection ---------------------------------------------
PSI_FN      = monotonic_degradation #exponential_degradation #monotonic_degradation

# ---- psi-family parameters ----------------------------------------------
ALPHA_CRITS = [0.08, 0.15, 0.2, 0.3]
N_MAX       = 5
TASK        = "task"
GOAL        = "goal"

# ---- file paths ---------------------------------------------------------
HERE     = Path(__file__).resolve().parent
CSV_PATH       = HERE / "framework_correctness" / "exp9_psi.csv"
DELTA_CSV_PATH = HERE / "framework_correctness" / "exp9_delta.csv"
PSI_OUT        = str(HERE / "exp9_psi_monotonic.pdf")
PHI_OUT        = str(HERE / "exp9_psi_timeline.pdf")
DELTA_OUT      = str(HERE / "exp9_delta_timeline.pdf")


def load_psi_csv(path):
    times, psis = [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            times.append(float(row["time"]))
            psis.append(float(row["psi"]))
    return times, psis


def load_delta_csv(path):
    times, deltas, operations = [], [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            times.append(float(row["time"]))
            try:
                d = int(float(row["delta"]))
                deltas.append(d)
                operations.append("NORMAL" if d == 1 else "DISRUPTED")
            except ValueError:
                # final marker row: delta="-", operation="DONE"/"HALTED"
                deltas.append(None)
                operations.append(row.get("operation", ""))
    return times, deltas, operations


def psi_k(k, alpha_crit):
    S, tau = set(), {}
    for i in range(k):
        d = f"c{i}"; S.add(d); tau[(d, TASK)] = 2
    return PSI_FN(S, tau, {}, TASK, GOAL, alpha_crit, ALPHA_BASE)


def plot_psi_family():
    fig, ax = plt.subplots(figsize=(7.0, 5.2))
    ks = list(range(0, N_MAX + 1))
    for ac in ALPHA_CRITS:
        psis = [psi_k(k, ac) for k in ks]
        is_exp = abs(ac - ALPHA_CRIT) < 1e-9
        ax.plot(ks, psis, "-o",
                lw=3.0 if is_exp else 1.6,
                ms=8   if is_exp else 5,
                zorder=5 if is_exp else 3,
                label=rf"$\alpha_{{crit}} = {ac}$" + (r"  (exp2)" if is_exp else ""))

    ax.axhline(THETA_CRIT, color="firebrick", ls="--", lw=1.4,
               label=rf"$\theta_{{crit}} = {THETA_CRIT}$")
    ax.axhline(THETA_BASE, color="gray", ls=":", lw=1.2,
               label=rf"$\theta_{{base}} = {THETA_BASE}$")
    ax.set_xlabel(r"number of critical devices  $k = |S|$", fontsize=16)
    ax.set_ylabel(r"$\psi$   (performance)", fontsize=16)
    ax.set_title(r"$\psi = \max(0,\ 1 - k\,\alpha_{crit})$", fontsize=20)
    #ax.set_title(r"$\psi = e^{-\alpha_{crit} k_{crit}}$", fontsize=20)
    ax.set_xticks(ks)
    ax.set_xlim(-0.15, N_MAX + 0.15)
    ax.set_ylim(0, 1.03)
    ax.tick_params(axis="both", labelsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=12)
    fig.tight_layout()
    fig.savefig(PSI_OUT, dpi=150)
    plt.close(fig)
    print(f"Saved {PSI_OUT}")


def plot_psi_timeline():
    times, psis = load_psi_csv(CSV_PATH)
    t_end = max(times)

    fig, ax = plt.subplots(figsize=(9.5, 5.2))

    # threshold bands
    # psi >= theta_crit : always tolerable (gamma=1) regardless of attack type
    ax.axhspan(THETA_CRIT, 1.0,        color="tab:green",  alpha=0.12)
    # theta_base <= psi < theta_crit : tolerable ONLY for non-critical attacks
    ax.axhspan(THETA_BASE, THETA_CRIT, color="tab:orange", alpha=0.10)
    # psi < theta_base  : never tolerable (gamma=0) regardless of attack type
    ax.axhspan(0.0,        THETA_BASE, color="tab:red",    alpha=0.12)

    # threshold lines
    ax.axhline(THETA_CRIT, color="firebrick", ls="--", lw=1.6,
               label=rf"$\theta_{{crit}} = {THETA_CRIT}$")
    ax.axhline(THETA_BASE, color="gray", ls=":", lw=1.2,
               label=rf"$\theta_{{base}} = {THETA_BASE}$")

    # recorded psi
    ax.step(times, psis, where="post", color="tab:blue", lw=2.0, zorder=3,
            label=r"$\psi(t)$")
    ax.plot(times, psis, "o", color="tab:blue", ms=4, alpha=0.8, zorder=4)

    # band labels
    ax.text(t_end - 0.3, (1.0 + THETA_CRIT) / 2 - 0.02,
            r"Tolerable  ($\gamma=1$, any attack)",
            ha="right", va="center", color="green", fontsize=13, fontweight="bold")
    ax.text(t_end - 0.3, (THETA_BASE + THETA_CRIT) / 2,
            "Tolerable if non-critical attack  ($\\gamma=1$)\n"
            "Not tolerable if critical attack  ($\\gamma=0$)",
            ha="right", va="center", color="darkorange", fontsize=12, fontweight="bold")
    ax.text(t_end - 0.3, THETA_BASE / 2,
            r"Not tolerable  ($\gamma=0$, any attack)",
            ha="right", va="center", color="firebrick", fontsize=13, fontweight="bold")

    ax.set_xlabel("simulation time  [s]", fontsize=16)
    ax.set_ylabel(r"$\psi$   (performance)", fontsize=16)
    ax.set_title(r"$\psi(t)$", fontsize=20)
    ax.set_xlim(0, t_end + 1)
    ax.set_ylim(0, 1.05)
    ax.tick_params(axis="both", labelsize=14)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower left", fontsize=14)
    fig.tight_layout()
    fig.savefig(PHI_OUT, dpi=150)
    plt.close(fig)
    print(f"Saved {PHI_OUT}  ({len(times)} samples, t=0..{t_end}s)")


def plot_delta_timeline():
    times, deltas, operations = load_delta_csv(DELTA_CSV_PATH)

    # Strip the final task-result marker row (delta=None)
    final_t, final_label = None, None
    if operations and operations[-1] in ("DONE", "HALTED"):
        final_t     = times.pop()
        final_label = operations.pop()
        deltas.pop()

    t_end = max(times)

    fig, ax = plt.subplots(figsize=(11.0, 4.4))

    # Axes-fraction coordinates for data y=0 and y=1 (so blocks don't bleed
    # into the margin areas above 1 or below 0)
    ylim_lo, ylim_hi = -0.25, 1.35
    y_span   = ylim_hi - ylim_lo
    ymin_ax  = (0.0 - ylim_lo) / y_span   # data y=0 → axes fraction
    ymax_ax  = (1.0 - ylim_lo) / y_span   # data y=1 → axes fraction

    # --- vertical time-region blocks + collect transitions -------------------
    COLORS = {"NORMAL": ("#2ecc71", 0.30), "DISRUPTED": ("#e74c3c", 0.35)}
    span_start = times[0]
    span_op    = operations[0]
    transitions = []

    for i in range(1, len(times)):
        if operations[i] != span_op:
            color, alpha = COLORS.get(span_op, ("gray", 0.2))
            ax.axvspan(span_start, times[i],
                       ymin=ymin_ax, ymax=ymax_ax,
                       color=color, alpha=alpha, zorder=0)
            transitions.append((times[i], span_op, operations[i]))
            span_start = times[i]
            span_op    = operations[i]

    # draw last block up to end
    color, alpha = COLORS.get(span_op, ("gray", 0.2))
    ax.axvspan(span_start, t_end, ymin=ymin_ax, ymax=ymax_ax,
               color=color, alpha=alpha, zorder=0)

    # --- region labels centered in each block --------------------------------
    prev_boundaries = [(times[0], operations[0])]
    for t, from_op, to_op in transitions:
        prev_boundaries.append((t, to_op))
    prev_boundaries.append((t_end, None))

    for k in range(len(prev_boundaries) - 1):
        bx0 = prev_boundaries[k][0]
        bx1 = prev_boundaries[k + 1][0]
        bop = prev_boundaries[k][1]
        label_text = "Normal" if bop == "NORMAL" else "Disrupted"
        fc = "#1a7a42" if bop == "NORMAL" else "#8b0000"
        ax.text((bx0 + bx1) / 2, 0.5, label_text,
                ha="center", va="center", fontsize=13, rotation=90,
                color=fc, fontweight="bold", alpha=0.55,
                transform=ax.get_xaxis_transform(), zorder=1)

    # --- delta step plot (on top of blocks) ----------------------------------
    ax.step(times, deltas, where="post", color="black", lw=2.0, zorder=3,
            label=r"$\delta(t)$")

    # --- transition annotations: vertical dashed line + arrow + label --------
    attack_count   = 0
    recovery_count = 0
    for t, from_op, to_op in transitions:
        if from_op == "NORMAL" and to_op == "DISRUPTED":
            attack_count += 1
            ax.axvline(t, color="#c0392b", ls="--", lw=1.3, alpha=0.8, zorder=2)
            ax.annotate(
                f"Attack {attack_count}",
                xy=(t, 1.0),
                xytext=(t + 0.15, 1.12),
                fontsize=12, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.0,
                                shrinkA=0, shrinkB=2),
                zorder=5,
            )
        else:
            recovery_count += 1
            ax.axvline(t, color="#1a7a42", ls=":", lw=1.3, alpha=0.8, zorder=2)
            ax.annotate(
                f"Recovery {recovery_count}",
                xy=(t, 0.0),
                xytext=(t + 0.15, 0.18),
                fontsize=11, color="#1a7a42",
                arrowprops=dict(arrowstyle="->", color="#1a7a42", lw=1.0,
                                shrinkA=0, shrinkB=2),
                zorder=5,
            )

    # --- final task-result marker --------------------------------------------
    if final_t is not None:
        fc = "#1a7a42" if final_label == "DONE" else "#8b0000"
        ax.axvline(final_t, color=fc, ls="-", lw=2.4, zorder=5)
        ax.text(final_t - 0.3, 0.5, f"Task {final_label}",
                rotation=90, va="center", ha="right",
                color=fc, fontsize=13, fontweight="bold")

    # --- legend & axes -------------------------------------------------------
    legend_handles = [
        ax.get_lines()[0],
        Patch(color="#2ecc71", alpha=0.55, label="Normal (δ=1)"),
        Patch(color="#e74c3c", alpha=0.55, label="Disrupted  (δ=0)"),
    ]
    ax.set_xlabel("simulation time  [s]", fontsize=16)
    ax.set_ylabel(r"$\delta$  (disruption)", fontsize=16)
    ax.set_title(r"$\delta(t)$, distruption over time", fontsize=20)
    ax.set_xlim(0, (final_t or t_end) + 2)
    ax.set_ylim(-0.25, 1.35)
    ax.set_yticks([0, 1])
    ax.tick_params(axis="both", labelsize=14)
    ax.grid(axis="x", alpha=0.2)

    # Position spines at the data origin to form coordinate axes
    ax.spines["bottom"].set_position(("data", 0))
    ax.spines["left"].set_position(("data", 0))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_linewidth(1.5)
    ax.spines["left"].set_linewidth(1.5)

    # Suppress x=0 tick label to avoid duplicate "0" at origin
    ax.set_xticks([t for t in ax.get_xticks() if t > 0])

    ax.legend(handles=legend_handles, loc="upper right", fontsize=14)
    fig.tight_layout()
    fig.savefig(DELTA_OUT, dpi=150)
    plt.close(fig)
    print(f"Saved {DELTA_OUT}  ({len(times)} samples, result={final_label})")


def main():
    plot_psi_family()
    plot_psi_timeline()
    plot_delta_timeline()


if __name__ == "__main__":
    main()
