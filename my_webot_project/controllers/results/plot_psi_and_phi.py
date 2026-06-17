"""
Side-by-side view of psi and phi.

LEFT  -- psi(|S|): the monotonic non-increasing degradation function (Def. 7),
         drawn as a FAMILY of curves psi = max(0, 1 - k * alpha_crit) for several
         alpha_crit values (same style as plot_monotonic_degradation.py). The
         alpha_crit used by phi on the right is drawn bold.

RIGHT -- phi[n] = psi(S(t_n)) SAMPLED ON A FIXED CLOCK (t_n = 0, DT, 2*DT, ...)
         across a long run of N_CHANGES attack/mitigation events. At each tick
         phi moves toward the current target psi(|S|) by one discrete
         exponential step:

             phi[n] = phi[n-1]*a + psi(|S_n|)*(1 - a),   a = e^{-lambda*DT}

         lambda = LAMBDA_DEC when the target is below phi (attack, fast),
         lambda = LAMBDA_INC when it is above (mitigation, slow). The grey step
         (right axis) is |S(t)|, the number of compromised devices driving phi.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pr2_controller.disruption_degradation import monotonic_degradation

TASK = "task"
GOAL = "goal"

ALPHA_CRITS = [0.1, 0.2, 0.3, 0.4]
ALPHA_PHI = 0.2
ALPHA_BASE = 0.0

THETA_CRIT = 0.5
THETA_BASE = 0.75

LAMBDA_DEC = 1.4          # fast drop on attack
LAMBDA_INC = 0.6          # slow rise on mitigation

DT = 0.1                  # sampling period [s] -> phi observed at 10 Hz
N_MAX = 5

# ---- attack/mitigation timeline: a seeded bounded walk of |S| ---------------
N_CHANGES = 20            # number of attack/mitigation events
EVENT_SPACING = 3.0       # seconds between events
SEED = 7
PSI_OUT = "psi_monotonic.png"   # left figure: psi(|S|) family
PHI_OUT = "phi_sampled.png"     # right figure: phi(t) sampled over time


def make_events():
    """N_CHANGES events; each moves |S| by +-1/2, clamped to [0, N_MAX]."""
    rng = np.random.default_rng(SEED)
    events = [(0.0, 0, 0)]            # nominal start, |S| = 0
    k = 0
    for i in range(1, N_CHANGES + 1):
        if k <= 0:
            step = int(rng.choice([1, 2]))          # at floor -> must attack
        elif k >= N_MAX:
            step = int(rng.choice([-2, -1]))        # at ceiling -> must mitigate
        else:
            step = int(rng.choice([-2, -1, 1, 2]))
        k = int(np.clip(k + step, 0, N_MAX))
        events.append((i * EVENT_SPACING, k, 0))
    return events


EVENTS = make_events()
T_END = N_CHANGES * EVENT_SPACING + 3.0


def psi_k(k, alpha_crit):
    """psi for k compromised critical (level-2) devices."""
    S, tau = set(), {}
    for i in range(k):
        d = f"c{i}"; S.add(d); tau[(d, TASK)] = 2
    return monotonic_degradation(S, tau, {}, TASK, GOAL, alpha_crit, ALPHA_BASE)


def s_count_at(t):
    """Number of compromised devices at time t (held between events)."""
    n = EVENTS[0][1] + EVENTS[0][2]
    for (te, nc, nb) in EVENTS:
        if t >= te:
            n = nc + nb
    return n


def sample_phi():
    """phi sampled at FS = 1/DT Hz via the discrete exponential update."""
    times = np.arange(0.0, T_END + DT / 2, DT)
    counts = np.array([s_count_at(t) for t in times])
    phi = np.empty_like(times)
    v = psi_k(int(counts[0]), ALPHA_PHI)
    phi[0] = v
    for n in range(1, len(times)):
        L = psi_k(int(counts[n]), ALPHA_PHI)
        lam = LAMBDA_DEC if L < v else (LAMBDA_INC if L > v else 0.0)
        a = np.exp(-lam * DT)
        v = v * a + L * (1.0 - a)
        phi[n] = v
    return times, counts, phi


def plot_psi():
    """Figure 1: psi(|S|) family, monotonic non-increasing in the set."""
    fig, ax = plt.subplots(figsize=(7.0, 5.2))
    ks = list(range(0, N_MAX + 1))
    for ac in ALPHA_CRITS:
        psis = [psi_k(k, ac) for k in ks]
        is_phi = abs(ac - ALPHA_PHI) < 1e-9
        ax.plot(ks, psis, "-o",
                lw=3.0 if is_phi else 1.6,
                ms=8 if is_phi else 5,
                zorder=5 if is_phi else 3,
                label=rf"$\alpha_{{crit}} = {ac}$" + (r"  (used by $\phi$)" if is_phi else ""))

    ax.axhline(THETA_CRIT, color="firebrick", ls="--", lw=1.4,
               label=rf"$\theta_{{crit}} = {THETA_CRIT}$")
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


def plot_phi():
    """Figure 2: phi sampled at FS Hz over N_CHANGES events."""
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.axhspan(THETA_CRIT, 1.0, color="tab:green", alpha=0.12)
    ax.axhspan(0.0, THETA_CRIT, color="tab:red", alpha=0.12)
    ax.axhline(THETA_CRIT, color="firebrick", ls="--", lw=1.6,
               label=rf"$\theta_{{crit}} = {THETA_CRIT}$")
    ax.axhline(THETA_BASE, color="gray", ls=":", lw=1.0,
               label=rf"$\theta_{{base}} = {THETA_BASE}$")

    times, counts, phi = sample_phi()
    fs = 1.0 / DT

    # |S(t)| driving signal on a secondary axis
    ax2 = ax.twinx()
    ax2.step(times, counts, where="post", color="dimgray", lw=1.2, alpha=0.5,
             label=r"$|S(t)|$")
    ax2.set_ylabel(r"$|S(t)|$  (compromised devices)", color="dimgray")
    ax2.set_ylim(-0.2, N_MAX + 0.4)
    ax2.set_yticks(range(0, N_MAX + 1))
    ax2.tick_params(axis="y", labelcolor="dimgray")

    ax.plot(times, phi, "-", color="tab:blue", lw=1.3, zorder=3)
    ax.plot(times, phi, "o", color="tab:blue", ms=2.4, alpha=0.7, zorder=4,
            label=rf"$\phi[n]=\psi(S(t_n))$ @ {fs:.0f} Hz, $\alpha_{{crit}}={ALPHA_PHI}$")

    ax.text(T_END - 0.4, (1.0 + THETA_CRIT) / 2, r"tolerable  ($\gamma=1$)",
            ha="right", va="center", color="green", fontsize=10)
    ax.text(T_END - 0.4, THETA_CRIT / 2, r"not tolerable  ($\gamma=0$)",
            ha="right", va="center", color="firebrick", fontsize=10)
    ax.set_xlabel("time  [s]")
    ax.set_ylabel(r"$\phi$   (performance)")
    ax.set_title(rf"$\phi[n]=\psi(S(t_n))$ — {N_CHANGES} events, sampled at "
                 rf"{fs:.0f} Hz ({len(times)} samples)")
    ax.set_xlim(0, T_END)
    ax.set_ylim(0, 1.03)
    ax.set_zorder(ax2.get_zorder() + 1)     # keep phi above the |S| step
    ax.patch.set_visible(False)
    ax.grid(True, alpha=0.3)

    # merged legend (phi + thresholds from ax, |S| from ax2)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="lower left", fontsize=8)

    fig.tight_layout()
    fig.savefig(PHI_OUT, dpi=150)
    plt.close(fig)
    print(f"Saved {PHI_OUT}  ({N_CHANGES} events, {len(times)} samples at {fs:.0f} Hz)")


def main():
    plot_psi()
    plot_phi()


if __name__ == "__main__":
    main()
