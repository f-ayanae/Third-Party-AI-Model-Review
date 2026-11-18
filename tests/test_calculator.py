import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lab"))
from calculator import (CreditStatus, Payment, Profile, _time_points, max_points, min_points,  # noqa: E402
                        points, score, score_class, table)

BEST = Profile(bank_contract_months=240, credit_card_months=180, address_months=240,
               credit_line_months=None, credit_status=CreditStatus.completed_positive,
               real_estate=True, identity_checked=True)
WORST = Profile(payment=Payment.resolved_under_1y, bank_contract_months=0, credit_card_months=0,
                address_months=0, credit_line_months=0, bank_card_inquiries_12m=5,
                nonbank_inquiries_12m=5, instalment_loans_12m=5, longest_remaining_term_months=96,
                credit_status=CreditStatus.open_or_negative)


def test_no_base_points_maxima_sum_to_999():
    assert sum(max_points().values()) == 999


def test_minima_sum_to_100():
    assert sum(min_points().values()) == 100


@pytest.mark.parametrize("reading", ["step", "interp"])
def test_best_profile_scores_999(reading):
    assert score(BEST, reading) == 999


@pytest.mark.parametrize("reading", ["step", "interp"])
def test_worst_profile_scores_100(reading):
    assert score(WORST, reading) == 100


def test_open_disruption_gives_no_score():
    assert score(Profile(payment=Payment.open)) is None
    assert score_class(None) == "No score"


@pytest.mark.parametrize("field,none_ok", [("bank_contract_months", True), ("credit_card_months", True),
                                           ("address_months", False), ("credit_line_months", True)])
@pytest.mark.parametrize("reading", ["step", "interp"])
def test_time_criteria_monotonic_in_age(field, none_ok, reading):
    prev = -1
    for m in range(0, 300):
        s = score(Profile(**{field: m}), reading)
        assert s >= prev, (field, m)
        prev = s


@pytest.mark.parametrize("field", ["bank_card_inquiries_12m", "nonbank_inquiries_12m", "instalment_loans_12m"])
def test_counts_monotonic_decreasing(field):
    vals = [score(Profile(**{field: n})) for n in range(0, 8)]
    assert all(b <= a for a, b in zip(vals, vals[1:]))


@pytest.mark.parametrize("reading", ["step", "interp"])
def test_remaining_term_monotonic_decreasing(reading):
    vals = [score(Profile(longest_remaining_term_months=m, credit_status=CreditStatus.open_or_negative), reading)
            for m in range(0, 120)]
    assert all(b <= a for a, b in zip(vals, vals[1:]))


def test_payment_recovery_monotonic():
    seq = [Payment.resolved_under_1y, Payment.resolved_1y_to_2y, Payment.resolved_2y_to_3y, Payment.none]
    vals = [score(Profile(payment=p)) for p in seq]
    assert vals == sorted(vals)


def test_step_is_lower_bound_of_interp():
    for m in range(0, 260, 5):
        p = Profile(bank_contract_months=m, credit_card_months=m, address_months=m, credit_line_months=m)
        assert score(p, "step") <= score(p, "interp")


def test_published_knots_reproduced_exactly():
    # spot checks against the bureau's pages (V02, V03, V04, V05)
    assert points(Profile(bank_contract_months=48))["c02_oldest_bank_contract"] == 23
    assert points(Profile(bank_contract_months=None))["c02_oldest_bank_contract"] == 18
    assert points(Profile(credit_card_months=None))["c03_oldest_credit_card"] == 24
    assert points(Profile(credit_card_months=60))["c03_oldest_credit_card"] == 59
    assert points(Profile(address_months=120))["c04_current_address"] == 63
    assert points(Profile(bank_card_inquiries_12m=2))["c06_bank_card_inquiries"] == 44


def test_completed_status_rejected_with_open_term():
    with pytest.raises(ValueError):
        Profile(longest_remaining_term_months=24, credit_status=CreditStatus.completed_positive)


def test_exclude_address_criterion():
    assert score(BEST, exclude=("c04_current_address",)) == 905


def test_class_boundaries():
    assert score_class(776) == "Class 1 (top)"
    assert score_class(775) == "Class 2"
    assert score_class(642) == "Class 3"
    assert score_class(641) == "Class 4"


def test_table_has_twelve_criteria():
    assert len(table()["criteria"]) == 12


def test_upper_reading_bounds_step_and_matches_published_knots():
    # step is a lower bound and upper an upper bound; both agree at every published knot
    for c in table()["criteria"]:
        if c["kind"] != "time":
            continue
        for m in range(0, 241):
            lo = _time_points(c["knots"], m, "step")
            hi = _time_points(c["knots"], m, "upper")
            assert lo <= hi, (c["id"], m)
        for thr, val in c["knots"]:
            assert _time_points(c["knots"], thr, "upper") == val, (c["id"], thr)
