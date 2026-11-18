# SCOPE.md: Third-Party Model Review, public-evidence readiness review of a German credit bureau's score

Status: Step 1 complete, 12 November 2026
Author: Fiona Edocket
Nature of work: portfolio case study. Public-evidence review and method demonstration, not an audit, certification, validation or assurance opinion. The bureau is anonymised in this public version; a named version is kept privately for interviews.

## 1. Summary

Mainkai Direktbank AG (fictional) is deciding whether to make the bureau's new 12-criterion score (v1.0) its primary bureau score for consumer instalment loans. The use falls under AI Act Annex III point 5(b). The bureau is the provider and Mainkai the deployer. The review is a readiness assessment: German scoring and credit rules change on 20 November 2026 (§37a BDSG; CCD2 transposition, BGBl. 2026 I Nr. 139), and the AI Act high-risk date arrives on 2 December 2027 (Regulation (EU) 2026/1744).

## 2. Scenario

| Element | Definition |
| --- | --- |
| Lender | Mainkai Direktbank AG (fictional), Frankfurt am Main. Branchless direct bank, CRR credit institution, less significant institution supervised by BaFin and the Bundesbank. About EUR 9bn assets, 450,000 retail customers. Subject to MaRisk and CRD governance, so the Art 26(5) and 26(6) financial-institution provisions apply. |
| Business driver | Cut-offs are calibrated to the bureau's older bank-sector score. The bureau's March 2026 reform makes the 100 to 999 score its single cross-industry score, so credit policy must be re-set on the new scale. |
| Product | Mainkai Ratenkredit: unsecured instalment loan, EUR 1,000 to 50,000, 12 to 96 months, five risk-based pricing bands, online only. Consumer credit under §§491 ff. BGB as amended for CCD2. |
| Customer population | German-resident consumers aged 18+, about 120,000 applications a year. Named thin-file segments: under-25s; residents in Germany under 3 years; self-employed. Excluded: business lending, joint applications, mortgages. |
| Use case | Origination only: (1) auto-decline below a cut-off score; (2) pricing band; (3) maximum loan amount. Mainkai's affordability calculation (§505a BGB) is out of scope except where it interacts with the score. |
| Data flow | Application form + bureau report (score, score class, points per criterion) + verified income and expenses to Mainkai's decision engine. Step 6 checks whether §37a BDSG limits any input. |
| Decision path | Auto-approve above the upper cut-off, auto-decline below the lower, refer the middle band (about 20%) to an underwriter with override authority. Any applicant can ask for human review and an explanation. |
| Decision under review | Adopt the bureau's new score (v1.0) as the primary bureau score for the Ratenkredit? Approve / approve with conditions / defer pending evidence / reject. |
| Vendor | A large German credit bureau (named only in the private version). The bureau's score (v1.0): 12 published criteria, logistic regression, 100 to 999 points, live since 17 March 2026. |
| Data lab | (a) A replica scorer built from the bureau's published points. (b) Outcomes lab on Bondora's public Loan Dataset, labelled as a proxy showing the tests Mainkai should demand from the bureau. |

## 3. Roles

| Party | AI Act | GDPR and German law | Other |
| --- | --- | --- | --- |
| The bureau | Provider. EU-based, no authorised representative needed. | Independent controller (credit agency). Bound by §37a BDSG from 20 Nov 2026. Under C-634/21 its score can itself be an Art 22 decision where Mainkai relies on it decisively. | Data/ICT service provider. MaRisk AT 9 outsourcing vs other external procurement: Step 6. |
| Mainkai Direktbank AG | Deployer | Controller for the credit decision. Own §37a BDSG duties, §505a BGB test, Art 22 safeguards. | Model owner. Supervised by BaFin, also its AI Act market surveillance authority (KI-MIG). |
| Applicants | Affected persons (Art 86) | Data subjects (Arts 15(1)(h), 22); BGH rulings of 21 Oct 2026 on information rights | Consumers under the BGB |

Role trap: if Mainkai blends the bureau's score with its own data into a new scoring model, Mainkai becomes provider of that combined system. Scope decision: score used as delivered; cut-offs are policy rules, not a model change.

## 4. High-risk classification

1. AI system (Art 3(1)): the crux. For: points learned from data by logistic regression; output is a prediction shaping credit decisions; Annex III 5(b) targets this use. Against: once fitted it is a fixed additive points table, close to the simple prediction systems the Commission's definition guidelines exclude. Position: treat as in scope on a precautionary basis and state why.
2. Annex III point 5(b): yes. Fraud-detection exception not engaged.
3. Art 6(3) derogation: unavailable. An Annex III system that profiles natural persons is always high-risk; credit scoring is profiling under GDPR Art 4(4).
4. Legacy rule (Art 111): The new score (v1.0) went on the market in March 2026, before 2 Dec 2027, so it is generally caught only after a significant design change. The bureau has said the method would be validated again; plan for the obligations rather than rely on the exemption.
5. Consequence: if in scope, the bureau carries the Chapter III provider requirements and Mainkai Arts 4, 26, 27, 86. Independently, §37a BDSG, §505a BGB, GDPR Art 22, EBA GL/2020/06 and MaRisk apply now.

## 5. Review scope

In scope:
- Model-risk desk review, elements A to L (SR 26-2, PRA SS1/23), with EBA GL/2020/06 s4.3.4 and MaRisk as EU and German anchors.
- Data lab: replica scorer built from the bureau's published criteria, and Bondora outcomes proxy.
- AI Act readiness: provider evidence and deployer actions (obligation_matrix.csv).
- Third-party review: MaRisk AT 9 classification, DORA contract baseline, data use and exit.
- German consumer and data-protection layer: §37a BDSG, §505a BGB, GDPR Arts 15 and 22 with C-634/21, C-203/22 and the BGH rulings of 21 Oct 2026.

Out of scope: independent validation; audit or certification opinion; legal advice; Mainkai's affordability model; bureau fraud and identity products; the bureau's older scores except as migration baseline; conformity assessment; IRB use; full ISO/IEC 42001 assessment.

Evidence standard: public sources and public datasets only, each cached with URL, retrieval date and SHA-256 hash. The bureau is anonymised. Findings are labelled fact (with source) or assessment (with basis), worded "not publicly available" or "available but inadequate", never "non-compliant". Absence of public evidence is not a failing: the bureau's evidence duties run to its lending customers under contract. The scorer is a replica built from the published criteria, and its results describe the replica, not how the bureau scores real people. Bondora results are always labelled proxy evidence about a different model.

Independence statement: prepared by the author as a portfolio exercise. The author is not independent of the work and had no access to the bureau's data, code or contracts.

## 6. Decision criteria

Evidence status per item: publicly available and adequate / available but inadequate / not publicly available / not applicable.

| Rating | Definition |
| --- | --- |
| Critical | Mainkai could not lawfully use the score, or could not meet a deployer or §37a duty, with no workable fix before go-live |
| High | Material gap a contract condition or pre-go-live evidence could close |
| Medium | Gap to close within 6 months of go-live |
| Low | Good-practice improvement |

Outcome rules:
1. Approve: no Critical or High open; every deployer obligation has an owner and an evidence plan.
2. Approve with conditions: no Critical; each High has a condition with owner and pre-go-live deadline.
3. Defer pending evidence: one or more core elements (conceptual soundness, data, testing, outcomes analysis, independent challenge) cannot be rated on the evidence available. Ratability test: a core element can be rated only if some result is visible, not just the existence of a process (a reported figure, a published table or a stated review conclusion counts; a description of a procedure does not).
4. Reject: any Critical the bureau confirms it will not remediate.

Mainkai's stated tolerances (fictional): materiality high (about 120,000 decisions a year). Discrimination is judged champion-challenger: on the same retro-scored applicants, the new score may not lose more than 3 Gini points against the current score, judged on the lower 95% bound of the paired bootstrap difference. Calibration: observed 12-month default rates inside the predicted interval in every pricing band. An absolute Gini is reported for information only; the bureau's figure of more than 60 Gini points covers its whole population and cannot be compared with a Gini on Mainkai's applicants. PSI below 0.10 green, 0.10 to 0.25 amber, above 0.25 red. Approval-rate ratio below 0.80 for any age band or length-of-residence band triggers investigation (screening heuristic, not an EU legal test). Replica must show monotonic points in every criterion.

## Publication rules

- Who this is for: model risk and third-party risk teams first, AI governance second.
- Language: "public-evidence review", "readiness review" or "method demonstration". Never "audit", "assurance opinion", "certified", "validated" or "compliant" about this work.
- Artefact first: the report opens with the replica calculator and the source register, then the findings.
- What this does not prove: latency, availability, access control, secrets management, model updates, incident response, audit log retention, data residency. Each gets one line on the evidence a real lender or bureau would hold.
- Data: never redistribute raw Bondora rows; publish download code and aggregates (groups of at least 30 loans). Terms recorded in LICENCES.md.
- Naming: if the named version is ever published, send the bureau the factual statements first and include any reply.
- Review: no external practitioner review. Findings, ratings and tolerances are the author's own judgement, and the review says so in its limitations.
- Release: publish a first version with the limitations section, then improve.
