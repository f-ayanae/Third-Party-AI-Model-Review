"""Review content as data: crosswalk A to N, findings, evidence requests.

Wording rules: "not publicly available" or "available but inadequate", never a
compliance verdict. Each finding is labelled fact or assessment. The bureau is
anonymised; VENDOR is substituted at render time.
Assumed for the case: contract signature target 31 Jan 2027, go-live 1 Apr 2027.
"""
from .models import CrosswalkRow, Finding, Rating, Request, Status

SIGN = "Before contract signature (target 31 Jan 2027)"
LIVE = "Before go-live (1 Apr 2027)"
SIX = "Within 6 months of go-live"

CROSSWALK = [
    CrosswalkRow(element="A", name="Purpose and intended use", core=False,
        anchors="SR 26-2 model use; SS1/23 P3; EBA GL 4.3.4; MaRisk BTO 1.2 Tz. 1; AI Act Art 13(3)(b)",
        expected="Stated purpose, target population, products and decisions the score is fit for; uses it is not designed for.",
        public_evidence="Cross-industry score predicting payment disruptions; replaces six sector scores (V12, V14). No statement of fitness for unsecured instalment lending or for cut-off setting.",
        lab="Not applicable.", status=Status.inadequate, ratable=True, findings=["F06"]),
    CrosswalkRow(element="B", name="Inventory and risk tiering", core=False,
        anchors="SR 26-2 inventory; SS1/23 P1; MaRisk AT 4.3.4 Tz. 1",
        expected="Mainkai inventory entry, tier (high: drives decline and price for about 120,000 decisions a year), owner, validator.",
        public_evidence="Mainkai-side.", lab="Not applicable.", status=Status.mainkai, ratable=True, findings=[]),
    CrosswalkRow(element="C", name="Data: sources, quality, representativeness", core=True,
        anchors="SR 26-2 data; SS1/23 P3; EBA GL 4.3.4; MaRisk AT 4.3.4 Tz. 3; AI Act Art 10; s.37a(2) BDSG",
        expected="Data lineage per criterion, reporting coverage, quality KPIs, correction process, representativeness by age and residence.",
        public_evidence="Twelve criteria and their meaning are published (V01 to V10). Lineage, coverage, quality KPIs and dispute data are not public. Consumer federation reports a paid document was required to correct address-age data (L14).",
        lab="Time-dependent criteria carry [[time_points]] of 999 points ([[time_points_pct]]); they mechanically favour long histories.",
        status=Status.inadequate, ratable=True, findings=["F01", "F11"],
        visible_result="The twelve criteria and what they measure, and the stored data categories and deletion periods (V01 to V10, V23)."),
    CrosswalkRow(element="D", name="Methodology and conceptual soundness", core=True,
        anchors="SR 26-2 development; SS1/23 P3; EBA GL 4.3.4; MaRisk AT 4.3.4 Tz. 2; s.37a(2) No.3 BDSG (scientific method)",
        expected="Target and default definition, horizon, development sample, exclusions, variable selection, scaling from log-odds to points.",
        public_evidence="Logistic regression; points reflect group default rates (V12, V13). Target, horizon, sample, exclusions and scaling are not public.",
        lab="Points are monotonic in every ordinal criterion under both readings; entry dips (a new product scores below holding none) are deliberate design features.",
        status=Status.inadequate, ratable=True, findings=["F06"],
        visible_result="The model's output in full: the published points table for all twelve criteria (V12, V13, V22)."),
    CrosswalkRow(element="E", name="Assumptions, limitations, business rules", core=False,
        anchors="SR 26-2 limitations; SS1/23 P3; AI Act Art 13(3)(b)(iii)",
        expected="Known limitations, no-score rules, grace periods, overrides, populations where the score is weak.",
        public_evidence="No score with open disruptions; 28-day and 30-day rules; a consumer score app notes that less active persons may score worse (V18). No limitations statement for lenders.",
        lab="Debt-collection inquiry effect and several bands are unpublished, so the calculator cannot reproduce every case.",
        status=Status.inadequate, ratable=True, findings=["F04", "F03"]),
    CrosswalkRow(element="F", name="Implementation and calculation accuracy", core=False,
        anchors="SR 26-2 implementation; SS1/23 P3",
        expected="Evidence that delivered scores match the documented table; version control of the table.",
        public_evidence="Published maxima sum to 999 with a floor of 100 (C01). Intermediate bands for three criteria unpublished.",
        lab="Calculator reproduces every published knot; unit tests pass (max 999, min 100, monotonicity, no base, step and upper bounds).",
        status=Status.inadequate, ratable=True, findings=["F04"]),
    CrosswalkRow(element="G", name="Developmental testing: discrimination, calibration, stability", core=True,
        anchors="SR 26-2 testing; SS1/23 P3; EBA GL 4.3.4; MaRisk AT 4.3.4 Tz. 5; AI Act Art 15",
        expected="Paired Gini against the current score on the same retro-scored applicants, with confidence interval; calibration per pricing band; stability; sensitivity.",
        public_evidence="Company-reported Gini of 0.6 with no sample, period, product or interval (V12).",
        lab="Sensitivity: one 60-month loan moves the under-25 archetype from [[a3_score]] to [[a6_score]] (Class 2 to Class 4).",
        status=Status.inadequate, ratable=True, findings=["F02", "F13"],
        visible_result="A reported Gini of 0.6 for the score (V12), without sample or interval."),
    CrosswalkRow(element="H", name="Outcomes analysis and back-testing", core=True,
        anchors="SR 26-2 outcomes analysis; SS1/23 P4; EBA GL 4.3.4; MaRisk BTO 1.2 Tz. 5; AI Act Art 26(5)",
        expected="Retro-scored Mainkai applicants: approval and default by score band, by segment, against Mainkai's own default definition.",
        public_evidence="None. Retrospective scoring of a bank's historical rating dates is needed to test a new version on its portfolio (V20).",
        lab="Proxy run on [[n_analysed]] Bondora loans: rank ordering breaks at the tail, segment observed/expected from [[oe_min]] to [[oe_max]], paired champion-challenger test demonstrated. Shows the tests, not the bureau's performance.",
        status=Status.not_public, ratable=False, findings=["F02", "F03"]),
    CrosswalkRow(element="I", name="Ongoing monitoring and thresholds", core=False,
        anchors="SR 26-2 monitoring; SS1/23 P3; MaRisk AT 4.3.4 Tz. 5; AI Act Arts 26(5), 72",
        expected="PSI and approval-rate thresholds, owners, frequency; vendor population reports; incident notices.",
        public_evidence="Scores refreshed quarterly per press reports; no lender monitoring pack is public.",
        lab="PSI green below 0.10, amber 0.10 to 0.25, red above 0.25 implemented in the harness.",
        status=Status.not_public, ratable=True, findings=["F12"]),
    CrosswalkRow(element="J", name="Independent validation and effective challenge", core=True,
        anchors="SR 26-2 validation; SS1/23 P4; EBA GL 4.3.4; MaRisk AT 4.3.4 Tz. 5",
        expected="Independent review report: scope, version, findings, limitations; Mainkai's own challenge.",
        public_evidence="Bureau reports a Fraunhofer IAIS review of scientific quality and data, a data protection authority finding of applicability, and review by two university departments (V12, V13). Reports not public.",
        lab="Not applicable.", status=Status.inadequate, ratable=True, findings=["F05"],
        visible_result="The external review's stated conclusion: scientific quality and data relevance confirmed (V12, V13)."),
    CrosswalkRow(element="K", name="Vendor and change management", core=False,
        anchors="SR 26-2 third-party models; SS1/23 P2; DORA Arts 28, 30; MaRisk AT 9 Tz. 1; AI Act Art 111",
        expected="Version policy, material-change definition, notice period, parallel runs, documentation access, exit.",
        public_evidence="Sector models expire 31 Dec 2028; older scores adjusted for s.37a (V17). No public change-notification policy.",
        lab="Not applicable.", status=Status.not_public, ratable=True, findings=["F07", "F08"]),
    CrosswalkRow(element="L", name="Governance, documentation, use and explanation", core=False,
        anchors="SR 26-2 governance; SS1/23 P2; EBA GL 4.3.4; MaRisk AT 4.3.4 Tz. 4, 6, BTO 1.1 Tz. 6; GDPR Arts 15, 22; ss.30(6)-(7), 37a(4)-(5) BDSG; Art 86 AI Act",
        expected="Per-decision explanation from criterion points; reason texts; contest and human-review route.",
        public_evidence="Points per criterion published and visible to consumers; bureau states it will give s.37a explanations for all relevant scores (press, Oct 2026).",
        lab="Calculator shows which criteria drive each archetype's score.",
        status=Status.inadequate, ratable=True, findings=["F10"]),
    CrosswalkRow(element="M", name="AI Act bridge (note)", core=False,
        anchors="AI Act Arts 3(1), 6(3), 111, Annex III 5(b); Reg 2026/1744",
        expected="Reasoned position on AI-system status and legacy treatment; provider support commitments.",
        public_evidence="Bureau describes the method as learning from data (V12); Commission guidelines carve out regression used to improve optimisation (L09).",
        lab="Not applicable.", status=Status.not_due, ratable=True, findings=["F09"]),
    CrosswalkRow(element="N", name="Agentic boundary (note)", core=False,
        anchors="SR 26-2 scope; OWASP Agentic Top 10",
        expected="Confirmation no agentic or generative component sits in the decision path.",
        public_evidence="Fixed additive points table; no agentic component described.",
        lab="Not applicable.", status=Status.not_applicable, ratable=True, findings=[]),
]

FINDINGS = [
    Finding(id="F01", title="Address-age criterion and the s.37a BDSG address-data exclusion",
        element="C; G2", status=Status.not_public, rating=Rating.high, basis="fact and assessment",
        observation=("From 20 Nov 2026, s.37a(2) No.1(d) BDSG allows a probability value to be created or used only if address data are not used; "
                     "the committee report calls their use impermissible without exception (L01, L02). The old s.31(1) No.3 restricted only the "
                     "exclusive use of address data; s.37a bans their use outright. Criterion 4, age of current address, carries up to 94 points. "
                     "Two readings are open: a broad one, under which residence time is derived from address history and so falls under the ban, "
                     "and a narrow one, under which the ban targets geographic location (geoscoring) and residence time is a stability measure. "
                     "Commentators say no court has decided between them, and VENDOR has not publicly explained its treatment; its 11 Nov 2026 "
                     "announcement, as reported, deals with older scores and does not mention this criterion (L03, L21, V17)."),
        why_it_matters=("Section 37a conditions use as well as creation, so Mainkai is directly exposed. If the criterion is changed or removed, "
                        "every score shifts and cut-offs set on today's table are stale."),
        condition=("VENDOR to give a written legal position on criterion 4 and confirm the exact model version Mainkai will receive after "
                   "20 Nov 2026. If the criterion changes, VENDOR supplies the revised table and a score-migration analysis before cut-offs are set."),
        owner="Head of Legal with Head of Credit Risk", deadline=SIGN, requests=["E01"], sources=["L01", "L02", "L03", "L21", "V04", "V17"],
        residual_risk=("Legal uncertainty remains until a court or the data protection authority rules; contract warranty and re-calibration "
                       "right reduce it. Residence time also correlates with age, which s.37a bans as an input, so the criterion may draw challenge on both grounds."),
        escalation="Becomes Critical if VENDOR keeps the criterion unchanged and Mainkai's counsel concludes it is address data."),
    Finding(id="F02", title="No outcomes evidence on Mainkai's own applicants",
        element="G; H", status=Status.not_public, rating=Rating.high, basis="fact",
        observation=("The only public performance figure is a company-reported Gini of 0.6 with no sample, period, product or interval (V12). "
                     "That figure is measured on the bureau's whole population and cannot be compared with a Gini on Mainkai's applicants, which is lower by "
                     "construction. Mainkai's tolerance is therefore relative: on the same retro-scored applicants, the new score may not lose more "
                     "than 3 Gini points against the current score (lower 95% bound of the paired difference), and must be calibrated within "
                     "tolerance in every pricing band. Testing a new score version on "
                     "a bank's own book needs VENDOR to score the bank's historical applicants retrospectively (V20). The Bondora proxy run (section 3) demonstrates the paired test and rank ordering; its absolute Gini ([[oot_gini]]) is not comparable, because the sample holds approved loans only (B03)."),
        why_it_matters=("Outcomes analysis is a core element and cannot be rated on public evidence. Under outcome rule 3 this alone defers the decision. "
                        "MaRisk requires Mainkai to assess a third-party model's suitability before use and validate it regularly (AT 4.3.4 Tz. 2 and 5), "
                        "and to form its own judgement of default risk rather than rely exclusively on external credit assessments (BTO 1.2 Tz. 5) (L11)."),
        condition=("VENDOR to retro-score a sample of Mainkai Ratenkredit applications (24 to 36 months, approvals and declines) with both the new "
                   "and the current score. Mainkai Model Validation computes the paired Gini difference with a bootstrap interval, calibration "
                   "by pricing band and class migration."),
        owner="Head of Model Validation", deadline=SIGN, requests=["E02", "E03"], sources=["V12", "V20", "B03", "L11"],
        residual_risk="Back-testing covers approved loans only; reject inference remains a limitation."),
    Finding(id="F03", title="Thin-file segments: calibration within segments not evidenced",
        element="E; H; D9", status=Status.not_public, rating=Rating.high, basis="assessment",
        observation=("No segment performance is public, so nothing shows that a given score carries the same default risk for thin-file "
                     "applicants as for everyone else. A lower score for a short credit history is expected by design; the open question is "
                     "whether the score is calibrated within those segments. Context from the calculator: time-dependent criteria hold [[time_points]] of 999 "
                     "points, and with perfect payment behaviour and no mortgage a person one year into the German credit file reaches at most [[ceiling_12m]] "
                     "(Class 2); Class 1 takes between [[class1_years_min]] and [[class1_years_max]] years, depending on unpublished annual bands. A consumer score app that displays the score says less "
                     "active persons may score somewhat worse (V18); the consumer federation expects young people to be more affected (L14). On "
                     "Bondora's data, the same grade carried between [[oe_min]] and [[oe_max]] times the expected default risk across segments (section 3, B03)."),
        why_it_matters=("Mainkai names under-25s and residents under 3 years as thin-file segments. A lower score is acceptable if it reflects "
                        "higher observed risk; without default rates by score band within each segment Mainkai cannot show that, apply its 0.80 "
                        "approval-rate screen or write the FRIA."),
        condition=("VENDOR to provide score distribution, default rate by score band and Gini within each age band and time-in-file band, and its "
                   "bias examination. Mainkai computes approval-rate ratios on retro-scored data before setting cut-offs."),
        owner="Head of Credit Risk", deadline=LIVE, requests=["E04", "E05"], sources=["V02", "V03", "V04", "V18", "L14", "B03"],
        residual_risk="Even with evidence, time-based criteria act as a partial age proxy; s.37a bans age as an input, not correlated inputs."),
    Finding(id="F04", title="Points table incomplete for policy simulation",
        element="E; F", status=Status.inadequate, rating=Rating.medium, basis="fact",
        observation=("Annual values are unpublished for bank-contract age (years 2 to 3, 5 to 9, 11 to 19), card age (years 2 to 4, 6 to 9) and "
                     "address age (years 2 to 9). The debt-collection inquiry effect has no published value. Criteria 4, 5, 8 and 9 and the class boundaries were confirmed "
                     "by the author on the bureau's own pages (V21, V22)."),
        why_it_matters=("Individual explanations are still possible because each bureau report shows points per criterion, but Mainkai cannot "
                        "simulate cut-off changes or explain policy effects without the full table."),
        condition="VENDOR to supply the complete band table with boundary and rounding rules under NDA.",
        owner="Head of Credit Risk", deadline=SIX, requests=["E06"], sources=["V01", "V02", "V03", "V04", "V22"],
        residual_risk="Low once the table is supplied and version-controlled."),
    Finding(id="F05", title="Independent review exists but its content is not available",
        element="J", status=Status.inadequate, rating=Rating.high, basis="fact",
        observation=("VENDOR reports a Fraunhofer IAIS review confirming scientific quality and data relevance, a data protection authority finding "
                     "of applicability, and review by two university departments (V12, V13). Scope, version reviewed, date and findings are not public."),
        why_it_matters="Mainkai's validators cannot rely on a review they have not read; reliance must be documented for BaFin.",
        condition="VENDOR to provide the review reports or a summary letter stating scope, model version, date, findings and limitations.",
        owner="Head of Model Validation", deadline=SIGN, requests=["E07"], sources=["V12", "V13"],
        residual_risk="Mainkai still owns effective challenge; the external review supplements it."),
    Finding(id="F06", title="Target definition and development documentation not available",
        element="A; D", status=Status.inadequate, rating=Rating.high, basis="fact",
        observation=("The method (logistic regression, points from group default rates) is public (V12, V13). The target event, horizon, development "
                     "and validation samples, exclusions and log-odds scaling are not. Fitness for unsecured instalment lending is not stated."),
        why_it_matters=("Mainkai must reconcile VENDOR's target with its own default definition before it can map scores to PDs and pricing bands. "
                        "MaRisk AT 4.3.4 Tz. 2 requires sufficient knowledge of the model's design, key assumptions, parameters and input data before use (L11)."),
        condition="VENDOR to supply a development summary covering target, horizon, samples, exclusions, scaling and intended uses.",
        owner="Head of Model Validation", deadline=SIGN, requests=["E03"], sources=["V12", "V13", "L11"],
        residual_risk="Low to medium once received; residual mismatch handled through Mainkai's own calibration."),
    Finding(id="F07", title="Version and change management not evidenced",
        element="K; P9; P10", status=Status.not_public, rating=Rating.high, basis="fact and assessment",
        observation=("Older sector models expire on 31 Dec 2028 and older scores were adjusted for s.37a (V17); further change to the new score is "
                     "plausible (F01). No public policy defines material change, notice periods or parallel runs. A significant design change after "
                     "2 Dec 2027 would also bring the score under the AI Act (L08)."),
        why_it_matters="Unannounced re-weighting would silently move approval rates and prices; Mainkai needs time to re-test and re-set cut-offs.",
        condition=("Contract to require advance notice of model changes (at least 90 days), a material-change definition, parallel scoring, "
                   "and re-validation evidence for each new version."),
        owner="Head of Third-Party Risk", deadline=SIGN, requests=["E09"], sources=["V17", "L08"],
        residual_risk="Medium: notice protects planning but not the outcome of a change."),
    Finding(id="F08", title="Third-party classification and DORA contract baseline",
        element="K; T1", status=Status.mainkai, rating=Rating.high, basis="assessment",
        observation=("Since MaRisk 06/2026, ICT services under Art 3(21) DORA fall outside AT 9 (L11). Score delivery is an ongoing data service "
                     "through ICT systems, so the most likely classification is a DORA ICT service supporting a critical or important function "
                     "(credit origination). Under MaRisk, retrieving a standard bureau score is generally treated as other external "
                     "procurement (sonstiger Fremdbezug, AT 9 Tz. 1), not outsourcing; AT 9 would matter only if VENDOR built or ran a model customised to "
                     "Mainkai's underwriting. Either way, the DORA classification sets the contract baseline. Contract, SLAs, assurance reports "
                     "and exit terms are not public."),
        why_it_matters="Classification sets the contract baseline (Art 30(2) and (3)), the register entry and the exit plan; getting it wrong leaves gaps BaFin will test.",
        condition=("Mainkai to document the classification, map the contract to Art 30(2) and (3), add the register-of-information entry and an exit "
                   "plan that keeps origination running if the score is withdrawn."),
        owner="Head of Third-Party Risk", deadline=SIGN, requests=["E11"], sources=["L11", "L16"],
        residual_risk="Concentration risk on a dominant bureau remains; exit options are limited."),
    Finding(id="F09", title="AI Act status contested; readiness plan needed",
        element="M; P1 to P10; D1 to D10", status=Status.not_due, rating=Rating.medium, basis="assessment",
        observation=("Annex III point 5(b) targets credit scoring, and VENDOR describes the method as learning from data (V12). The Commission's "
                     "guidelines place logistic regression used to improve optimisation outside the definition (L09). The score was placed on the "
                     "market in March 2026, so under Art 111(2) it is caught only after a significant design change following 2 Dec 2027 (L08)."),
        why_it_matters="If in scope, Mainkai needs Art 13 information to meet Arts 26 and 27, including a FRIA notified to BaFin.",
        condition=("Adopt a precautionary in-scope position; contract for VENDOR to supply Art 13 instructions for use, logging and incident "
                   "information if the score becomes in scope; prepare a FRIA outline now."),
        owner="Head of Compliance (AI governance)", deadline=SIX, requests=["E12"], sources=["L08", "L09", "V12"],
        residual_risk="Low: GDPR, s.37a BDSG and MaRisk already require most of the same controls."),
    Finding(id="F10", title="Decline notices, explanation and contest route must meet ss.30(6)-(7) and 37a(5) BDSG",
        element="L; D10; G1; G3", status=Status.inadequate, rating=Rating.high, basis="fact and assessment",
        observation=("Points per criterion allow a person-level explanation. From 20 Nov 2026, s.37a(5) gives applicants a right to contest and to a "
                     "decision by a natural person against the lender (L04). The BGH held Art 15(1)(h) applies only where Art 22(1) is met, but a "
                     "transmitted score followed by an adverse decision raises a presumption (L05). The act itself sets three lender duties for consumer "
                     "loans (L01): under s.30(6), where the creditworthiness check is automated the borrower may demand human intervention, a clear "
                     "explanation including the logic and risks, to state a view and a review, and must be told of these rights; under s.30(7) "
                     "sentence 1, a rejection resulting from credit-agency information must be notified at once with the information received, "
                     "details of the database consulted and the data categories considered; under s.30(7) sentence 2, a rejection resting on "
                     "automated processing must also state the right to review by a person and the procedure to contest. Failing to inform under "
                     "s.30(6) sentence 3 or s.30(7) is an administrative offence (s.43(1) No. 2 BDSG), and consumer associations can sue over "
                     "ss.30 and 37a (s.2(2) No. 14 UKlaG as amended)."),
        why_it_matters=("Auto-declines below the cut-off will usually meet the presumption and trigger both sentences of s.30(7), so every decline "
                        "needs a compliant notice from the first day of go-live; a gap is a finable offence, not just a quality issue."),
        condition=("Mainkai to rebuild decline letters and the underwriter review script around the 12 criteria, name the bureau database and data "
                   "categories in every decline that rests on bureau information (s.30(7) sentence 1), state the right to review by a person and the "
                   "contest procedure in every automated decline (sentence 2), and agree with VENDOR the data-correction turnaround for disputed entries."),
        owner="Head of Retail Lending Operations", deadline=LIVE, requests=["E13"], sources=["L01", "L04", "L05", "L07"],
        residual_risk="Low once notice templates are tested on real declines and reviewed by Legal before go-live."),
    Finding(id="F11", title="Data quality and correction process not evidenced",
        element="C; D4", status=Status.not_public, rating=Rating.high, basis="fact",
        observation=("VENDOR publishes the categories of data it stores and their deletion periods, for example inquiries after 12 months and "
                     "settled claims after 3 years (V23). Data lineage, reporting coverage (for example which accounts count as bank contracts), "
                     "quality KPIs and dispute volumes are not public. The consumer federation reports a correction of address-age data offered only against a paid registration certificate (L14)."),
        why_it_matters="Wrong inputs produce wrong declines; Mainkai's human reviewers need a fast route to correct bureau data.",
        condition="VENDOR to provide data-quality KPIs, coverage by criterion and dispute statistics; contract a correction SLA.",
        owner="Head of Third-Party Risk", deadline=LIVE, requests=["E08"], sources=["L14", "V02", "V23"],
        residual_risk="Medium: data accuracy depends on reporting firms outside VENDOR's control."),
    Finding(id="F12", title="Monitoring pack and thresholds not yet defined",
        element="I; D5", status=Status.not_public, rating=Rating.medium, basis="assessment",
        observation=("Art 26(5) monitoring can be met through MaRisk governance, but needs VENDOR population reports and Mainkai's own approval, "
                     "override and default tracking by score band and segment. On Bondora's data the overall default rate was [[dr_oot]] in 2025 against "
                     "[[dr_ref]] in the reference period, while [[grades_worse]] grades worsened, because the mix shifted to the best grade (section 3, B03)."),
        why_it_matters="Without baselines at go-live, drift and segment effects will be found late.",
        condition="Mainkai to set PSI, approval-rate and override thresholds with owners; VENDOR to supply quarterly population reports.",
        owner="Head of Credit Risk", deadline=SIX, requests=["E10"], sources=["L17", "B03"],
        residual_risk="Low once in operation."),
    Finding(id="F13", title="Mainkai's own loan moves its borrowers' scores",
        element="G", status=Status.not_applicable, rating=Rating.medium, basis="assessment",
        observation=("In the calculator a 60-month Ratenkredit lowers the score by [[loan60_drop]] points and a 96-month loan by [[loan96_drop]], through three "
                     "criteria at once (loans taken, remaining term, credit status). The under-25 archetype falls from Class 2 to Class 4."),
        why_it_matters=("Top-up and repeat lending decisions will see scores depressed by Mainkai's own loans; term choice changes the customer's "
                        "future access to credit."),
        condition="Mainkai to reflect own-exposure effects in top-up policy and monitoring, and to tell applicants how loan term affects their score.",
        owner="Head of Credit Risk", deadline=SIX, requests=[], sources=["V22", "V07"],
        residual_risk="Low; policy design issue rather than a model defect."),
    Finding(id="F14", title="Consumer-facing reason texts",
        element="L", status=Status.inadequate, rating=Rating.low, basis="fact",
        observation="The consumer federation reports generic replies to follow-up questions about score changes (L14).",
        why_it_matters="Plain reason texts reduce complaints and support s.37a(4) explanations.",
        condition="Agree a plain-German reason-text catalogue for the 12 criteria with VENDOR.",
        owner="Head of Retail Lending Operations", deadline=SIX, requests=["E13"], sources=["L14"],
        residual_risk="Low."),
]

REQUESTS = [
    Request(id="E01", item="Written legal position on criterion 4 (age of current address) under s.37a(2) No.1(d) BDSG, the model version to be delivered after 20 Nov 2026, and if changed the revised table and a score-migration analysis.",
            why="Lawful use of the score from 20 Nov 2026.", test="Counsel review; re-run calculator and cut-off simulation on the revised table.",
            findings=["F01"], deadline=SIGN, owner="Head of Legal"),
    Request(id="E02", item="Retrospective scores for Mainkai Ratenkredit applications from the last 24 to 36 months (approved and declined), at each application date, with model version.",
            why="Only way to measure discrimination and calibration on Mainkai's own book.", test="Paired Gini difference, new minus current score, with 95% bootstrap interval (lower bound above -0.03), calibration by pricing band, class migration.",
            findings=["F02", "F03"], deadline=SIGN, owner="Head of Model Validation"),
    Request(id="E03", item="Development and validation summary: target event and horizon, default definition, development and hold-out samples, exclusions, scaling from log-odds to points, Gini by industry and for consumer instalment loans with intervals.",
            why="Conceptual soundness and reconciliation to Mainkai's default definition.", test="Read-across to Mainkai's EBA default definition; check Gini claim against samples.",
            findings=["F02", "F06"], deadline=SIGN, owner="Head of Model Validation"),
    Request(id="E04", item="Score distribution, default rate and Gini by age band (18-24, 25-34, 35-49, 50+) and by time in file (<1, 1-3, 3+ years), including people holding no card or no bank contract.",
            why="Segment fitness for named thin-file groups.", test="Observed versus implied risk per segment; approval-rate ratio screen at 0.80.",
            findings=["F03"], deadline=LIVE, owner="Head of Credit Risk"),
    Request(id="E05", item="VENDOR's bias examination and its assessment of age-proxy effects of time-dependent criteria.",
            why="FRIA input and AI Act Art 10 style evidence.", test="Compare with E04 results; document in FRIA.",
            findings=["F03"], deadline=LIVE, owner="Head of Compliance"),
    Request(id="E06", item="Complete points table: every band and boundary, rounding, grace rules, debt-collection inquiry effect, which contracts count as bank contracts, missing-value and no-score rules.",
            why="Policy simulation and explanation accuracy.", test="Load into the calculator; reconcile 100 delivered reports to the cent.",
            findings=["F04"], deadline=SIX, owner="Head of Credit Risk"),
    Request(id="E07", item="Fraunhofer IAIS review report (or summary letter) and the university reviews: scope, version, date, findings, limitations; scope of the data protection authority finding.",
            why="Basis for reliance on independent challenge.", test="Map review scope to elements C, D, G; identify gaps for Mainkai's own validation.",
            findings=["F05"], deadline=SIGN, owner="Head of Model Validation"),
    Request(id="E08", item="Data governance: sources and reporting coverage per criterion, data-quality KPIs, dispute and correction volumes and turnaround, refresh cycle.",
            why="Input accuracy and correction route.", test="Check coverage of Mainkai's applicant profile; set correction SLA.",
            findings=["F11"], deadline=LIVE, owner="Head of Third-Party Risk"),
    Request(id="E09", item="Change policy: material-change definition, notice period, parallel-scoring support, recalibration schedule, sunset plan for older scores.",
            why="Controlled adoption of future versions.", test="Contract clause review; dry-run of a version switch.",
            findings=["F07"], deadline=SIGN, owner="Head of Third-Party Risk"),
    Request(id="E10", item="Quarterly population report: score and class distribution, PSI against the reference period, dispute and override statistics.",
            why="Art 26(5) monitoring and MaRisk model monitoring.", test="Set thresholds: PSI <0.10 green, 0.10-0.25 amber, >0.25 red.",
            findings=["F12"], deadline=SIX, owner="Head of Credit Risk"),
    Request(id="E11", item="ICT third-party pack: DORA Art 30(2)/(3) clause mapping, SLAs (availability, latency), incident notification, ISAE 3402 or SOC 2 Type II report, penetration-test summary, BCP test results, subcontractors, data location, exit support.",
            why="DORA contract baseline and register entry.", test="Gap list against Art 30; exit plan test.",
            findings=["F08"], deadline=SIGN, owner="Head of Third-Party Risk"),
    Request(id="E12", item="VENDOR's position on AI Act Art 3(1) status and Art 111(2) legacy treatment, and a commitment to supply Art 13 instructions for use, logging and incident information if in scope.",
            why="Deployer readiness for 2 Dec 2027.", test="Map to rows P1 to P10 and D1 to D10.",
            findings=["F09"], deadline=SIX, owner="Head of Compliance"),
    Request(id="E13", item="Sample s.37a(4) explanation letter, reason-text catalogue for the 12 criteria, and the process and turnaround for data disputes raised during s.37a(5) reviews.",
            why="Explanation and contest duties at the lender.", test="Test decline letters with five archetype cases.",
            findings=["F10", "F14"], deadline=LIVE, owner="Head of Retail Lending Operations"),
    Request(id="E14", item="Per-inquiry log content (score version, criterion points, input snapshot) and retention period.",
            why="Art 26(6) logs, s.37a(4) one-year record, complaint handling.", test="Confirm Mainkai credit-file retention covers at least 6 months and the s.37a period.",
            findings=["F10", "F12"], deadline=LIVE, owner="Head of IT Risk"),
]

# Obligation matrix: (actual_status, rating, finding/notes) per row of obligation_matrix.csv
OBLIGATION_FILL = {
    "P1": ("Not publicly available", "Medium", "F09; request via E12. Not yet due (2 Dec 2027)."),
    "P2": ("Available but inadequate", "High", "F03, F11; criteria public, no bias tests or representativeness data."),
    "P3": ("Not publicly available", "Medium", "F06, F09; development summary requested (E03). Legacy rule may defer."),
    "P4": ("Not publicly available", "Medium", "E14; log content and retention."),
    "P5": ("Available but inadequate", "High", "F03, F06; criteria explained, no limitations or segment accuracy."),
    "P6": ("Available but inadequate", "Medium", "Points per criterion support oversight; no reliance guidance (F10)."),
    "P7": ("Available but inadequate", "High", "F02; company-reported Gini 0.6 only."),
    "P8": ("Not publicly available", "Medium", "F09; QMS overview via E12."),
    "P9": ("Not yet due", "Low", "Legacy rule Art 111(2); watch for significant change (F07)."),
    "P10": ("Not publicly available", "Medium", "F07, F12; monitoring plan and incident route."),
    "D1": ("Mainkai-side", "Low", "Training for underwriters on the 12 criteria."),
    "D2": ("Mainkai-side", "Medium", "Blocked by P5 until VENDOR supplies use instructions."),
    "D3": ("Mainkai-side", "Medium", "Underwriter mandate exists in scenario; update for s.37a(5) reviews (F10)."),
    "D4": ("Mainkai-side", "Medium", "Input controls; depends on bureau correction route (F11)."),
    "D5": ("Mainkai-side", "Medium", "F12; needs VENDOR population reports (E10)."),
    "D6": ("Mainkai-side", "Low", "E14; confirm retention."),
    "D7": ("Mainkai-side", "High", "DPIA needed now under GDPR Art 35 regardless of AI Act; blocked in part by P5."),
    "D8": ("Mainkai-side", "Low", "Application-journey wording; draft once AI Act position fixed (F09)."),
    "D9": ("Mainkai-side", "Medium", "FRIA outline in report annex; needs E04, E05 (F03)."),
    "D10": ("Available but inadequate", "Medium", "Feasible from points per criterion (F10)."),
    "G1": ("Mainkai-side", "Medium", "s.505a BGB from 20 Nov 2026; human review route (F10)."),
    "G2": ("Not publicly available", "High", "F01; address-age criterion versus s.37a(2) No.1(d)."),
    "G3": ("Available but inadequate", "Medium", "F10; BGH 21 Oct 2026 presumption; C-203/22 standard."),
    "M1": ("Not publicly available", "High", "F02, F05, F06; core elements G, H, J."),
    "T1": ("Mainkai-side", "High", "F08; DORA ICT service, Art 30 baseline."),
}
