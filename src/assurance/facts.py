"""Every figure quoted in the report, findings and claims, computed from the lab outputs.

Text uses [[key]] tokens; fill() replaces them and fails loudly on an unknown token, so a
figure can never drift from the data or be left unfilled.
"""
from __future__ import annotations

import csv
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "lab" / "out"
BON = LAB / "bondora" / "bondora_proxy"
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
TOKEN = re.compile(r"\[\[([a-z0-9_]+)\]\]")


def _csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(x) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _pct(x: float, d: int = 1) -> str:
    return f"{100 * x:.{d}f}%"


def _years(months: int) -> str:
    return f"{months / 12:g}"


def _seg_label(dim: str, seg: str) -> str:
    if dim == "income_band":
        return "incomes under EUR 1,500" if seg.startswith("<") else f"incomes EUR {seg}"
    if dim == "term_band":
        return f"terms {seg.replace(' m', ' months')}"
    return seg


def _first_break(rows: list[dict]) -> tuple[dict, dict] | None:
    rows = [r for r in rows if r["suppressed"] == "False"]
    for a, b in zip(rows, rows[1:]):
        if float(b["observed_dr"]) < float(a["observed_dr"]):
            return a, b
    return None


@lru_cache(maxsize=1)
def facts() -> dict[str, str]:
    f: dict[str, str] = {}
    # Lab A: calculator
    s = {r[0]: r[1] for r in csv.reader((LAB / "summary.csv").open(encoding="utf-8"))}
    f["time_points"] = s["time_points"]
    f["time_points_pct"] = f"{100 * int(s['time_points']) / 999:.0f}%"
    f["ceiling_12m"] = s["ceiling_at_12m_step"]
    f["class1_years_min"] = _years(int(s["months_to_class1_upper"]))
    f["class1_years_max"] = _years(int(s["months_to_class1_step"]))
    f["class1_months_interp"] = s["months_to_class1_interp"]
    arch = {r["archetype"][:2]: r for r in _csv(LAB / "archetypes.csv")}
    f["a3_score"] = f"{float(arch['A3']['score_step']):g}"
    f["a6_score"] = f"{float(arch['A6']['score_step']):g}"
    sens = _csv(LAB / "sensitivity.csv")

    def drop(term: str) -> tuple[int, int]:
        v = sorted(-int(float(r["delta"])) for r in sens if r["event"] == f"Takes {term}-month Ratenkredit")
        return v[0], v[-1]

    for term in ("36", "60", "96"):
        lo, hi = drop(term)
        f[f"loan{term}_drop"] = f"{lo} to {hi}" if lo != hi else str(lo)
    f["a3_loan60_drop"] = str(-int(float(next(r["delta"] for r in sens if r["base"] == "A3" and r["event"] == "Takes 60-month Ratenkredit"))))

    # Lab B: Bondora proxy (only if the run exists)
    if (BON / "summary.json").exists():
        b = json.loads((BON / "summary.json").read_text(encoding="utf-8"))
        f["n_analysed"] = f"{b['n_analysed']:,}"
        f["oot_gini"] = f"{b['out_of_time']['gini']:.2f}"
        f["oot_gini_ci"] = f"{b['out_of_time']['ci'][0]:.2f} to {b['out_of_time']['ci'][1]:.2f}"
        f["ref_gini"] = f"{b['reference']['gini']:.2f}"
        f["ref_window"] = b["reference"]["window"]
        f["oot_window"] = b["out_of_time"]["window"]
        f["dr_oot"] = _pct(b["out_of_time"]["default_rate"])
        f["dr_ref"] = _pct(b["reference"]["default_rate"])
        rs = b.get("reference_sensitivity")
        if rs:
            f["ref_sens_gini"] = f"{rs['gini']:.2f}"
            f["ref_sens_window"] = rs["window"]
            f["ref_sens_psi"] = ", ".join(f"{p['quarter']} {p['psi']:.2f}" for p in rs["psi_2025"])
        cc = b.get("champion_challenger_demo")
        if cc:
            f["cc_new"] = f"{cc['gini_new']:.2f}"
            f["cc_old"] = f"{cc['gini_old']:.2f}"
            f["cc_diff"] = f"{cc['difference']:+.2f}"
            f["cc_ci"] = f"{cc['ci'][0]:+.2f} to {cc['ci'][1]:+.2f}"
            f["cc_loss"] = f"{cc['material_loss']:.2f}"
            f["cc_result"] = "no material loss" if cc["no_material_loss"] else "material loss"
        ro = _csv(BON / "rank_ordering.csv")
        for sample in ("out_of_time", "reference"):
            br = _first_break([r for r in ro if r["sample"] == sample])
            key = "oot_break" if sample == "out_of_time" else "ref_break"
            f[key] = (f"{br[1]['grade']} ({_pct(float(br[1]['observed_dr']))}, {int(float(br[1]['n'])):,} loans) defaults less than "
                      f"{br[0]['grade']} ({_pct(float(br[0]['observed_dr']))})") if br else "default rates rise in every grade"
        gd = [r for r in _csv(BON / "grade_drift.csv") if r["suppressed"] == "False"]
        worse = [r for r in gd if float(r["o_to_e"]) > 1]
        f["grades_worse"] = f"{WORDS.get(len(worse), len(worse))} of {WORDS.get(len(gd), len(gd))}"
        top = max(gd, key=lambda r: float(r["o_to_e"]))
        f["drift_top"] = f"{top['grade']} by {100 * (float(top['o_to_e']) - 1):.0f}%"
        seg = [r for r in _csv(BON / "segments.csv") if r["suppressed"] == "False" and _f(r["o_to_e"]) is not None]
        seg.sort(key=lambda r: float(r["o_to_e"]))
        f["oe_min"] = f"{float(seg[0]['o_to_e']):.2f}"
        f["oe_max"] = f"{float(seg[-1]['o_to_e']):.2f}"
        hi = ", ".join(f"{_seg_label(r['dimension'], r['segment'])} {float(r['o_to_e']):.2f}" for r in reversed(seg[-3:]))
        lo = ", ".join(f"{_seg_label(r['dimension'], r['segment'])} {float(r['o_to_e']):.2f}" for r in seg[:2][::-1])
        f["seg_extremes"] = f"{hi}; {lo}"
        stab = _csv(BON / "stability.csv")
        early = [float(r["gini"]) for r in stab if r["quarter"] < "2024Q2" and _f(r["gini"]) is not None]
        if early:
            f["early_gini_range"] = f"{min(early):.2f} to {max(early):.2f}"
        q25 = [r for r in stab if r["quarter"].startswith("2025")]
        f["psi_2025"] = ", ".join(f"{r['quarter']} {float(r['psi_vs_reference']):.2f}" for r in q25)
        bands = [r["psi_band"] for r in q25]
        f["psi_2025_reading"] = "Red" if "red" in bands else ("Amber" if "amber" in bands else "Green")
        f["psi_2025_bands"] = ", ".join(f"{r['quarter']} {r['psi_band']}" for r in q25)
    return f


def fill(text: str) -> str:
    def rep(m: re.Match) -> str:
        key = m.group(1)
        if key not in facts():
            raise KeyError(f"unknown figure token [[{key}]]")
        return facts()[key]
    return TOKEN.sub(rep, text)
