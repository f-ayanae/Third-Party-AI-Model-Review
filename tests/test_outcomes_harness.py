import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lab" / "bondora"))
from fixture import make_fixture  # noqa: E402
from outcomes import (detect, gini, grade_dr, psi, rank_ordering, run,  # noqa: E402
                      schema_check, segment_oe, standardise, suppress, wilson)


@pytest.fixture(scope="module")
def std():
    return standardise(make_fixture())


def investor_frame(n=4000, seed=3):
    """Tiny synthetic frame in the 2026 investor-export layout (no real data)."""
    rng = np.random.default_rng(seed)
    grades = np.array(["AA", "A", "B", "C", "D", "E", "F", "G"])
    g = rng.choice(grades, n)
    p = {x: 0.02 + 0.03 * i for i, x in enumerate(grades)}
    bad = (rng.uniform(size=n) < np.array([p[x] for x in g])).astype(float)
    bad[:200] = np.nan                                   # not yet measurable
    early = np.where(rng.uniform(size=n) < 0.05, 1.0, np.nan)
    return pd.DataFrame({
        "loan_issued_at": pd.to_datetime("2023-10-01") + pd.to_timedelta(rng.integers(0, 700, n), unit="D"),
        "has_default_within_12_months": bad, "customer_risk_rating": g,
        "country": rng.choice(["Finland", "Estonia"], n), "combined_income": rng.uniform(800, 5000, n),
        "initial_loan_duration": rng.choice([24, 60, 84], n), "initial_interest_rate": rng.uniform(0.1, 0.25, n),
        "is_early_repaid_within_14_days": early, "loan_status": "Repaid"})


def test_schema_check_flags_unknown_columns():
    assert schema_check(pd.DataFrame({"LoanDate": []})) != []


def test_detects_both_formats():
    assert detect(make_fixture(n=500)) == "legacy"
    assert detect(investor_frame()) == "investor_2026"


def test_investor_adapter_applies_exclusions():
    s = standardise(investor_frame())
    assert s.exclusions["12-month outcome not yet measurable"] == 200
    assert s.exclusions["withdrawn within 14 days"] > 0
    assert s.df["bad"].isin([0, 1]).all()
    assert not s.has_pd


def test_investor_rank_ordering_monotonic():
    s = standardise(investor_frame(n=20000))
    ro = rank_ordering(s.df, "all")
    assert bool(ro["monotonic_overall"].iloc[0])


def test_legacy_immature_loans_dropped(std):
    assert len(std.df) < std.n_raw


def test_gini_positive_on_fixture(std):
    assert gini(std.df["bad"], std.df["risk_rank"]) > 0.2


def test_planted_underprediction_in_grade_f_detected(std):
    ro = rank_ordering(std.df, "all").set_index("grade")
    assert ro.loc["F", "observed_dr"] > ro.loc["F", "mean_pd"]
    assert not ro.loc["F", "pd_inside_ci"]


def test_planted_young_segment_effect_detected(std):
    seg = segment_oe(std.df, grade_dr(std.df), "age_band").set_index("segment")
    assert seg.loc["18-24", "o_to_e"] > 1.3
    assert seg.loc["35-49", "o_to_e"] < 1.15


def test_psi_detects_model_version_shift(std):
    d = std.df
    y = d["issue_date"].dt.year
    assert psi(d[y == 2021]["grade"], d[y == 2022]["grade"]) > psi(d[y == 2019]["grade"], d[y == 2020]["grade"])


def test_small_groups_suppressed():
    df = pd.DataFrame({"segment": ["a", "b"], "n": [29, 30], "rate": [0.1, 0.2]})
    out = suppress(df)
    assert np.isnan(out.loc[0, "rate"]) and out.loc[1, "rate"] == 0.2


def test_wilson_contains_point_estimate():
    lo, hi = wilson(10, 100)
    assert lo < 0.1 < hi


def test_run_writes_only_aggregates(tmp_path, monkeypatch):
    import outcomes
    monkeypatch.setattr(outcomes, "OUT", tmp_path)
    run(investor_frame(), "t")
    for f in (tmp_path / "t").glob("*.csv"):
        cols = set(pd.read_csv(f).columns)
        assert not cols & {"loan_issued_at", "combined_income", "issue_date", "LoanId"}
        n = pd.read_csv(f)["n"].dropna()
        assert (n >= 30).all()


def test_champion_challenger_identical_scores_show_no_loss():
    from outcomes import champion_challenger
    rng = np.random.default_rng(1)
    y = (rng.uniform(size=3000) < 0.1).astype(int)
    s = y * 0.5 + rng.uniform(size=3000)
    r = champion_challenger(y, s, s)
    assert r["difference"] == 0 and r["ci"] == [0.0, 0.0] and r["no_material_loss"]


def test_champion_challenger_flags_a_clearly_weaker_challenger():
    from outcomes import champion_challenger
    rng = np.random.default_rng(2)
    y = (rng.uniform(size=5000) < 0.1).astype(int)
    strong = y * 1.0 + rng.uniform(size=5000)
    weak = y * 0.1 + rng.uniform(size=5000)
    r = champion_challenger(y, weak, strong)
    assert r["difference"] < -0.1 and r["ci"][1] < 0 and not r["no_material_loss"]
