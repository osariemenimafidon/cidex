"""08 — Publication figures.

Every value is read from the built tables or stats.json; nothing is hard-coded.
Figures carry a DRAFT stamp until the verification gate is signed.
"""
import json, os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MultipleLocator

OUT, FIG = "data/processed", "figures"
os.makedirs(FIG, exist_ok=True)
S = json.load(open(f"{OUT}/stats.json"))

HWY, NR, GRID, INK, MUTE = "#2a78d6", "#eb6834", "#d8dce2", "#1a1d21", "#6b7280"
plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": MUTE, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": MUTE, "ytick.color": MUTE,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
})
DRAFT = not os.path.exists(".gate-signed")
thou = FuncFormatter(lambda v, p: f"{int(v):,}")


def stamp(fig):
    if DRAFT:
        fig.text(0.99, 0.01, "DRAFT — NOT VERIFIED", ha="right", va="bottom",
                 fontsize=7, color="#b45309", alpha=.85, weight="bold")


def save(fig, name):
    stamp(fig)
    for ext in ("png", "pdf"):
        fig.savefig(f"{FIG}/{name}.{ext}")
    plt.close(fig)
    print(f"  {name}.png / .pdf")


fam = pd.read_csv(f"{OUT}/cidex_family.csv", low_memory=False)
em = pd.read_csv(f"{OUT}/cidex_emissions.csv", low_memory=False)
car = pd.read_csv(f"{OUT}/cidex_carryover.csv")

# --- Fig 1: families per model year, separate scales -------------------------
fig, axes = plt.subplots(2, 1, figsize=(6.4, 4.2), sharex=True,
                         gridspec_kw={"hspace": .28})
COV = S["model_year_coverage"]
for ax, (panel, col) in zip(axes, [("nonroad", NR), ("highway", HWY)]):
    s = fam[fam.panel.eq(panel)].groupby("model_year").size().sort_index()
    s = s[s > 0]                      # a panel's uncovered years are absent, not zero
    byyear = COV[panel]["by_year"]
    bad = [int(y) for y, v in byyear.items() if v["coverage"] != "complete"]

    # Shade the structurally incomplete years. Drawing them unmarked would let a
    # reader mistake an archive boundary for an industry collapse.
    for y in bad:
        ax.axvspan(y - .5, y + .5, color="#b45309", alpha=.10, lw=0, zorder=0)
    good = s[~s.index.isin(bad)]
    ax.plot(good.index, good.values, color=col, lw=2, marker="o", ms=3.6,
            mfc="white", mew=1.4, mec=col, zorder=3)
    # incomplete years plotted, but hollow and unconnected
    for y in bad:
        ax.plot([y], [s.loc[y]], marker="o", ms=3.6, mfc="white", mec="#b45309",
                mew=1.4, ls="none", zorder=3)
    ax.set_title(panel.capitalize(), loc="left", fontsize=9.5, weight="bold", pad=6)
    ax.grid(axis="y", color=GRID, lw=.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(thou)
    ax.set_ylim(0, s.max() * 1.18)
# Model years are integers; matplotlib's default locator produces half-years.
allyears = sorted(fam.model_year.unique())
for ax in axes:
    ax.set_xlim(min(allyears) - .8, max(allyears) + .8)
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{int(v)}"))
axes[1].set_xlabel("Model year")
fig.supylabel("Engine families certified", fontsize=9, x=.02)
fig.suptitle("Certified engine families per model year", x=.02, ha="left",
             fontsize=11, weight="bold", y=1.04)
fig.text(.02, .935, "Shaded years are structurally incomplete and excluded from the line: "
                    "EPA archive files\nnot ingested at the left edge, still being certified "
                    "at the right. See LIMITATIONS §4.",
         fontsize=7.5, color=MUTE, ha="left")
save(fig, "fig1_families_per_year")

# --- Fig 2: records by pollutant ---------------------------------------------
pc = (em.groupby(["pollutant", "panel"]).size().unstack(fill_value=0)
        .assign(total=lambda d: d.sum(axis=1)).sort_values("total"))
fig, ax = plt.subplots(figsize=(6.4, 4.0))
y = range(len(pc))
ax.barh(y, pc.get("highway", 0), color=HWY, height=.68, label="Highway")
ax.barh(y, pc.get("nonroad", 0), left=pc.get("highway", 0), color=NR,
        height=.68, label="Nonroad")
for i, v in enumerate(pc.total):
    ax.text(v + pc.total.max() * .012, i, f"{v:,}", va="center", fontsize=7.5, color=MUTE)
ax.set_yticks(list(y)); ax.set_yticklabels(pc.index, fontsize=8.5)
ax.set_xlim(0, pc.total.max() * 1.14)
ax.xaxis.set_major_formatter(thou)
ax.grid(axis="x", color=GRID, lw=.8); ax.set_axisbelow(True)
ax.set_xlabel("Emission records")
ax.legend(frameon=False, loc="lower right", fontsize=8.5)
ax.set_title("Emission records by pollutant", loc="left", fontsize=11, weight="bold", pad=10)
save(fig, "fig2_pollutant_coverage")

# --- Fig 3: carryover lineage depth ------------------------------------------
d = car.lineage_depth.value_counts().sort_index()
fig, ax = plt.subplots(figsize=(6.4, 3.2))
ax.bar(d.index, d.values, color=HWY, width=.74)
ax.set_xticks(list(d.index))
ax.grid(axis="y", color=GRID, lw=.8); ax.set_axisbelow(True)
ax.yaxis.set_major_formatter(thou)
ax.set_xlabel("Carryover steps to lineage root (model years)")
ax.set_ylabel("Engine families")
ax.set_title("Nonroad carryover lineage depth", loc="left", fontsize=11, weight="bold", pad=10)
ex = S["carryover_longest_example"]
ax.text(.98, .93, f"{S['carryover_distinct_lineages']:,} distinct lineages · deepest "
                  f"{S['carryover_depth_max']} years\n{ex['lineage_root']} → {ex['engine_family']}",
        transform=ax.transAxes, ha="right", va="top", fontsize=7.5, color=MUTE)
save(fig, "fig3_lineage_depth")

# --- Fig 4: nonroad tier migration -------------------------------------------
nr = fam[fam.panel.eq("nonroad")]
tt = nr.groupby(["model_year", "tier"]).size().unstack(fill_value=0)
order = [t for t in ["Tier 2", "Tier 3", "Interim Tier 4", "Tier 4 (Final or Phase In)"]
         if t in tt.columns]
tt = tt[order]
share = tt.div(tt.sum(axis=1), axis=0) * 100
fig, ax = plt.subplots(figsize=(6.4, 3.6))
shades = ["#c9d6e8", "#8fb3dc", "#5591cf", HWY]
ax.stackplot(share.index, *[share[c] for c in order], labels=order,
             colors=shades[-len(order):], edgecolor="white", linewidth=.6)
ax.set_xlim(share.index.min(), share.index.max())
ax.set_ylim(0, 100)
ax.set_ylabel("Share of families certified (%)")
ax.set_xlabel("Model year")
ax.legend(frameon=False, fontsize=8, loc="lower left", ncol=2)
ax.set_title("Nonroad tier migration", loc="left", fontsize=11, weight="bold", pad=10)
ax.text(.99, .04, f"Final year partial (MY{share.index.max()})", transform=ax.transAxes,
        ha="right", fontsize=7.5, color="white")
save(fig, "fig4_tier_migration")

print(f"\n{len(os.listdir(FIG))} files in {FIG}/")
