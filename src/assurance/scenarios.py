"""What-if scenarios for the outcome rules.

SYNTHETIC: the evidence in scenarios S1 and S2 is invented to show that the
rules can produce outcomes other than "defer". None of it is a statement about
the bureau. S0 is the review as it stands on public evidence.
"""
from __future__ import annotations

from .data import CROSSWALK, FINDINGS
from .models import Rating
from .outcome_rules import decide


def _s0():
    return FINDINGS, CROSSWALK, ()


def _s1():
    # Retro-score received and tested: outcomes analysis (H) becomes ratable and F02 closes.
    cw = [r.model_copy(update={"ratable": True, "visible_result": "Retro-score results on Mainkai applicants (synthetic)"})
          if r.element == "H" else r for r in CROSSWALK]
    fs = [f.model_copy(update={"rating": Rating.none}) if f.id == "F02" else f for f in FINDINGS]
    return fs, cw, ()


def _s2():
    # F01 escalation trigger met, and the bureau confirms it will not change criterion 4.
    fs = [f.model_copy(update={"rating": Rating.critical}) if f.id == "F01" else f for f in FINDINGS]
    return fs, CROSSWALK, ("F01",)


SCENARIOS = [
    dict(id="S0", name="Public evidence only (this review)", synthetic=False, build=_s0,
         assumption="The evidence as reviewed. Outcomes analysis (element H) cannot be rated on public evidence.",
         expected="Defer pending evidence"),
    dict(id="S1", name="Bureau supplies a retro-score", synthetic=True, build=_s1,
         assumption=("VENDOR retro-scores 24 to 36 months of Mainkai Ratenkredit applications with the new and the current score. On the "
                     "same applicants the new score's Gini is 0.02 above the current score's (95% interval of the difference -0.01 to +0.05, "
                     "so no material loss), and calibration by pricing band is inside tolerance. A result is now visible, so element H "
                     "becomes ratable and F02 closes; every other finding is unchanged."),
         expected="Approve with conditions"),
    dict(id="S2", name="Criterion 4 kept; counsel says address data", synthetic=True, build=_s2,
         assumption=("VENDOR confirms in writing that it will not change criterion 4 (age of current address), and Mainkai's counsel "
                     "concludes that the criterion is address data under s.37a(2) No.1(d) BDSG. F01 escalates to Critical with no "
                     "remediation."),
         expected="Reject"),
]


def run() -> list[dict]:
    out = []
    for sc in SCENARIOS:
        fs, cw, confirmed = sc["build"]()
        o = decide(fs, cw, confirmed_unremediated_critical=confirmed)
        out.append(dict(id=sc["id"], name=sc["name"], synthetic=sc["synthetic"], assumption=sc["assumption"],
                        decision=o.decision, rule=o.rule, expected=sc["expected"]))
    return out
