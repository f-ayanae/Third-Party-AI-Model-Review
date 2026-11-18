# Data manifest

Every dataset this project uses or produces, where it lives, and what may be published.

| Dataset | Location | Rows / size | Real or synthetic | Publish? |
|---|---|---|---|---|
| Published points table (12 criteria, all bands) | `lab/points_table.yaml` | 12 criteria | Real (public bureau pages and two secondary sources) | Yes, as facts with citations |
| Source register | `evidence/sources.csv` | 41 sources | Real; excerpts with checksums, original files hashed where saved (L01, L11) | Yes (vendor URLs withheld) |
| Source captures | `evidence/raw/*.md` | 41 files | Real text excerpts | Yes |
| Claims register | `evidence/claims.csv` | 23 claims | Real, each fact or assessment | Yes |
| Lab A outputs | `lab/out/*.csv`, `lab/out/*.png` | archetypes, ceiling (81 points), sensitivity (14 events), monotonicity, weights | Calculator results on hand-built profiles | Yes |
| Findings, obligations, evidence request | `deliverables/*.csv`, `deliverables/evidence_request.md` | 14 findings, 25 obligations, 14 requests | Review outputs | Yes |
| **Bondora loan dataset (investor export)** | `data/bondora/loan_dataset_investor.parquet` (converted from the supplied xlsx) | 843,755 loans, 30 columns, issued Feb 2009 to Sep 2026 | Real, pseudonymised loan records | **No.** Gitignored; in the private bundle only. Only aggregates of at least 30 loans are published |
| Bondora provenance log | `data/bondora/PROVENANCE.csv` | written on download | Real | Yes (URL, date, hashes only) |
| Bondora aggregates and charts | `lab/out/bondora/bondora_proxy/` | 303,949 loans analysed; summary.json, rank_ordering, segments, grade_drift, stability, 2 charts | Real, proxy evidence about a different lender | Yes, groups of 30 or more loans only |

## Getting the Bondora file

The current run used the investor export supplied on 12 Nov 2026 (hash in PROVENANCE.csv). To refresh it:

```bash
python lab/bondora/download.py                       # or --url <link from the public statistics page>
python lab/bondora/download.py --file ~/Downloads/loan_dataset_investor.xlsx
make bondora CSV=data/bondora/loan_dataset_investor.parquet
```

If the automatic download fails, download "Loan dataset" by hand from https://bondora.com/en/public-statistics/ and run
`python lab/bondora/download.py --file ~/Downloads/LoanData.zip`. Record the terms shown on the page in docs/LICENCES.md the same day.

The synthetic Bondora-format fixture (`lab/bondora/fixture.py`) is generated in memory by the tests and by `make fixture`; it is not saved to disk.
