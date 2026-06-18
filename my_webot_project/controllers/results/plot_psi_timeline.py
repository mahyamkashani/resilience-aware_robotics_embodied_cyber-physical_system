"""
Side-by-side view of psi theory and the recorded psi timeline from exp2_psi.csv.

LEFT  -- psi(|S|): the monotonic non-increasing degradation function (Def. 7),
         drawn as a family of curves psi = max(0, 1 - k * alpha_crit) for
         several alpha_crit values. The alpha_crit used in experiment2 is bold.

RIGHT -- psi(t) recorded from exp2_psi.csv: the actual psi sampled once per
         simulation second. Threshold lines and tolerable / not-tolerable bands
         use the values from experiment2.json.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pr2_controller.disruption_degradation import monotonic_degradation

# ---- experiment2.json thresholds ----------------------------------------
THETA_CRIT = 0.99
THETA_BASE = 0.75
ALPHA_CRIT = 0.4
ALPHA_BASE = 0.05

# ---- psi-family parameters ----------------------------------------------
ALPHA_CRITS = [0.3, 0.4, 0.5, 0.6]
N_MAX       = 5
TASK        = "task"
GOAL        = "goal"

# ---- file paths ---------------------------------------------------------
HERE     = Path(__file__).resolve().parent
CSV_PATH = HERE / "framework_correctness" / "exp6_psi.csv"
PSI_OUT  = str(HERE / "exp6_psi_monotonic.pdf")
PHI_OUT  = str(HERE / "exp6_psi_timeline.pdf")


def load_psi_csv(path):
    times, psis = [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            times.append(float(row["time"]))
            psis.append(float(row["psi"]))
    return times, psis


def psi_k(k, alpha_crit):
    S, tau = set(), {}
    for i in range(k):
        d = f"c{i}"; S.add(d); tau[(d, TASK)] = 2
    return monotonic_degradation(S, tau, {}, TASK, GOAL, alpha_crit, ALPHA_BASE)


def plot_psi_family():
    """Left figure: psi(|S|) family, monotonic non-increasing."""
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
    ax.set_xlabel(r"number of disrupted (critical) devices  $k = |S|$")
    ax.set_ylabel(r"$\psi$   (performance)")
    ax.set_title(r"$\psi = \max(0,\ 1 - k\,\alpha_{crit})$  — monotonic non-increasing")
    ax.set_xticks(ks)
    ax.set_xlim(-0.15, N_MAX + 0.15)
    ax.set_ylim(0, 1.03)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(PSI_OUT, dpi=150)
    plt.close(fig)
    print(f"Saved {PSI_OUT}")


def plot_psi_timeline():
    """Right figure: recorded psi(t) from exp2_psi.csv."""
    times, psis = load_psi_csv(CSV_PATH)
    t_end = max(times)

    fig, ax = plt.subplots(figsize=(9.5, 5.2))

    # threshold bands
    ax.axhspan(THETA_CRIT, 1.0,        color="tab:green",  alpha=0.12)
    ax.axhspan(THETA_BASE, THETA_CRIT, color="tab:orange", alpha=0.10)
    ax.axhspan(0.0,        THETA_BASE, color="tab:red",    alpha=0.12)

    # threshold lines
    ax.axhline(THETA_CRIT, color="firebrick", ls="--", lw=1.6,
               label=rf"$\theta_{{crit}} = {THETA_CRIT}$")
    ax.axhline(THETA_BASE, color="gray", ls=":", lw=1.2,
               label=rf"$\theta_{{base}} = {THETA_BASE}$")

    # recorded psi
    ax.step(times, psis, where="post", color="tab:blue", lw=2.0, zorder=3,
            label=r"$\psi(t)$ — exp2")
    ax.plot(times, psis, "o", color="tab:blue", ms=4, alpha=0.8, zorder=4)

    # band labels
    ax.text(t_end - 0.5, (1.0 - 0.05 + THETA_CRIT) / 2,
            r"resilient  ($\gamma=1$, $\delta=1$)",
            ha="right", va="center", color="green", fontsize=11)
    ax.text(t_end - 0.6, (THETA_BASE + THETA_CRIT) / 2,
            r"tolerable degradation  ($\gamma=1$, $\delta=0$)",
            ha="right", va="center", color="darkorange", fontsize=11)
    ax.text(t_end - 0.6, THETA_BASE / 2,
            r"not tolerable  ($\gamma=0$)",
            ha="right", va="center", color="firebrick", fontsize=11)

    ax.set_xlabel("simulation time  [s]")
    ax.set_ylabel(r"$\psi$   (performance)")
    ax.set_title(r"$\psi(t)$ over time: exp5  (sampled 50 Hz from simulation)")
    ax.set_xlim(0, t_end + 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    fig.savefig(PHI_OUT, dpi=150)
    plt.close(fig)
    print(f"Saved {PHI_OUT}  ({len(times)} samples, t=0..{t_end}s)")


def main():
    plot_psi_family()
    plot_psi_timeline()


if __name__ == "__main__":
    main()
