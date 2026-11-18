"""Prose and anonymisation lint for the public repo. Fails CI on:
em dashes, banned self-descriptions, and vendor names in public files."""
import re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SKIP = {"private", ".git", ".venv", "__pycache__", "raw_named", "out"}
PUBLIC_EXT = {".md", ".py", ".yaml", ".csv", ".j2", ".html", ".yml"}
import hashlib
VENDOR_HASHES = {'c9022b91a83a741282eb8869b066b23b2e655201eed6b5c827960968b461ad6a','f08f30e7c133c0d762dd0129f038547b5004756bd6d27ee1f5bc8cd4a89425c9','2e737c2291bc3c37863607197788b1306d4abaa0f67eba3308c97cc709499919','e4d9ea270424dd4384d1517d9a809562e0819fe3c9cea4f869f9f5c47f1a1d19'}  # sha256 of lower-case vendor words; names are not spelled out in the public repo

def vendor_hit(text):
    for w in set(re.findall(r"[a-z]+", text.lower())):
        if hashlib.sha256(w.encode()).hexdigest() in VENDOR_HASHES:
            return True
    return False
BANNED = re.compile(r"\b(we|this review|this work|i) (audited|certified|validated)\b|\bnon-compliant\b|\bassurance opinion\b", re.I)
errors = []
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix not in PUBLIC_EXT or set(p.relative_to(ROOT).parts) & SKIP:
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if "\u2014" in t:
        errors.append(f"{p.relative_to(ROOT)}: em dash")
    if vendor_hit(t):
        errors.append(f"{p.relative_to(ROOT)}: vendor-identifying word")
    if p.name not in ("prose_lint.py", "models.py") and "tests" not in p.parts:
        for line in t.splitlines():
            if BANNED.search(line) and not re.search(r"\b(not|never|no)\b", line, re.I):
                errors.append(f"{p.relative_to(ROOT)}: banned wording '{BANNED.search(line).group(0)}'")
print("\n".join(errors) or "prose lint: clean")
sys.exit(1 if errors else 0)
