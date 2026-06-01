import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch



# Used for tolerable degradation (that sweep and alpha = [0.1, 0.2, 0.3])
def plot_multiple_fig():
    # Filer
    files = {
        "α = 0.1": "task1/alpha_crit0.1_theta_crit_sweep.csv",
        "α = 0.2": "task1/alpha_base0.2_theta_base_sweep.csv",
        "α = 0.3": "task1/alpha_base0.3_theta_base_sweep.csv"
    }
    # Färgkarta
    cmap = ListedColormap(["#ee3e32", "#f68838"])  # 0=röd, 1=orange

    # Skapa subplot
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)

    for ax, (title, file) in zip(axes, files.items()):
        df = pd.read_csv(file)
        pivot = df.pivot(index="k", columns="theta_base", values="gamma")

        im = ax.imshow(
            pivot,
            aspect="auto",
            cmap=cmap,
            vmin=0,
            vmax=1,
            origin="lower"   # 🔥 rätt håll på y-axeln
        )

        # 🔲 grid (rutor)
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_yticks(range(len(pivot.index)))

        ax.set_xticks([x - 0.5 for x in range(1, len(pivot.columns))], minor=True)
        ax.set_yticks([y - 0.5 for y in range(1, len(pivot.index))], minor=True)

        ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)

        for i in range(pivot.shape[0]):       # rader (k)
            for j in range(pivot.shape[1]):   # kolumner (theta)
                value = pivot.values[i, j]

                ax.text(
                    j, i,
                    str(int(value)),         # skriv 0 eller 1
                    ha="center",
                    va="center",
                    color="black",           # textfärg
                    fontsize=8
                )

        ax.set_title(title)
        ax.set_xlabel("theta_base")

        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels([round(v, 2) for v in pivot.columns], rotation=45)

        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)

    # Endast vänstra plotten får y-label
    axes[0].set_ylabel("Number of attacked devices (k)")

    # Legend (gemensam)
    #legend_elements = [
    #    Patch(facecolor="#f68838", label="γ = 1"),
    #    Patch(facecolor="#ee3e32", label="γ = 0")
    #]
    #fig.legend(handles=legend_elements, loc="center right", bbox_to_anchor=(1.02, 0.5) )

    plt.tight_layout()
    plt.show()

# Used for tolerable degradation (that sweep and alpha = [0.1, 0.2, 0.3])
def plot_one_fig():
    # ===== välj fil =====
    file = "task1/alpha_crit0.1_theta_crit_sweep.csv"

    # Läs data
    df = pd.read_csv(file)

    # Pivot
    pivot = df.pivot(index="k", columns="theta_crit", values="gamma")

    # Färger (0 = röd, 1 = orange)
    cmap = ListedColormap(["#ee3e32", "#f68838"])

    # Plot
    fig, ax = plt.subplots(figsize=(8, 4))

    im = ax.imshow(
        pivot,
        aspect="auto",
        cmap=cmap,
        vmin=0,
        vmax=1,
        origin="lower"
    )

    # Axlar
    ax.set_xlabel("θ_crit ")
    ax.set_ylabel("Number of attacked devices (k)")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([round(v, 2) for v in pivot.columns], rotation=45)

    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)

    # ===== grid (rutor) =====
    ax.set_xticks([x - 0.5 for x in range(1, len(pivot.columns))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(pivot.index))], minor=True)

    ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)

    # ===== skriv 0/1 i varje ruta =====
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            value = pivot.values[i, j]
            ax.text(
                j, i,
                str(int(value)),
                ha="center",
                va="center",
                color="black",
                fontsize=8
            )

    # Titel (valfri)
    ax.set_title("α = 0.1")

    plt.tight_layout()
    plt.show()

plot_one_fig()



#--------------------------------------------------------
'''

# ===== Läs data =====
df = pd.read_csv("task1/detection_90.csv")

# Om kolumnnamnet inte är "devices", ta sista kolumnen:
if "devices" not in df.columns:
    df.rename(columns={df.columns[-1]: "devices"}, inplace=True)

# ===== Robust parser =====
def classify(row):
    s = str(row["devices"])

    # ta bort { } och whitespace
    s = s.replace("{", "").replace("}", "").strip()

    if s == "" or s.lower() == "nan":
        return "None"

    # dela upp på komma
    parts = [p.strip() for p in s.split(",")]

    lw = "LW" in parts
    rw = "RW" in parts

    #if lw and rw:
    #    return "Both"
    if lw or rw:
        return "One"
    else:
        return "None"

df["detection_category"] = df.apply(classify, axis=1)

# ===== Debug (kolla att det funkar) =====
print(df[["devices", "detection_category"]].head(10))

# ===== Räkna =====
counts = df["detection_category"].value_counts(normalize=True)
counts = counts.reindex(["None", "One"]).fillna(0)

# ===== Plot =====
plt.figure(figsize=(6, 4))

colors = ["#d73027", "#1a9850"]  # None, One, Both
bars = plt.bar(counts.index, counts.values, color=colors)

for bar, val in zip(bars, counts.values):
    plt.text(bar.get_x() + bar.get_width()/2, val,
             f"{val*100:.1f}%",
             ha='center', va='bottom')

plt.ylabel("Probability")
plt.xlabel("Detected Devices")
plt.title("IDS Detection Rate 70%")
plt.ylim(0, 1)
plt.grid(axis='y', linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()
'''

'''

# -----------------------------------------------------------------------------------
# Lägg in dina filer här
import numpy as np
files = {
    "70%": "task1/detection_70_attackall.csv",
    "80%": "task1/detection_80_attackall.csv",
    "90%": "task1/detection_90_attackall.csv"
}

rates = []
means = []
errors = []

n = 20  # antal runs

for rate, file in files.items():
    df = pd.read_csv(file)
    p = (df["delta"] == 0).mean()

    se = np.sqrt(p * (1 - p) / n)

    rates.append(rate)
    means.append(p)
    errors.append(se)

plt.figure(figsize=(6,4))
plt.bar(rates, means, yerr=errors, capsize=5)

plt.xlabel("Detection Rate (%)")
plt.ylabel("P(δ = 0)")
plt.title("Disruption Probability with Uncertainty")
plt.ylim(0,1)
plt.grid(axis='y')

plt.show()
'''