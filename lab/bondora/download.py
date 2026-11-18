"""Download Bondora's public loan dataset and record provenance.

Run this on your own machine (the build environment could not reach bondora.com).
Check the current download link on Bondora's public statistics page first:
    https://bondora.com/en/public-statistics/  ->  "Loan dataset"
The default URL below is the commonly cited one and may change.

Usage:
    python lab/bondora/download.py                      # default URL
    python lab/bondora/download.py --url <link>         # link copied from the page
    python lab/bondora/download.py --file LoanData.zip  # a file you downloaded by hand

Writes data/bondora/LoanData.csv, or for the 2026 xlsx investor export
data/bondora/loan_dataset_investor.parquet (both gitignored, never published),
and appends URL, date, size and SHA-256 to data/bondora/PROVENANCE.csv.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

DEFAULT_URL = "https://www.bondora.com/marketing/media/LoanData.zip"
DATA = Path(__file__).resolve().parents[2] / "data" / "bondora"


def xlsx_to_parquet(src, out: Path) -> None:
    """2026 investor export: one 'Loan Dataset' sheet with mixed-type date columns."""
    import pandas as pd  # needs python-calamine and pyarrow
    df = pd.read_excel(src, sheet_name="Loan Dataset", engine="calamine")
    for c in ("loan_issued_at", "early_repaid_at", "loan_last_recorded_action_date_local",
              "next_payment_date_local", "debt_occured_date_local"):
        df[c] = pd.to_datetime(df[c], errors="coerce")
    text = ("country", "loan_status", "loan_status_risk", "customer_risk_rating")
    for c in df.columns:
        if df[c].dtype == object and c not in text:
            df[c] = pd.to_numeric(df[c].map(lambda x: int(x) if isinstance(x, bool) else x), errors="coerce")
    for c in text:
        df[c] = df[c].astype("string")
    df.to_parquet(out, index=False)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--file")
    a = ap.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    if a.file:
        raw, source = Path(a.file).read_bytes(), f"manual:{Path(a.file).name}"
    else:
        req = urllib.request.Request(a.url, headers={"User-Agent": "third-party-model-review-research"})
        with urllib.request.urlopen(req, timeout=120) as r:
            raw, source = r.read(), a.url
    sha = hashlib.sha256(raw).hexdigest()
    is_xlsx = raw[:2] == b"PK" and (a.file or "").lower().endswith(".xlsx")
    if is_xlsx:
        out = DATA / "loan_dataset_investor.parquet"
        xlsx_to_parquet(io.BytesIO(raw), out)
        csv_bytes = out.read_bytes()
    elif raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            csv_bytes = z.read(name)
        out = DATA / "LoanData.csv"
        out.write_bytes(csv_bytes)
    else:
        csv_bytes = raw
        out = DATA / "LoanData.csv"
        out.write_bytes(csv_bytes)
    prov = DATA / "PROVENANCE.csv"
    new = not prov.exists()
    with prov.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["retrieved_at_utc", "source", "bytes", "sha256_download", "sha256_saved_file"])
        w.writerow([dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), source, len(raw), sha,
                    hashlib.sha256(csv_bytes).hexdigest()])
    print(f"saved {out} ({len(csv_bytes):,} bytes). Record the terms shown on the download page in LICENCES.md.")
    print(f"Next: make bondora CSV={out.relative_to(DATA.parents[1])}")


if __name__ == "__main__":
    main()
