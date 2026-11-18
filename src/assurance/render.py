"""Render artefacts and the review from data.

python -m assurance.render            # public, anonymised
python -m assurance.render --named    # private named version (never publish)
"""
from __future__ import annotations

import base64
import csv
import re
import sys
from collections import Counter
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .data import CROSSWALK, FINDINGS, OBLIGATION_FILL, REQUESTS
from .models import Rating
from .outcome_rules import decide
from .scenarios import run as run_scenarios
from .facts import facts, fill

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evidence"))
sys.path.insert(0, str(ROOT / "lab"))
from calculator import max_points, table  # noqa: E402
from register_data import SOURCES  # noqa: E402

PUBLIC = dict(vendor="the bureau", vendor_long="a large German credit bureau", score_name="the bureau's 12-criterion score (v1.0)",
              named=False, case_bgh="BGH, judgments of 21 Oct 2026, I ZR 227/25 to 230/25 (claims against a credit bureau)",
              case_cjeu="CJEU C-634/21 (Scoring), 7 Dec 2023", app="a consumer score app")
_NAMED_FILE = ROOT / "private" / "named_config.py"
NAMED = None
if _NAMED_FILE.exists():  # private overlay, gitignored
    _ns: dict = {}
    exec(_NAMED_FILE.read_text(), _ns)
    NAMED = _ns["NAMED"]


def subst(text: str, v: dict) -> str:
    text = fill(text)  # figures come from the lab outputs, never typed in
    text = text.replace("VENDOR's", v["vendor"] + "'s").replace("VENDOR", v["vendor"])
    if not v["named"]:
        text = re.sub(r"(^|[.!?:]\s+|\(\s*)the bureau", lambda m: m.group(1) + "The bureau", text)
        text = re.sub(r"(;\s+)The bureau", r"\1the bureau", text)
    return text


def img64(p: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()


def read_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_obligations(v) -> list[dict]:
    rows = read_csv(ROOT / "docs" / "obligation_matrix_step1.csv")
    for r in rows:
        st, rt, note = OBLIGATION_FILL[r["id"]]
        r["actual_status"], r["rating"], r["notes"] = st, rt, subst(note, v)
        if v["named"]:
            r["owner"] = r["owner"].replace("the bureau", v["vendor"]).replace("Bureau", v["vendor"])
            r["expected_public_status"] = r["expected_public_status"].replace("the bureau's", v["vendor"] + "'s")
    return rows


def write_artefacts(v, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    obl = build_obligations(v)
    with (out / "obligation_matrix.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(obl[0]))
        w.writeheader()
        w.writerows(obl)
    with (out / "findings_register.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "title", "element", "status", "rating", "basis", "observation", "condition",
                    "owner", "deadline", "requests", "sources", "residual_risk", "escalation"])
        for f in FINDINGS:
            w.writerow([f.id, subst(f.title, v), f.element, f.status.value, f.rating.value, f.basis,
                        subst(f.observation, v), subst(f.condition, v), f.owner, f.deadline,
                        ";".join(f.requests), ";".join(f.sources), subst(f.residual_risk, v),
                        subst(f.escalation or "", v)])
    with (out / "scenarios.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "scenario", "synthetic", "evidence_assumed", "decision", "rule"])
        for sc in run_scenarios():
            w.writerow([sc["id"], sc["name"], "SYNTHETIC" if sc["synthetic"] else "no",
                        subst(sc["assumption"], v), sc["decision"], sc["rule"]])
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=False)
    md = env.get_template("evidence_request.md.j2").render(reqs=REQUESTS, v=v, subst=subst)
    (out / "evidence_request.md").write_text(md, encoding="utf-8")
    return dict(obligations=obl)


def context(v) -> dict:
    lab = ROOT / "lab" / "out"
    outcome = decide(FINDINGS, CROSSWALK, obligations=build_obligations(v))
    mp = max_points()
    crit = []
    src_tiers = {s["id"]: s["tier"] for s in SOURCES}
    for c in table()["criteria"]:
        crit.append(dict(label=c["label"], max=mp[c["id"]], sources=", ".join(c["sources"]),
                         tier="primary" if all(src_tiers[s] == "V1" for s in c["sources"]) else "secondary for some bands",
                         unpublished=c.get("unpublished", ""), legal=c.get("legal_flag", "")))
    counts = Counter(f.rating.value for f in FINDINGS)
    tiers = Counter(s["tier"] for s in SOURCES)
    sources = []
    reg = read_csv((ROOT / "private" / "sources_named.csv") if v["named"] else (ROOT / "evidence" / "sources.csv"))
    for r in reg:
        sources.append(dict(r, sha_short=r["excerpt_sha256"][:12], file_sha_short=(r.get("file_sha256") or "")[:12]))
    summary = {r[0]: r[1] for r in csv.reader((lab / "summary.csv").open())}
    bdir = lab / "bondora" / "bondora_proxy"
    bondora = None
    if (bdir / "summary.json").exists():
        import json
        bondora = dict(s=json.loads((bdir / "summary.json").read_text()),
                       ro=read_csv(bdir / "rank_ordering.csv"), seg=read_csv(bdir / "segments.csv"),
                       drift=read_csv(bdir / "grade_drift.csv"), stab=read_csv(bdir / "stability.csv"),
                       img_ro=img64(bdir / "chart_rank_ordering.png"), img_seg=img64(bdir / "chart_segments_oe.png"))
        sens = bdir / "summary_sensitivity.json"
        bondora["sens"] = json.loads(sens.read_text()) if sens.exists() else None
    return dict(
        v=v, s=lambda t: subst(t, v), findings=FINDINGS, crosswalk=CROSSWALK, requests=REQUESTS,
        outcome=outcome, counts=counts, criteria=crit, tiers=tiers, sources=sources,
        archetypes=read_csv(lab / "archetypes.csv"), sensitivity=read_csv(lab / "sensitivity.csv"),
        monotonicity=read_csv(lab / "monotonicity.csv"), summary=summary,
        highs=[f for f in FINDINGS if f.rating == Rating.high], bondora=bondora,
        obligations=build_obligations(v), scenarios=run_scenarios(), F=facts(),
        n_claims=len(read_csv(ROOT / "evidence" / "claims.csv")),
        img=dict(ceiling=img64(lab / "chart_ceiling.png"), archetypes=img64(lab / "chart_archetypes.png"),
                 weights=img64(lab / "chart_weights.png"), sensitivity=img64(lab / "chart_sensitivity.png")),
    )


def render_html(v, out: Path) -> Path:
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=False)
    html = env.get_template("review.html.j2").render(**context(v))
    cw = env.get_template("crosswalk.html.j2").render(**context(v))
    for name, doc in (("review", html), ("crosswalk", cw)):
        if "[[" in doc:
            raise ValueError(f"unfilled figure token in {name}: " + doc[doc.index("[["):doc.index("[[") + 40])
    p = out / ("review_named_PRIVATE.html" if v["named"] else "review.html")
    p.write_text(html, encoding="utf-8")
    if not v["named"]:  # public write-up only; figures come from the same facts as the review
        wu = env.get_template("writeup.md.j2").render(**context(v))
        if "[[" in wu:
            raise ValueError("unfilled figure token in writeup")
        (out / "WRITEUP.md").write_text(wu, encoding="utf-8")
    (out / ("crosswalk_named_PRIVATE.html" if v["named"] else "crosswalk.html")).write_text(cw, encoding="utf-8")
    return p


def main():
    named = "--named" in sys.argv
    if named and NAMED is None:
        sys.exit("named version needs private/named_config.py")
    v = NAMED if named else PUBLIC
    out = (ROOT / "private" / "build") if named else (ROOT / "deliverables")
    write_artefacts(v, out)
    p = render_html(v, out)
    print("rendered", p)


if __name__ == "__main__":
    main()
