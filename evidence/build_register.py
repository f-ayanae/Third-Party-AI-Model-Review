"""Write evidence/raw/<id>.md excerpts, sources.csv and claims.csv.

Two different checksums, kept apart on purpose:
  excerpt_sha256  SHA-256 of the recorded excerpt in evidence/raw/. It proves the excerpt has not changed since it
                  was written; it does NOT prove the excerpt matches the original page.
  file_sha256     SHA-256 of an original document saved in evidence/ (for example a statute PDF). Only this kind of
                  hash ties a source to the bytes that were published.

Usage:  python evidence/build_register.py            # public, vendor URLs withheld
        python evidence/build_register.py --named    # private register with URLs
Run after lab/run_lab.py and the Bondora run: claims quote figures from their outputs.
"""
from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from register_data import CLAIMS, RETRIEVED, SOURCES  # noqa: E402
from assurance.facts import fill  # noqa: E402

ROOT = Path(__file__).resolve().parent


def file_sha(s: dict) -> str:
    if not s.get("file"):
        return ""
    p = ROOT.parent / s["file"]
    if not p.exists():
        raise FileNotFoundError(f"{s['id']}: saved original {s['file']} is missing")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def capture_text(s: dict, named: bool) -> str:
    show_url = named or not s["vendor_identifying"]
    url = s["url"] if show_url else "[withheld in public version; see private named register]"
    title = s["title"]
    lines = [f"# {s['id']}: {title}", "", f"- URL: {url}", f"- Retrieved: {s.get('retrieved', RETRIEVED)}",
             f"- Tier: {s['tier']}",
             f"- Capture method: {s.get('capture', 'web-fetch/search text extraction (excerpt, not byte-exact HTML)')}"]
    if s.get("file"):
        lines.append(f"- Original file: {s['file']} (SHA-256 {file_sha(s)})")
    lines += ["", "## Facts extracted", ""]
    lines += [f"- {fill(f)}" for f in s["facts"]]
    return "\n".join(lines) + "\n"


def main(named: bool = False) -> None:
    if named:
        import json
        ov = json.loads((ROOT.parent / "private" / "vendor_overlay.json").read_text())
        for s in SOURCES:
            if s["id"] in ov:
                s.update(ov[s["id"]])
    raw = (ROOT.parent / "private" / "raw_named") if named else (ROOT / "raw")
    raw.mkdir(exist_ok=True)
    rows = []
    for s in SOURCES:
        text = capture_text(s, named)
        p = raw / f"{s['id']}.md"
        p.write_text(text, encoding="utf-8")
        show_url = named or not s["vendor_identifying"]
        rows.append({
            "id": s["id"], "tier": s["tier"], "title": s["title"],
            "url": s["url"] if show_url else "WITHHELD (vendor-identifying)",
            "retrieved_at": s.get("retrieved", RETRIEVED),
            "capture": "original file" if s.get("file") else ("author check" if s.get("capture") else "text excerpt"),
            "excerpt_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "file": s.get("file", ""), "file_sha256": file_sha(s),
            "vendor_identifying": s["vendor_identifying"],
        })
    out = (ROOT.parent / "private" / "sources_named.csv") if named else (ROOT / "sources.csv")
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with (ROOT / "claims.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["claim_id", "claim", "type", "source_ids", "checklist_item", "finding_id"])
        w.writerows([(c[0], fill(c[1]), *c[2:]) for c in CLAIMS])
    print(f"wrote {len(rows)} sources to {out.name} ({sum(1 for r in rows if r['file'])} with original files), {len(CLAIMS)} claims")


if __name__ == "__main__":
    main(named="--named" in sys.argv)
