"""Published points-table calculator (the "replica scorer").

It reproduces the bureau's *published* 12-criterion points table and nothing
more. Results describe this calculator, not how the bureau scores real people:
the bureau's production system may apply business rules, rounding, grace
periods, missing-value handling and data mappings that are not public.

Three readings of unpublished intermediate bands are supported:
  step  : hold the last published value until the next published knot
          (a lower bound on the true table, assuming monotonic points)
  upper : the bureau's bands step once a year, so a value stays fixed for a
          year after a published knot and can at most reach the next
          published value after that (an upper bound, assuming monotonic
          points and annual steps)
  interp: linear interpolation between published knots
          (illustrative only; it is neither a lower nor an upper bound)
The true table lies between step and upper.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

TABLE_PATH = Path(__file__).with_name("points_table.yaml")
Reading = Literal["step", "interp", "upper"]


@lru_cache(maxsize=1)
def table() -> dict:
    return yaml.safe_load(TABLE_PATH.read_text(encoding="utf-8"))


def criterion(cid: str) -> dict:
    for c in table()["criteria"]:
        if c["id"] == cid:
            return c
    raise KeyError(cid)


class Payment(str, Enum):
    none = "none"
    resolved_under_1y = "resolved_under_1y"
    resolved_1y_to_2y = "resolved_1y_to_2y"
    resolved_2y_to_3y = "resolved_2y_to_3y"
    open = "open"


class CreditStatus(str, Enum):
    open_or_negative = "open_or_negative"
    no_instalment_loan = "no_instalment_loan"
    completed_positive = "completed_positive"


class Profile(BaseModel):
    """One applicant's bureau-file facts, as the published criteria describe them.

    Ages are in months; None means the person holds no such product.
    """
    payment: Payment = Payment.none
    bank_contract_months: Optional[int] = Field(default=None, ge=0)
    credit_card_months: Optional[int] = Field(default=None, ge=0)
    address_months: int = Field(default=0, ge=0)
    credit_line_months: Optional[int] = Field(default=None, ge=0)
    bank_card_inquiries_12m: int = Field(default=0, ge=0)
    nonbank_inquiries_12m: int = Field(default=0, ge=0)
    instalment_loans_12m: int = Field(default=0, ge=0)
    longest_remaining_term_months: Optional[int] = Field(default=None, ge=0)
    credit_status: CreditStatus = CreditStatus.no_instalment_loan
    real_estate: bool = False
    identity_checked: bool = False

    @field_validator("credit_status")
    @classmethod
    def _completed_needs_no_open_loan(cls, v, info):
        # Published rule: 19 points for a positively completed loan apply only
        # when no instalment loan is open. An open term implies an open loan.
        term = info.data.get("longest_remaining_term_months")
        if v == CreditStatus.completed_positive and term not in (None, 0):
            raise ValueError("completed_positive requires no open instalment loan")
        return v


def _time_points(knots: list[list[float]], months: float, reading: Reading) -> float:
    pts = knots[0][1]
    for i, (thr, val) in enumerate(knots):
        if months >= thr:
            pts = val
            if i + 1 < len(knots):
                nthr, nval = knots[i + 1]
                if reading == "interp" and months < nthr:
                    pts = val + (nval - val) * (months - thr) / (nthr - thr)
                elif reading == "upper":
                    # knots below one year are published month by month; from one year on, values step annually
                    step_at = thr + 12 if thr >= 12 else nthr
                    if step_at <= months < nthr:
                        pts = nval
    return pts


def _term_points(knots: list[list[float]], months: float, reading: Reading) -> float:
    # decreasing knots: thresholds on remaining months
    pts = knots[0][1]
    for i, (thr, val) in enumerate(knots):
        if months >= thr:
            pts = val
            if reading == "interp" and i + 1 < len(knots):
                nthr, nval = knots[i + 1]
                if months < nthr:
                    pts = val + (nval - val) * (months - thr) / (nthr - thr)
    return pts


def _count_points(values: list[int], floor: int, n: int) -> int:
    return values[n] if n < len(values) else floor


def points(p: Profile, reading: Reading = "step",
           exclude: tuple[str, ...] = ()) -> Optional[dict[str, float]]:
    """Per-criterion points, or None when no score is calculated (open disruption)."""
    if p.payment == Payment.open:
        return None
    t = {c["id"]: c for c in table()["criteria"]}
    out: dict[str, float] = {}
    out["c01_payment_disruptions"] = t["c01_payment_disruptions"]["options"][p.payment.value]

    def tm(cid, months):
        c = t[cid]
        if months is None:
            return c["none"]
        return _time_points(c["knots"], months, reading)

    out["c02_oldest_bank_contract"] = tm("c02_oldest_bank_contract", p.bank_contract_months)
    out["c03_oldest_credit_card"] = tm("c03_oldest_credit_card", p.credit_card_months)
    out["c04_current_address"] = _time_points(t["c04_current_address"]["knots"], p.address_months, reading)
    out["c05_recent_credit_line"] = tm("c05_recent_credit_line", p.credit_line_months)
    c6, c7, c8 = t["c06_bank_card_inquiries"], t["c07_nonbank_inquiries"], t["c08_instalment_loans_taken"]
    out["c06_bank_card_inquiries"] = _count_points(c6["values"], c6["floor"], p.bank_card_inquiries_12m)
    out["c07_nonbank_inquiries"] = _count_points(c7["values"], c7["floor"], p.nonbank_inquiries_12m)
    out["c08_instalment_loans_taken"] = _count_points(c8["values"], c8["floor"], p.instalment_loans_12m)
    c9 = t["c09_longest_remaining_term"]
    out["c09_longest_remaining_term"] = (c9["none"] if p.longest_remaining_term_months is None
                                         else _term_points(c9["knots"], p.longest_remaining_term_months, reading))
    out["c10_credit_status"] = t["c10_credit_status"]["options"][p.credit_status.value]
    out["c11_real_estate"] = t["c11_real_estate"]["options"]["yes" if p.real_estate else "no"]
    out["c12_identity_check"] = t["c12_identity_check"]["options"]["yes" if p.identity_checked else "no"]
    for cid in exclude:
        out[cid] = 0
    return out


def score(p: Profile, reading: Reading = "step", exclude: tuple[str, ...] = ()) -> Optional[float]:
    pts = points(p, reading, exclude)
    return None if pts is None else round(sum(pts.values()), 1)


def score_class(s: Optional[float]) -> str:
    if s is None:
        return "No score"
    for thr, label in table()["classes"]:
        if s >= thr:
            return label
    return "Below scale"


def max_points() -> dict[str, int]:
    out = {}
    for c in table()["criteria"]:
        if c["kind"] == "categorical":
            out[c["id"]] = max(c["options"].values())
        elif c["kind"] in ("time",):
            out[c["id"]] = max([k[1] for k in c["knots"]] + ([c["none"]] if c.get("none") is not None else []))
        elif c["kind"] == "term":
            out[c["id"]] = max([k[1] for k in c["knots"]] + [c["none"]])
        else:
            out[c["id"]] = max(c["values"] + [c["floor"]])
    return out


def min_points() -> dict[str, int]:
    out = {}
    for c in table()["criteria"]:
        if c["kind"] == "categorical":
            out[c["id"]] = min(c["options"].values())
        elif c["kind"] in ("time", "term"):
            vals = [k[1] for k in c["knots"]] + ([c["none"]] if c.get("none") is not None else [])
            out[c["id"]] = min(vals)
        else:
            out[c["id"]] = min(c["values"] + [c["floor"]])
    return out


TIME_CRITERIA = ("c02_oldest_bank_contract", "c03_oldest_credit_card",
                 "c04_current_address", "c05_recent_credit_line")
