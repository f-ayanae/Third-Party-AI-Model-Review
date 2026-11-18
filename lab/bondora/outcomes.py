"""Lab B: outcomes-analysis harness, run on Bondora's public loan data.

PROXY EVIDENCE ONLY. Bondora is an Estonian consumer lender; its rating model,
population, products and default definition differ from the bureau's score and
from Mainkai's applicants. The harness shows the tests Mainkai should require
on its own retro-scored applicants (request E02).

Two input formats are supported through adapters:
  * investor_2026: the 2026 "Loan Dataset" export (customer_risk_rating,
    has_default_within_12_months, country, combined_income, ...). No PD,
    no model version, no age.
  * legacy: the older public legend (Rating, ProbabilityOfDefault,
    ModelVersion, Age, DefaultDate, ...). Used by the synthetic fixture.

Publication rule: raw rows are never written. Every published aggregate
covers at least MIN_GROUP loans; smaller groups are suppressed.

Usage:
    python lab/bondora/outcomes.py --file data/bondora/loan_dataset_investor.parquet
    python lab/bondora/outcomes.py --file LoanData.csv
    python lab/bondora/outcomes.py --fixture
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

MIN_GROUP = 30
HORIZON_MONTHS = 12
OUT = Path(__file__).resolve().parents[1] / "out" / "bondora"
GRADES = ["AA", "A", "B", "C", "D", "E", "F", "G", "HR"]
# Mainkai's discrimination tolerance is relative (champion-challenger): on the same applicants, the new score may not
# lose more than this many Gini points against the current score, judged on the lower 95% bound of the paired difference.
MATERIAL_GINI_LOSS = 0.03

LEGACY = dict(loan_date="LoanDate", default_date="DefaultDate", pd="ProbabilityOfDefault",
              rating="Rating", model_version="ModelVersion", age="Age", country="Country")
INVESTOR = dict(issued="loan_issued_at", target="has_default_within_12_months",
                rating="customer_risk_rating", country="country", income="combined_income",
                term="initial_loan_duration", rate="initial_interest_rate",
                early14="is_early_repaid_within_14_days", status="loan_status")


# ------------------------------------------------------------------ adapters
@dataclass
class Standard:
    """Common frame: issue_date, bad (0/1), grade, risk_rank (higher = riskier),
    optional pd and price, plus segment columns."""
    df: pd.DataFrame
    fmt: str
    n_raw: int
    exclusions: dict
    segments: list[str]
    has_pd: bool
    notes: list[str] = field(default_factory=list)


def detect(df: pd.DataFrame) -> str:
    if set(INVESTOR.values()) - {INVESTOR["early14"]} <= set(df.columns):
        return "investor_2026"
    if {LEGACY[k] for k in ("loan_date", "default_date", "pd", "rating")} <= set(df.columns):
        return "legacy"
    raise ValueError("unrecognised Bondora format; check the dataset dictionary")


def schema_check(df: pd.DataFrame) -> list[str]:
    try:
        detect(df)
        return []
    except ValueError:
        return ["no supported column set found"]


def _grade_rank(g: pd.Series) -> pd.Series:
    return g.map({x: i for i, x in enumerate(GRADES)})


def income_band(x: pd.Series) -> pd.Series:
    b = pd.cut(x, [-0.01, 1500, 2500, 3500, np.inf], labels=["< 1,500", "1,500-2,500", "2,500-3,500", "3,500+"])
    return b.astype("string").fillna("not recorded")


def from_investor(df: pd.DataFrame) -> Standard:
    c = INVESTOR
    n_raw = len(df)
    ex = {}
    d = df.copy()
    mask = d[c["rating"]].notna()
    ex["no rating (issued before current model)"] = int((~mask).sum())
    d = d[mask]
    mask = d[c["target"]].notna()
    ex["12-month outcome not yet measurable"] = int((~mask).sum())
    d = d[mask]
    if c["early14"] in d:
        mask = d[c["early14"]].fillna(0) != 1
        ex["withdrawn within 14 days"] = int((~mask).sum())
        d = d[mask]
    out = pd.DataFrame({
        "issue_date": pd.to_datetime(d[c["issued"]]),
        "bad": d[c["target"]].astype(int),
        "grade": d[c["rating"]].astype("string"),
        "price": pd.to_numeric(d[c["rate"]], errors="coerce"),
        "country": d[c["country"]].astype("string"),
        "income_band": income_band(pd.to_numeric(d[c["income"]], errors="coerce")),
        "term_band": pd.cut(d[c["term"]], [0, 36, 60, 999], labels=["up to 36 m", "37-60 m", "over 60 m"]).astype("string"),
    })
    out["risk_rank"] = _grade_rank(out["grade"])
    out = out[out["risk_rank"].notna()]
    return Standard(out, "investor_2026", n_raw, ex, ["country", "income_band", "term_band"], False,
                    ["No PD in this export: calibration of predicted PDs cannot be tested; observed/expected by segment is used instead.",
                     "No age field: age-band segments cannot be tested.",
                     "Issued loans only: approval-rate ratios and reject inference cannot be tested."])


def from_legacy(df: pd.DataFrame, snapshot: pd.Timestamp | None = None) -> Standard:
    c = LEGACY
    loan_date = pd.to_datetime(df[c["loan_date"]], errors="coerce")
    default_date = pd.to_datetime(df[c["default_date"]], errors="coerce")
    snapshot = snapshot or loan_date.max()
    cutoff = snapshot - pd.DateOffset(months=HORIZON_MONTHS)
    keep = (loan_date <= cutoff) & pd.to_numeric(df[c["pd"]], errors="coerce").between(0, 1) & df[c["rating"]].notna()
    ex = {"12-month outcome not yet measurable or missing PD/rating": int((~keep).sum())}
    d = df[keep]
    ld, dd = loan_date[keep], default_date[keep]
    out = pd.DataFrame({
        "issue_date": ld,
        "bad": (dd.notna() & (dd <= ld + pd.DateOffset(months=HORIZON_MONTHS))).astype(int),
        "grade": d[c["rating"]].astype("string"),
        "pd": pd.to_numeric(d[c["pd"]], errors="coerce"),
        "country": d[c["country"]].astype("string"),
        "age_band": pd.cut(pd.to_numeric(d[c["age"]], errors="coerce"), [17, 24, 34, 49, 120],
                           labels=["18-24", "25-34", "35-49", "50+"]).astype("string"),
        "model_version": pd.to_numeric(d[c["model_version"]], errors="coerce"),
    })
    out["risk_rank"] = _grade_rank(out["grade"])
    return Standard(out, "legacy", len(df), ex, ["age_band", "country"], True)


def standardise(df: pd.DataFrame) -> Standard:
    return from_investor(df) if detect(df) == "investor_2026" else from_legacy(df)


# ------------------------------------------------------------------ statistics
def gini(y, s) -> float:
    return 2 * roc_auc_score(y, s) - 1


def gini_ci(y, s, n_boot=200, seed=7) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    y, s = np.asarray(y), np.asarray(s)
    g = gini(y, s)
    boots = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            boots.append(gini(y[i], s[i]))
    return g, float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def gini_diff_ci(y, s_new, s_old, n_boot=200, seed=7) -> tuple[float, float, float]:
    """Paired bootstrap of Gini(new) - Gini(old) on the same observations (champion-challenger)."""
    rng = np.random.default_rng(seed)
    y, a, b = np.asarray(y), np.asarray(s_new), np.asarray(s_old)
    diff = gini(y, a) - gini(y, b)
    boots = []
    for _ in range(n_boot):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() != y[i].max():
            boots.append(gini(y[i], a[i]) - gini(y[i], b[i]))
    return diff, float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def champion_challenger(y, s_new, s_old, material_loss: float = MATERIAL_GINI_LOSS) -> dict:
    d, lo, hi = gini_diff_ci(y, s_new, s_old)
    return dict(gini_new=gini(y, s_new), gini_old=gini(y, s_old), difference=d, ci=[lo, hi],
                material_loss=material_loss, no_material_loss=bool(lo > -material_loss))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - h, c + h


def psi(expected: pd.Series, actual: pd.Series, eps: float = 1e-4) -> float:
    cats = sorted(set(expected.dropna()) | set(actual.dropna()))
    e = expected.value_counts(normalize=True).reindex(cats, fill_value=0) + eps
    a = actual.value_counts(normalize=True).reindex(cats, fill_value=0) + eps
    return float(((a - e) * np.log(a / e)).sum())


def psi_band(v: float) -> str:
    return "green" if v < 0.10 else ("amber" if v <= 0.25 else "red")


def suppress(df: pd.DataFrame, n_col: str = "n") -> pd.DataFrame:
    df = df.copy()
    small = df[n_col] < MIN_GROUP
    for c in df.columns:
        if c != n_col and df[c].dtype.kind in "fi":
            df.loc[small, c] = np.nan
    df.loc[small, n_col] = np.nan
    df["suppressed"] = small
    return df


def _safe_gini(g: pd.DataFrame, col: str) -> float:
    k = g["bad"].sum()
    return gini(g["bad"], g[col]) if 0 < k < len(g) else np.nan


# ------------------------------------------------------------------ tests
def rank_ordering(d: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for gr in GRADES:
        g = d[d.grade == gr]
        n, k = len(g), int(g["bad"].sum())
        if n == 0:
            continue
        lo, hi = wilson(k, n)
        row = dict(sample=label, grade=gr, n=n, observed_dr=k / n, ci_low=lo, ci_high=hi)
        if "pd" in g:
            row["mean_pd"] = float(g["pd"].mean())
            row["pd_inside_ci"] = bool(lo <= row["mean_pd"] <= hi)
        if "price" in g:
            row["mean_rate"] = float(g["price"].mean())
        rows.append(row)
    out = suppress(pd.DataFrame(rows))
    drs = out.loc[~out["suppressed"], "observed_dr"].tolist()
    out["monotonic_overall"] = all(b >= a for a, b in zip(drs, drs[1:]))
    return out


def grade_dr(d: pd.DataFrame) -> pd.Series:
    return d.groupby("grade")["bad"].mean()


def segment_oe(d: pd.DataFrame, ref_dr: pd.Series, seg: str) -> pd.DataFrame:
    """Observed vs expected defaults, expected = reference grade default rates
    applied to the segment's own grade mix (indirect standardisation)."""
    rows = []
    for s, g in d.groupby(seg):
        n, obs = len(g), int(g["bad"].sum())
        exp = float(g["grade"].map(ref_dr).fillna(g["bad"].mean()).sum())
        se = np.sqrt(max(obs, 1)) / exp if exp else np.nan
        rows.append(dict(dimension=seg, segment=s, n=n, observed_dr=obs / n, expected_dr=exp / n,
                         o_to_e=obs / exp if exp else np.nan,
                         o_to_e_low=(obs / exp) - 1.96 * se if exp else np.nan,
                         o_to_e_high=(obs / exp) + 1.96 * se if exp else np.nan,
                         gini=_safe_gini(g, "risk_rank")))
    return suppress(pd.DataFrame(rows))


def stability(d: pd.DataFrame, ref_mask: pd.Series) -> pd.DataFrame:
    ref = d.loc[ref_mask, "grade"]
    rows = []
    for q, g in d.groupby(d["issue_date"].dt.to_period("Q")):
        v = psi(ref, g["grade"])
        rows.append(dict(quarter=str(q), n=len(g), psi_vs_reference=v, psi_band=psi_band(v),
                         observed_dr=g["bad"].mean(), gini=_safe_gini(g, "risk_rank")))
    return suppress(pd.DataFrame(rows))


# ------------------------------------------------------------------ run
def split(std: Standard) -> tuple[pd.Series, pd.Series, str, str]:
    d = std.df
    if std.fmt == "investor_2026":
        # 2023 Q3 to 2024 Q1 is a different regime (quarterly Gini 0.18 to 0.30 against 0.31+ from 2024 Q2), so the
        # stable reference starts in 2024 Q2; the earlier window is kept as a sensitivity (REF_SENSITIVITY).
        ref = (d["issue_date"] >= "2024-04-01") & (d["issue_date"] < "2025-01-01")
        oot = (d["issue_date"] >= "2025-01-01") & (d["issue_date"] < "2025-10-01")
        return ref, oot, "2024 Q2 to Q4", "2025 Q1 to Q3"
    last = d["issue_date"].dt.year.max()
    return d["issue_date"].dt.year < last, d["issue_date"].dt.year == last, f"before {last}", str(last)


def run(df: pd.DataFrame, label: str, source_sha: str = "") -> dict:
    std = standardise(df)
    d = std.df
    out = OUT / label
    out.mkdir(parents=True, exist_ok=True)
    ref, oot, ref_lab, oot_lab = split(std)
    g_all = gini_ci(d["bad"], d["risk_rank"])
    g_ref = gini_ci(d.loc[ref, "bad"], d.loc[ref, "risk_rank"])
    g_oot = gini_ci(d.loc[oot, "bad"], d.loc[oot, "risk_rank"])
    summary = dict(
        label=label, format=std.fmt, source_sha256=source_sha, n_raw=std.n_raw, exclusions=std.exclusions,
        n_analysed=len(d), issue_window=[str(d.issue_date.min().date()), str(d.issue_date.max().date())],
        horizon_months=HORIZON_MONTHS, default_rate=float(d["bad"].mean()),
        reference=dict(window=ref_lab, n=int(ref.sum()), gini=g_ref[0], ci=list(g_ref[1:]),
                       default_rate=float(d.loc[ref, "bad"].mean())),
        out_of_time=dict(window=oot_lab, n=int(oot.sum()), gini=g_oot[0], ci=list(g_oot[1:]),
                         default_rate=float(d.loc[oot, "bad"].mean())),
        pooled=dict(gini=g_all[0], ci=list(g_all[1:])),
        absolute_gini_note=("Reported for information only: an absolute Gini depends on the population scored and is not "
                            "comparable across lenders or with a bureau's whole-population figure."),
        approval_rate_ratio="not computable: dataset holds issued loans only",
        not_testable=std.notes,
    )
    if std.fmt == "investor_2026":
        early = (d["issue_date"] >= "2023-07-01") & (d["issue_date"] < "2025-01-01")
        g_e = gini_ci(d.loc[early, "bad"], d.loc[early, "risk_rank"])
        summary["reference_sensitivity"] = dict(window="2023 Q3 to 2024 Q4", n=int(early.sum()), gini=g_e[0], ci=list(g_e[1:]),
                                                psi_2025=[dict(quarter=str(q), psi=psi(d.loc[early, "grade"], g["grade"]))
                                                          for q, g in d[oot].groupby(d[oot]["issue_date"].dt.to_period("Q"))])
    if "price" in d:
        # Method demonstration only: the export holds one score, so the interest rate stands in for a "current score".
        o = d[oot].dropna(subset=["price"])
        summary["champion_challenger_demo"] = dict(
            challenger="customer risk rating", champion="interest rate (stand-in; partly set from the rating)",
            sample="out-of-time", n=len(o), **champion_challenger(o["bad"], o["risk_rank"], o["price"]))
    if "price" in d:
        summary["price_gini_oot"] = _safe_gini(d[oot].dropna(subset=["price"]), "price")
    if std.has_pd:
        summary["pd_gini_oot"] = _safe_gini(d[oot], "pd")
    ref_dr = grade_dr(d[ref])
    tables = {
        "rank_ordering": pd.concat([rank_ordering(d[ref], "reference"), rank_ordering(d[oot], "out_of_time")]),
        # expected = same-period grade rates, so segment effects are not mixed with time drift
        "segments": pd.concat([segment_oe(d[oot], grade_dr(d[oot]), s) for s in std.segments], ignore_index=True),
        # all quarters up to the end of the out-of-time window, against the stable reference, so the early regime stays visible
        "stability": stability(d[stab := ((d["issue_date"] < "2025-10-01") if std.fmt == "investor_2026" else (ref | oot))],
                               ref[stab]),
    }
    # grade-level drift: OOT observed vs reference grade rates
    oe = d[oot].groupby("grade").agg(n=("bad", "size"), observed_dr=("bad", "mean")).reindex(GRADES).dropna(subset=["n"])
    oe["reference_dr"] = ref_dr.reindex(oe.index)
    oe["o_to_e"] = oe["observed_dr"] / oe["reference_dr"]
    tables["grade_drift"] = suppress(oe.reset_index())
    if std.fmt == "investor_2026":  # sensitivity: keep 14-day withdrawals
        summary["sensitivity_including_withdrawals"] = "see summary_sensitivity.json"
    for name, t in tables.items():
        t.to_csv(out / f"{name}.csv", index=False)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float))
    return dict(summary=summary, **tables)


def sensitivity_with_withdrawals(df: pd.DataFrame, label: str) -> dict:
    d2 = df.drop(columns=[INVESTOR["early14"]], errors="ignore")
    std = from_investor(d2)
    ref, oot, *_ = split(std)
    g = gini_ci(std.df.loc[oot, "bad"], std.df.loc[oot, "risk_rank"])
    res = dict(n_oot=int(oot.sum()), gini_oot=g[0], ci=list(g[1:]), default_rate_oot=float(std.df.loc[oot, "bad"].mean()))
    (OUT / label / "summary_sensitivity.json").write_text(json.dumps(res, indent=2, default=float))
    return res


def load(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix == ".parquet":
        return pd.read_parquet(p)
    if p.suffix in (".xlsx", ".xls"):
        return pd.read_excel(p, sheet_name=0, engine="calamine")
    return pd.read_csv(p, low_memory=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", "--csv", dest="file")
    ap.add_argument("--fixture", action="store_true")
    a = ap.parse_args()
    if a.fixture:
        from fixture import make_fixture
        res = run(make_fixture(), "SYNTHETIC_FIXTURE_NOT_BONDORA")
    else:
        df = load(a.file)
        sha = hashlib.sha256(Path(a.file).read_bytes()).hexdigest()
        res = run(df, "bondora_proxy", sha)
        if detect(df) == "investor_2026":
            res["summary"]["sensitivity"] = sensitivity_with_withdrawals(df, "bondora_proxy")
    print(json.dumps(res["summary"], indent=2, default=float))


if __name__ == "__main__":
    main()
