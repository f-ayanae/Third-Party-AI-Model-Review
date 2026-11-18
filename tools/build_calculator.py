"""Embed lab/points_table.yaml into the self-contained calculator page."""
import json
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
t = yaml.safe_load((ROOT / "lab/points_table.yaml").read_text())
for c in t["criteria"]:
    c.pop("sources", None)
html = (ROOT / "templates/calculator_template.html").read_text().replace("/*TABLE*/null", json.dumps(t))
(ROOT / "deliverables/calculator.html").write_text(html)
print("calculator.html built")
