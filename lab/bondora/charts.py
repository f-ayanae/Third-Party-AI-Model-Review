"""Charts for the Bondora proxy run (aggregates only)."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "out" / "bondora" / "bondora_proxy"
NAVY, BLUE, ORANGE, INK, MUTED, GRID = "#111111", "#b3b3b3", "#a8452c", "#111111", "#6b6b6b", "#e6e6e6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "figure.dpi": 200})

summary = json.loads((src / "summary.json").read_text())
windows = {"reference": summary["reference"]["window"], "out_of_time": summary["out_of_time"]["window"]}
ro = pd.read_csv(src / "rank_ordering.csv")
ro = ro[~ro["suppressed"]]
grades = [g for g in ["AA", "A", "B", "C", "D", "E", "F", "G"] if g in set(ro.grade)]
fig, ax = plt.subplots(figsize=(6.6, 3.0))
for i, (lab, col, off) in enumerate([("reference", BLUE, -0.17), ("out_of_time", ORANGE, 0.17)]):
    d = ro[ro["sample"] == lab].set_index("grade").reindex(grades)
    x = [j + off for j in range(len(grades))]
    ax.bar(x, d.observed_dr * 100, width=0.32, color=col, zorder=3,
           label=("Reference " if lab == "reference" else "Out-of-time ") + windows[lab])
    ax.errorbar(x, d.observed_dr * 100, yerr=[(d.observed_dr - d.ci_low) * 100, (d.ci_high - d.observed_dr) * 100],
                fmt="none", ecolor=INK, elinewidth=0.8, capsize=2, zorder=4)
ax.set_xticks(range(len(grades)), grades)
ax.set_ylabel("12-month default rate, % (95% interval)")
oot = ro[ro["sample"] == "out_of_time"].set_index("grade").reindex(grades)
brk = next((j for j in range(1, len(grades)) if oot.observed_dr.iloc[j] < oot.observed_dr.iloc[j - 1]), None)
if brk is not None:  # point at the first out-of-time grade that defaults less than the grade before it
    ax.annotate(f"{grades[brk]} below {grades[brk - 1]}: rank-ordering\nbreaks out of time", xy=(brk + 0.17, oot.observed_dr.iloc[brk] * 100 + 1),
                xytext=(brk - 2.6, oot.observed_dr.max() * 100 + 5), fontsize=7.5, color=INK,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.legend(frameon=False, fontsize=7.5, loc="upper left")
ax.grid(axis="y", color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(src / "chart_rank_ordering.png"); plt.close(fig)

seg = pd.read_csv(src / "segments.csv")
seg = seg[~seg["suppressed"]].copy()
names = {"country": "Country", "income_band": "Income (EUR/month)", "term_band": "Term"}
seg["label"] = seg.apply(lambda r: f"{names[r.dimension]}: {r.segment}", axis=1)
seg = seg.iloc[::-1]
fig, ax = plt.subplots(figsize=(6.6, 3.6))
y = range(len(seg))
ax.axvline(1, color=MUTED, lw=0.8, ls=(0, (3, 3)))
cols = [ORANGE if lo > 1.1 else (BLUE if hi < 0.95 else NAVY) for lo, hi in zip(seg.o_to_e_low, seg.o_to_e_high)]
ax.hlines(list(y), seg.o_to_e_low, seg.o_to_e_high, color=cols, lw=2, zorder=3)
ax.scatter(seg.o_to_e, list(y), color=cols, s=22, zorder=4)
for yy, (v, hi, n) in enumerate(zip(seg.o_to_e, seg.o_to_e_high, seg.n)):
    ax.text(hi + 0.05, yy, f"{v:.2f}  (n={int(n):,})", va="center", fontsize=7, color=INK)
ax.set_yticks(list(y), seg.label, fontsize=7.6)
ax.set_ylim(-0.6, len(seg) + 0.2)
ax.set_xlim(0.5, 3.6)
ax.set_xlabel(f"Observed / expected 12-month defaults, {windows['out_of_time']} (95% interval)")
ax.text(3.55, len(seg) - 0.45, "Orange: grade understates risk.  Blue: grade overstates risk.", ha="right", fontsize=7, color=MUTED)
ax.tick_params(axis="y", length=0)
ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(src / "chart_segments_oe.png"); plt.close(fig)
print("charts written to", src)
