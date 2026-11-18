import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from assurance.data import CROSSWALK, FINDINGS, REQUESTS  # noqa: E402
from assurance.models import Finding, Rating, Status  # noqa: E402
from assurance.outcome_rules import decide  # noqa: E402


def test_public_evidence_gives_defer():
    out = decide(FINDINGS, CROSSWALK)
    assert out.decision == "Defer pending evidence"
    assert any("Core element H" in r for r in out.reasons)


def test_ratable_crosswalk_with_conditioned_highs_gives_approve_with_conditions():
    cw = [r.model_copy(update={"ratable": True}) for r in CROSSWALK]
    assert decide(FINDINGS, cw).decision == "Approve with conditions"


def _obligations():
    import csv
    with (Path(__file__).resolve().parents[1] / "docs" / "obligation_matrix_step1.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_no_high_with_complete_obligations_gives_approve():
    cw = [r.model_copy(update={"ratable": True}) for r in CROSSWALK]
    fs = [f.model_copy(update={"rating": Rating.medium}) for f in FINDINGS]
    assert decide(fs, cw, obligations=_obligations()).decision == "Approve"


def test_rule_1_needs_every_deployer_obligation_to_have_an_evidence_plan():
    cw = [r.model_copy(update={"ratable": True}) for r in CROSSWALK]
    fs = [f.model_copy(update={"rating": Rating.medium}) for f in FINDINGS]
    obl = _obligations()
    d = next(o for o in obl if "mainkai" in o["owner"].lower())
    d["evidence_needed"] = ""
    out = decide(fs, cw, obligations=obl)
    assert out.decision == "Approve with conditions" and d["id"] in out.reasons[0]
    assert decide(fs, cw).decision == "Approve with conditions"   # obligations not supplied


def test_ratability_test_is_enforced_for_core_elements():
    from assurance.models import CrosswalkRow
    row = next(r for r in CROSSWALK if r.core and r.ratable).model_dump()
    row["visible_result"] = ""
    with pytest.raises(ValueError):
        CrosswalkRow(**row)
    h = next(r for r in CROSSWALK if r.element == "H")
    assert not h.ratable and not h.visible_result


def test_confirmed_critical_gives_reject():
    cw = [r.model_copy(update={"ratable": True}) for r in CROSSWALK]
    fs = [f.model_copy(update={"rating": Rating.critical}) if f.id == "F01" else f for f in FINDINGS]
    assert decide(fs, cw, confirmed_unremediated_critical=("F01",)).decision == "Reject"


def test_every_high_has_owner_and_pre_live_deadline():
    for f in FINDINGS:
        if f.rating == Rating.high:
            assert f.owner and f.deadline.startswith(("Before contract signature", "Before go-live")), f.id


def test_request_count_in_range_and_linked():
    assert 12 <= len(REQUESTS) <= 15
    ids = {f.id for f in FINDINGS}
    for r in REQUESTS:
        assert set(r.findings) <= ids


def test_tone_validator_blocks_banned_words():
    base = FINDINGS[0].model_dump()
    base["observation"] = "The vendor is non-compliant."
    with pytest.raises(ValueError):
        Finding(**base)


def test_not_public_is_never_rated_as_failure_wording():
    for f in FINDINGS:
        assert f.status != Status.adequate or f.rating in (Rating.low, Rating.none)


def test_scenarios_reach_their_expected_outcomes():
    from assurance.scenarios import run
    res = {sc["id"]: sc for sc in run()}
    assert res["S0"]["decision"] == "Defer pending evidence"
    assert res["S1"]["decision"] == "Approve with conditions"
    assert res["S2"]["decision"] == "Reject"
    for sc in res.values():
        assert sc["decision"] == sc["expected"], sc["id"]
    assert res["S1"]["synthetic"] and res["S2"]["synthetic"] and not res["S0"]["synthetic"]
