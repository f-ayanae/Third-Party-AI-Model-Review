"""Apply the SCOPE.md outcome rules mechanically to the ratings.

Rule 4  Reject: any Critical the vendor confirms it will not remediate.
Rule 3  Defer pending evidence: a core element cannot be rated (ratability test in models.py).
Rule 2  Approve with conditions: no Critical; each High has an owner and a pre-go-live deadline.
Rule 1  Approve: no Critical or High open, and every deployer obligation has an owner and an evidence plan.
"""
from __future__ import annotations

from dataclasses import dataclass

from .models import CrosswalkRow, Finding, Rating

LIVE_WORDS = ("Before contract signature", "Before go-live")


@dataclass
class Outcome:
    decision: str
    rule: str
    reasons: list[str]
    path: list[str]


def deployer_gaps(obligations: list[dict] | None) -> list[str]:
    """Deployer (Mainkai) obligations without an owner or an evidence plan. None means the list was not supplied."""
    if obligations is None:
        return ["deployer obligations were not supplied, so rule 1 cannot be confirmed"]
    gaps = []
    for o in obligations:
        owner = (o.get("owner") or "").strip()
        if not owner:
            gaps.append(f"{o.get('id', '?')} has no owner")
        elif "mainkai" in owner.lower() and not (o.get("evidence_needed") or "").strip():
            gaps.append(f"{o.get('id', '?')} has no evidence plan")
    return gaps


def decide(findings: list[Finding], crosswalk: list[CrosswalkRow],
           confirmed_unremediated_critical: tuple[str, ...] = (),
           obligations: list[dict] | None = None) -> Outcome:
    crit = [f for f in findings if f.rating == Rating.critical]
    high = [f for f in findings if f.rating == Rating.high]
    unratable = [r for r in crosswalk if r.core and not r.ratable]

    if any(f.id in confirmed_unremediated_critical for f in crit):
        return Outcome("Reject", "Rule 4", [f"{f.id} Critical, vendor will not remediate" for f in crit], [])
    if unratable:
        reasons = [f"Core element {r.element} ({r.name}) cannot be rated on public evidence" for r in unratable]
        path = ["Receive and test the requests tied to the unratable elements, then re-rate."]
        if not crit and all(f.owner and f.deadline.startswith(LIVE_WORDS) for f in high):
            path.append("If no new Critical arises and every High keeps a pre-go-live condition, "
                        "rule 2 (approve with conditions) becomes available.")
        return Outcome("Defer pending evidence", "Rule 3", reasons, path)
    if crit:
        return Outcome("Defer pending evidence", "Rule 3 (Critical open, remediation unconfirmed)",
                       [f"{f.id} Critical" for f in crit], [])
    if high:
        missing = [f.id for f in high if not (f.owner and f.deadline.startswith(LIVE_WORDS))]
        if missing:
            return Outcome("Defer pending evidence", "Rule 2 not met", [f"{m} lacks owner or pre-go-live deadline" for m in missing], [])
        return Outcome("Approve with conditions", "Rule 2", [f"{f.id} High with condition" for f in high], [])
    gaps = deployer_gaps(obligations)
    if gaps:
        return Outcome("Approve with conditions", "Rule 2 (rule 1 not met)", gaps, [])
    return Outcome("Approve", "Rule 1", ["No Critical or High open; every deployer obligation has an owner and an evidence plan"], [])
