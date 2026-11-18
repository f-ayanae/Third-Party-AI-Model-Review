"""One-off: restyle the review, memo and crosswalk from blue to the editorial monochrome house style
(serif headings, plain text, small-caps labels, thin rules), add a cover page and a memo header.
The blue originals are archived in archive/pdf_blue_2026-11-17/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Instrument+Serif:ital@0;1&family=Geist+Mono:wght@400;500&display=swap">'


def edit(path, pairs):
    p = ROOT / path
    t = p.read_text(encoding="utf-8")
    for a, b in pairs:
        assert t.count(a) == 1, (path, t.count(a), a[:80])
        t = t.replace(a, b)
    p.write_text(t, encoding="utf-8")
    print("edited", path)


REVIEW_CSS_OLD_START = ":root { --navy:#1f3a5f;"
review = (ROOT / "templates/review.html.j2").read_text(encoding="utf-8")
s = review.index(REVIEW_CSS_OLD_START)
e = review.index("</style>", s)
NEW_CSS = """:root { --ink:#111111; --ink2:#3d3d3d; --muted:#6b6b6b; --line:#dcdcdc; --tint:#f4f4f2;
        --serif:"Instrument Serif", "Times New Roman", Georgia, serif; --mono:"Geist Mono", "DejaVu Sans Mono", monospace; }
* { box-sizing:border-box; }
body { font-family: Inter, "DejaVu Sans", sans-serif; color:var(--ink); font-size:9.2pt; line-height:1.45; margin:0; }
h1 { font-family:var(--serif); font-weight:400; font-size:24pt; letter-spacing:-0.01em; margin:0 0 6px; line-height:1.05; }
h2 { break-after:avoid; page-break-after:avoid; font-family:var(--serif); font-weight:400; font-size:17pt; letter-spacing:-0.005em; margin:18px 0 8px; padding-bottom:4px; border-bottom:1px solid var(--ink); line-height:1.1; }
h3 { break-after:avoid; page-break-after:avoid; font-size:9.6pt; font-weight:600; margin:12px 0 4px; }
p { margin:0 0 7px; }
ul, ol { margin:0 0 7px 0; padding-left:17px; } li { margin-bottom:3px; }
.kicker { font-family:var(--mono); font-size:7pt; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); font-weight:400; }
.private { background:#111; color:#fff; font-family:var(--mono); text-align:center; padding:4px; font-size:7.5pt; letter-spacing:.08em; margin-bottom:6px; }
.meta { font-size:8pt; color:var(--muted); border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:5px 0; margin:6px 0 10px; }
.cols { display:flex; gap:16px; } .cols > div { flex:1; }
.box { background:var(--tint); border-left:2px solid var(--ink); padding:7px 10px; margin:6px 0 9px; }
.box.warn { border-left-color:var(--ink); background:var(--tint); }
table { width:100%; border-collapse:collapse; margin:5px 0 10px; font-size:8.1pt; page-break-inside:auto; border-top:1px solid var(--ink); }
th { background:none; color:var(--muted); font-family:var(--mono); font-size:6.6pt; letter-spacing:.08em; text-transform:uppercase; text-align:left; padding:5px 5px 4px; font-weight:400; vertical-align:bottom; border-bottom:1px solid var(--line); }
td { padding:4px 5px; border-bottom:1px solid var(--line); vertical-align:top; }
tr { page-break-inside:avoid; }
.small { font-size:7.6pt; } .muted { color:var(--muted); }
.r-Critical { color:#fff; background:#111; } .r-High { color:#fff; background:#555; }
.r-Medium { color:var(--ink); background:#fff; box-shadow: inset 0 0 0 1px var(--ink); } .r-Low { color:var(--ink); background:#e8e8e6; }
.pill { display:inline-block; padding:1px 6px; border-radius:0; font-family:var(--mono); font-size:6.6pt; font-weight:500; letter-spacing:.06em; text-transform:uppercase; white-space:nowrap; }
.fig { margin:6px 0 4px; text-align:center; } .fig img { width:100%; max-width:165mm; }
.cap { font-size:7.6pt; color:var(--muted); margin:0 0 10px; }
.pb { page-break-before:always; }
.memo { font-size:8.6pt; line-height:1.36; } .memo li { margin-bottom:2px; }
.memo-t td { padding:2.5px 5px; font-size:7.8pt; } .memo-t th { padding:3px 5px; }
.finding { border-top:1px solid var(--ink); padding:7px 0 4px; margin:0 0 8px; page-break-inside:avoid; }
.finding .hd { display:flex; justify-content:space-between; align-items:baseline; gap:8px; margin-bottom:3px; }
.finding .hd b { font-size:9.6pt; font-weight:600; }
.finding dl { display:grid; grid-template-columns: 27mm 1fr; gap:2px 8px; margin:0; font-size:8.2pt; }
.finding dt { color:var(--muted); font-family:var(--mono); font-size:6.8pt; letter-spacing:.06em; text-transform:uppercase; padding-top:1px; } .finding dd { margin:0; }
code { font-family:var(--mono); font-size:7.6pt; background:var(--tint); padding:0 3px; }
.tag { font-family:var(--mono); font-size:6.4pt; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); border:1px solid var(--line); padding:0 4px; white-space:nowrap; }
/* cover page */
.cover { height:255mm; display:flex; flex-direction:column; justify-content:space-between; page-break-after:always; }
.cv-top { display:flex; justify-content:space-between; border-bottom:1px solid var(--ink); padding-bottom:6px; }
.cv-mid { padding-top:40mm; }
.cv-mid h1 { font-size:40pt; line-height:1; margin:10px 0 14px; max-width:150mm; }
.cv-sub { font-size:11pt; color:var(--ink2); max-width:130mm; line-height:1.4; }
.cv-meta { border-top:1px solid var(--ink); margin:0; font-size:8.4pt; }
.cv-meta th { width:38mm; border-bottom:1px solid var(--line); }
.cv-meta td { border-bottom:1px solid var(--line); }
/* memo header and decision */
.memo-head { border-bottom:1px solid var(--ink); padding-bottom:6px; margin-bottom:8px; }
.memo-head .mh-title { font-family:var(--serif); font-size:24pt; line-height:1; margin:4px 0 8px; }
.mh { border-top:1px solid var(--ink); margin:0; font-size:8pt; }
.mh th { width:24mm; padding:3px 5px 3px 0; } .mh td { padding:3px 5px 3px 0; }
.decision { border-top:2px solid var(--ink); border-bottom:1px solid var(--ink); padding:7px 0 8px; margin:8px 0 10px; }
.decision .d { font-family:var(--serif); font-size:20pt; line-height:1.05; margin:3px 0 4px; }
.decision .r { font-size:8.3pt; color:var(--ink2); }
"""
review = review[:s] + NEW_CSS + review[e:]
review = review.replace("<style>\n@page { size: A4;", FONTS + "\n<style>\n@page { size: A4;", 1)
(ROOT / "templates/review.html.j2").write_text(review, encoding="utf-8")
print("review CSS replaced")

edit("templates/review.html.j2", [
    ('''<!-- ============================== PAGE 1: DECISION MEMO ============================== -->
<div class="memo">
<div class="kicker">Third-Party Model Review · Public-evidence readiness review · 12 November 2026</div>
<h1>Should Mainkai Direktbank adopt {{ v.score_name }} as its primary bureau score for consumer instalment loans?</h1>
<div class="meta">Prepared by Fiona Edocket as a portfolio case study. Mainkai Direktbank AG is fictional; {{ v.vendor_long }} is real{% if not v.named %} and anonymised in this version{% endif %}. This is a public-evidence readiness review and method demonstration. It is not an audit, a validation, a certification or a legal opinion, and it uses public sources only.</div>

<div class="banner"><div class="d">Recommendation: {{ outcome.decision }}</div>
<div class="r">''',
     '''<!-- ============================== COVER ============================== -->
<section class="cover">
  <div class="cv-top kicker"><span>Third-Party Model Review</span><span>Public-evidence readiness review</span></div>
  <div class="cv-mid">
    <div class="kicker">Case study · Model risk · Third-party risk</div>
    <h1>Assessing a credit bureau score ahead of Germany's new scoring rules</h1>
    <p class="cv-sub">Should Mainkai Direktbank adopt {{ v.score_name }} as its primary bureau score for consumer instalment loans?</p>
  </div>
  <table class="cv-meta"><tbody>
    <tr><th>Prepared by</th><td>Fiona Edocket</td></tr>
    <tr><th>Date</th><td>12 November 2026</td></tr>
    <tr><th>Version</th><td>{% if v.named %}Private named version{% else %}Public version; the bureau is anonymised{% endif %}</td></tr>
    <tr><th>Recommendation</th><td>{{ outcome.decision }}</td></tr>
    <tr><th>Status</th><td>Portfolio case study. Mainkai Direktbank AG is fictional; {{ v.vendor_long }} is real. Based on public sources only. Not an audit, a validation, a certification or a legal opinion.</td></tr>
  </tbody></table>
</section>

<!-- ============================== DECISION MEMO ============================== -->
<div class="memo">
<div class="memo-head">
  <div class="kicker">Decision memo</div>
  <table class="mh"><tbody>
    <tr><th>To</th><td>Credit Risk Committee, Mainkai Direktbank AG (fictional)</td></tr>
    <tr><th>From</th><td>Fiona Edocket, Third-Party Model Review</td></tr>
    <tr><th>Date</th><td>12 November 2026</td></tr>
    <tr><th>Subject</th><td>Adoption of {{ v.score_name }} as the primary bureau score for consumer instalment loans</td></tr>
  </tbody></table>
</div>

<div class="decision"><div class="kicker">Recommendation</div><div class="d">{{ outcome.decision }}</div>
<div class="r">'''),
])

edit("templates/crosswalk.html.j2", [
    ('<title>Model-risk crosswalk for a vendor credit score</title>\n<style>',
     '<title>Model-risk crosswalk for a vendor credit score</title>\n' + FONTS + '\n<style>'),
    ('body { font-family: Inter, "DejaVu Sans", sans-serif; color:#1b1b1b; font-size:7.3pt; line-height:1.3; margin:0; }',
     'body { font-family: Inter, "DejaVu Sans", sans-serif; color:#111; font-size:7.3pt; line-height:1.32; margin:0; }'),
    ('h1 { font-size:13pt; color:#1f3a5f; margin:0 0 2px; } .sub { color:#5b6573; font-size:7.6pt; margin-bottom:6px; }',
     'h1 { font-family:"Instrument Serif", Georgia, serif; font-weight:400; font-size:20pt; line-height:1; margin:0 0 4px; } .sub { color:#6b6b6b; font-size:7.4pt; margin-bottom:7px; }'),
    ('table { width:100%; border-collapse:collapse; } th { background:#1f3a5f; color:#fff; text-align:left; padding:3px 4px; font-weight:600; }',
     'table { width:100%; border-collapse:collapse; border-top:1px solid #111; } th { background:none; color:#6b6b6b; font-family:"Geist Mono", monospace; font-size:6pt; letter-spacing:.08em; text-transform:uppercase; text-align:left; padding:4px 4px 3px; font-weight:400; border-bottom:1px solid #dcdcdc; }'),
    ('td { padding:2.6px 4px; border-bottom:1px solid #d9dee5; vertical-align:top; } tbody tr:nth-child(even) td { background:#f6f8fa; }',
     'td { padding:2.6px 4px; border-bottom:1px solid #e3e3e3; vertical-align:top; }'),
    ('.core { font-size:6.5pt; color:#b4472f; font-weight:700; } .foot { color:#5b6573; font-size:6.8pt; margin-top:4px; }',
     '.core { font-family:"Geist Mono", monospace; font-size:5.8pt; letter-spacing:.06em; color:#111; border:1px solid #111; padding:0 2px; } .foot { color:#6b6b6b; font-size:6.6pt; margin-top:5px; border-top:1px solid #111; padding-top:4px; }'),
])

edit("tools/build_pdfs.py", [
    ("pg.goto(cw_html.resolve().as_uri())", 'pg.goto(cw_html.resolve().as_uri(), wait_until="networkidle")'),
    ("w.add_page(PdfReader(str(review)).pages[0])", "w.add_page(PdfReader(str(review)).pages[1])  # page 0 is the cover"),
])
edit("tools/to_pdf.py", [
    ("foot = (f'<div style=\"font-family:Inter,DejaVu Sans,sans-serif;font-size:7px;color:#5b6573;width:100%;'",
     "foot = (f'<div style=\"font-family:Inter,DejaVu Sans,sans-serif;font-size:6.5px;letter-spacing:.04em;color:#6b6b6b;width:100%;'"),
])
