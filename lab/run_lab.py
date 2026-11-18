"""Lab A: what the published points table does, tested on constructed profiles.

Outputs (lab/out/): archetypes.csv, ceiling.csv, sensitivity.csv,
monotonicity.csv, weights.csv and four PNG charts.
No synthetic population is used: profiles are hand-built, documented cases.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from calculator import (TIME_CRITERIA, CreditStatus, Payment, Profile,  # noqa: E402
                        max_points, points, score, score_class, table)

OUT = Path(__file__).with_name("out")
OUT.mkdir(exist_ok=True)

NAVY, BLUE, ORANGE, AQUA = "#111111", "#9a9a9a", "#a8452c", "#6b6b6b"  # editorial monochrome, one rust accent
INK, MUTED, GRID = "#1b1b1b", "#5b6573", "#e3e6ea"
CLASS_LINES = [(642, "Class 3 from 642"), (709, "Class 2 from 709"), (776, "Class 1 from 776")]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 200,
})

# ---------------------------------------------------------------- archetypes
ARCHETYPES: dict[str, tuple[str, Profile]] = {
    "A1 Established homeowner": (
        "45, same address 20+ years, mortgage, old card, no new credit",
        Profile(bank_contract_months=300, credit_card_months=240, address_months=300,
                credit_status=CreditStatus.completed_positive, real_estate=True,
                identity_checked=True)),
    "A2 Established renter, moved 6 months ago": (
        "45, long bank and card history, recent house move",
        Profile(bank_contract_months=300, credit_card_months=200, address_months=6,
                nonbank_inquiries_12m=1, credit_status=CreditStatus.completed_positive,
                identity_checked=True)),
    "A3 Under-25, first job": (
        "22, bank contract since 18, no credit card, moved for work a year ago",
        Profile(bank_contract_months=48, credit_card_months=None, address_months=12,
                bank_card_inquiries_12m=1, nonbank_inquiries_12m=1, identity_checked=True)),
    "A4 Resident in Germany 14 months": (
        "35, employed, account opened on arrival, no card, phone contract",
        Profile(bank_contract_months=14, credit_card_months=None, address_months=14,
                nonbank_inquiries_12m=1, identity_checked=True)),
    "A5 Resident in Germany 8 months": (
        "30, employed, account and card applications on arrival, phone and energy contracts",
        Profile(bank_contract_months=8, credit_card_months=None, address_months=8,
                bank_card_inquiries_12m=1, nonbank_inquiries_12m=2, identity_checked=True)),
    "A6 Under-25 after a 60-month Ratenkredit": (
        "A3 immediately after taking a 60-month instalment loan",
        Profile(bank_contract_months=48, credit_card_months=None, address_months=12,
                bank_card_inquiries_12m=1, nonbank_inquiries_12m=1, instalment_loans_12m=1,
                longest_remaining_term_months=60, credit_status=CreditStatus.open_or_negative,
                identity_checked=True)),
}


def write_csv(name: str, rows: list[dict]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def run_archetypes() -> list[dict]:
    rows = []
    for name, (desc, p) in ARCHETYPES.items():
        s_step, s_int = score(p, "step"), score(p, "interp")
        s_no_addr = score(p, "step", exclude=("c04_current_address",))
        pts = points(p, "step")
        rows.append({"archetype": name, "description": desc, "score_step": s_step,
                     "score_interp": s_int, "class_step": score_class(s_step),
                     "class_interp": score_class(s_int),
                     "time_criteria_points": sum(pts[c] for c in TIME_CRITERIA),
                     "address_points": pts["c04_current_address"],
                     "score_without_address_criterion": s_no_addr})
    write_csv("archetypes.csv", rows)
    return rows


# ---------------------------------------------------------------- ceiling
def ceiling_profile(m: int) -> Profile:
    """Best attainable profile after m months in the German credit file,
    with perfect payment behaviour, no mortgage, address age = m."""
    return Profile(
        bank_contract_months=m,
        credit_card_months=None,  # resolved below by taking the better option
        address_months=m,
        bank_card_inquiries_12m=1 if m < 12 else 0,  # account opening counts within 12 months
        credit_status=CreditStatus.completed_positive if m >= 24 else CreditStatus.no_instalment_loan,
        identity_checked=True)


def best_score(m: int, reading: str) -> float:
    p_none = ceiling_profile(m)
    p_card = p_none.model_copy(update={"credit_card_months": m})
    return max(score(p_none, reading), score(p_card, reading))


def run_ceiling() -> list[dict]:
    rows = []
    for m in range(0, 241, 3):
        rows.append({"months_in_file": m, "years": round(m / 12, 2),
                     "ceiling_step": best_score(m, "step"),
                     "ceiling_interp": best_score(m, "interp"),
                     "ceiling_upper": best_score(m, "upper")})
    write_csv("ceiling.csv", rows)
    return rows


def first_month_reaching(rows, col, thr):
    for r in rows:
        if r[col] >= thr:
            return r["months_in_file"]
    return None


# ---------------------------------------------------------------- sensitivity
def run_sensitivity() -> list[dict]:
    bases = {"A2": ARCHETYPES["A2 Established renter, moved 6 months ago"][1],
             "A3": ARCHETYPES["A3 Under-25, first job"][1]}
    events = {
        "New credit card (one inquiry; a first card replaces the no-card points)":
            lambda p: p.model_copy(update={"bank_card_inquiries_12m": p.bank_card_inquiries_12m + 1,
                                           "credit_card_months": p.credit_card_months if p.credit_card_months is not None else 0}),
        "One more non-bank inquiry":
            lambda p: p.model_copy(update={"nonbank_inquiries_12m": p.nonbank_inquiries_12m + 1}),
        "Takes 36-month Ratenkredit":
            lambda p: p.model_copy(update={"instalment_loans_12m": 1, "longest_remaining_term_months": 36,
                                           "credit_status": CreditStatus.open_or_negative}),
        "Takes 60-month Ratenkredit":
            lambda p: p.model_copy(update={"instalment_loans_12m": 1, "longest_remaining_term_months": 60,
                                           "credit_status": CreditStatus.open_or_negative}),
        "Takes 96-month Ratenkredit":
            lambda p: p.model_copy(update={"instalment_loans_12m": 1, "longest_remaining_term_months": 96,
                                           "credit_status": CreditStatus.open_or_negative}),
        "Moves house": lambda p: p.model_copy(update={"address_months": 0}),
        "Payment disruption settled within the last year":
            lambda p: p.model_copy(update={"payment": Payment.resolved_under_1y}),
    }
    rows = []
    for bname, base in bases.items():
        b = score(base)
        for ename, f in events.items():
            new = score(f(base))
            rows.append({"base": bname, "event": ename, "before": b, "after": new,
                         "delta": round(new - b, 1), "class_before": score_class(b),
                         "class_after": score_class(new)})
    write_csv("sensitivity.csv", rows)
    return rows


# ---------------------------------------------------------------- monotonicity
def run_monotonicity() -> list[dict]:
    rows = []
    for c in table()["criteria"]:
        if c["kind"] == "time":
            vals = [k[1] for k in c["knots"]]
            ok = all(b >= a for a, b in zip(vals, vals[1:]))
            entry = (c.get("none") is not None and c["none"] > c["knots"][0][1])
            rows.append({"criterion": c["label"], "direction": "older is better",
                         "monotonic": ok, "entry_dip": entry,
                         "note": f"holding none earns {c['none']} vs {c['knots'][0][1]} for a new product" if entry else ""})
        elif c["kind"] == "term":
            vals = [k[1] for k in c["knots"]]
            rows.append({"criterion": c["label"], "direction": "longer remaining term is worse",
                         "monotonic": all(b <= a for a, b in zip(vals, vals[1:])), "entry_dip": False,
                         "note": "no loan earns the maximum"})
        elif c["kind"] == "count":
            vals = c["values"] + [c["floor"]]
            rows.append({"criterion": c["label"], "direction": "more is worse",
                         "monotonic": all(b <= a for a, b in zip(vals, vals[1:])), "entry_dip": False, "note": ""})
        elif c["id"] == "c01_payment_disruptions":
            o = c["options"]
            seq = [o["resolved_under_1y"], o["resolved_1y_to_2y"], o["resolved_2y_to_3y"], o["none"]]
            rows.append({"criterion": c["label"], "direction": "longer since settlement is better",
                         "monotonic": all(b >= a for a, b in zip(seq, seq[1:])), "entry_dip": False,
                         "note": "open disruption: no score"})
        elif c["id"] == "c10_credit_status":
            rows.append({"criterion": c["label"], "direction": "categorical",
                         "monotonic": True, "entry_dip": True,
                         "note": "an open loan earns 0, below having no loan (9)"})
        else:
            rows.append({"criterion": c["label"], "direction": "binary", "monotonic": True,
                         "entry_dip": False, "note": ""})
    write_csv("monotonicity.csv", rows)
    return rows


def run_weights() -> list[dict]:
    mp = max_points()
    rows = [{"criterion": c["label"], "id": c["id"], "max_points": mp[c["id"]],
             "share_pct": round(100 * mp[c["id"]] / 999, 1),
             "time_dependent": c["id"] in TIME_CRITERIA,
             "legal_flag": c.get("legal_flag", "")} for c in table()["criteria"]]
    write_csv("weights.csv", rows)
    return rows


# ---------------------------------------------------------------- charts
def _class_lines(ax, x_text, horizontal=True):
    for thr, lab in CLASS_LINES:
        if horizontal:
            ax.axhline(thr, color=MUTED, lw=0.8, ls=(0, (3, 3)), zorder=1)
            ax.text(x_text, thr + 4, lab, color=MUTED, fontsize=7.5, ha="right", va="bottom")
        else:
            ax.axvline(thr, color=MUTED, lw=0.8, ls=(0, (3, 3)), zorder=1)
            ax.text(thr + 3, x_text, lab, color=MUTED, fontsize=7, rotation=90, va="bottom")


def chart_ceiling(rows):
    yrs = [r["years"] for r in rows]
    lo = [r["ceiling_step"] for r in rows]
    hi = [r["ceiling_interp"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.6, 3.2))
    ax.fill_between(yrs, lo, hi, color=BLUE, alpha=0.18, lw=0, zorder=2)
    ax.plot(yrs, lo, color=NAVY, lw=2, zorder=3)
    ax.plot(yrs, hi, color=BLUE, lw=1.2, ls=(0, (1, 1.5)), zorder=3)
    _class_lines(ax, 20)
    ax.text(12.2, 850, "Solid: published values only\n(step-hold, lower bound)", color=NAVY, fontsize=7.5)
    ax.text(0.4, 905, "Dotted: interpolated between\npublished points (illustrative)", color=BLUE, fontsize=7.5)
    ax.set_xlim(0, 20)
    ax.set_ylim(560, 960)
    ax.set_xlabel("Years since first contract in the German credit file (address age assumed equal)")
    ax.set_ylabel("Highest score the published table allows")
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "chart_ceiling.png")
    plt.close(fig)


def chart_archetypes(rows):
    rows = list(reversed(rows))
    names = [r["archetype"] for r in rows]
    vals = [r["score_step"] for r in rows]
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    bars = ax.barh(names, vals, color=NAVY, height=0.55, zorder=3)
    for b, v, r in zip(bars, vals, rows):
        ax.text(v + 6, b.get_y() + b.get_height() / 2, f"{v:.0f}", va="center", fontsize=8, color=INK)
    for thr, lab in CLASS_LINES:
        ax.axvline(thr, color=MUTED, lw=0.8, ls=(0, (3, 3)), zorder=2)
        ax.text(thr, len(rows) - 0.35, lab.replace(" from ", "\n"), color=MUTED, fontsize=6.8, ha="center", va="bottom")
    ax.set_xlim(500, 1040)
    ax.set_xlabel("Calculator score (published values, step-hold)")
    ax.tick_params(axis="y", length=0, labelsize=8, labelcolor=INK)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "chart_archetypes.png")
    plt.close(fig)


def chart_weights(rows):
    rows = sorted(rows, key=lambda r: r["max_points"])
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    colors = [ORANGE if r["time_dependent"] else NAVY for r in rows]
    bars = ax.barh([r["criterion"] for r in rows], [r["max_points"] for r in rows],
                   color=colors, height=0.6, zorder=3)
    for b, r in zip(bars, rows):
        lab = f"{r['max_points']}"
        if r["legal_flag"]:
            lab += "   (s.37a BDSG address-data question)"
        ax.text(b.get_width() + 3, b.get_y() + b.get_height() / 2, lab, va="center", fontsize=7.5, color=INK)
    ax.set_xlim(0, 470)
    ax.set_xlabel("Maximum points (sum of maxima = 999)")
    ax.tick_params(axis="y", length=0, labelsize=7.8, labelcolor=INK)
    ax.text(285, 4.6, "Time-dependent\n(280 points, 28%)", color=ORANGE, fontsize=8, fontweight="bold")
    ax.text(285, 6.6, "Other criteria", color=NAVY, fontsize=8, fontweight="bold")
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "chart_weights.png")
    plt.close(fig)


def chart_sensitivity(rows):
    a3 = [r for r in rows if r["base"] == "A3"]
    a3 = sorted(a3, key=lambda r: r["delta"])
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    vals = [r["delta"] for r in a3]
    bars = ax.barh([r["event"] for r in a3], vals,
                   color=[ORANGE if v < 0 else AQUA for v in vals], height=0.55, zorder=3)
    for b, r in zip(bars, a3):
        v = r["delta"]
        txt = f"{v:+.0f}  ({r['class_before'].split(' (')[0]} → {r['class_after'].split(' (')[0]})"
        ax.text(v - 3 if v < 0 else v + 3, b.get_y() + b.get_height() / 2, txt,
                va="center", ha="right" if v < 0 else "left", fontsize=7.3, color=INK)
    ax.axvline(0, color=MUTED, lw=0.8)
    ax.set_xlim(-380, 40)
    ax.set_xlabel("Score change, under-25 archetype A3 (base 719)")
    ax.tick_params(axis="y", length=0, labelsize=7.8, labelcolor=INK)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(OUT / "chart_sensitivity.png")
    plt.close(fig)


def main():
    arch = run_archetypes()
    ceil = run_ceiling()
    sens = run_sensitivity()
    mono = run_monotonicity()
    w = run_weights()
    chart_ceiling(ceil)
    chart_archetypes(arch)
    chart_weights(w)
    chart_sensitivity(sens)
    summary = {
        "max_total": sum(max_points().values()),
        "time_points": sum(r["max_points"] for r in w if r["time_dependent"]),
        "months_to_class1_step": first_month_reaching(ceil, "ceiling_step", 776),
        "months_to_class1_interp": first_month_reaching(ceil, "ceiling_interp", 776),
        "months_to_class1_upper": first_month_reaching(ceil, "ceiling_upper", 776),
        "ceiling_at_12m_upper": next(r["ceiling_upper"] for r in ceil if r["months_in_file"] == 12),
        "months_to_class2_step": first_month_reaching(ceil, "ceiling_step", 709),
        "ceiling_at_12m_step": next(r["ceiling_step"] for r in ceil if r["months_in_file"] == 12),
        "ceiling_at_12m_interp": next(r["ceiling_interp"] for r in ceil if r["months_in_file"] == 12),
        "ceiling_at_36m_step": next(r["ceiling_step"] for r in ceil if r["months_in_file"] == 36),
        "ceiling_at_36m_interp": next(r["ceiling_interp"] for r in ceil if r["months_in_file"] == 36),
        "all_monotonic": all(r["monotonic"] for r in mono),
    }
    with (OUT / "summary.csv").open("w", newline="") as fh:
        wr = csv.writer(fh)
        for k, v in summary.items():
            wr.writerow([k, v])
    for r in arch:
        print(f"{r['archetype']:45s} step={r['score_step']:6.1f} interp={r['score_interp']:6.1f} {r['class_step']}  no-addr={r['score_without_address_criterion']}")
    print(summary)
    for r in sens:
        print(r["base"], r["event"], r["delta"], r["class_before"], "->", r["class_after"])


if __name__ == "__main__":
    main()
