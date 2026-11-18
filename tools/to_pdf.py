"""HTML -> PDF with headless Chrome (Playwright). Usage: python tools/to_pdf.py in.html out.pdf [label]"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

src, dst = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
label = sys.argv[3] if len(sys.argv) > 3 else "Public-evidence review. Not an audit, validation or legal opinion."
foot = (f'<div style="font-family:Inter,DejaVu Sans,sans-serif;font-size:6.5px;letter-spacing:.04em;color:#6b6b6b;width:100%;'
        f'padding:0 16mm;display:flex;justify-content:space-between"><span>{label}</span>'
        '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>')
with sync_playwright() as p:
    try:
        b = p.chromium.launch()
    except Exception:  # fall back to a system Chrome
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_page()
    pg.goto(src.as_uri(), wait_until="networkidle")
    pg.pdf(path=str(dst), format="A4", print_background=True, display_header_footer=True,
           header_template="<span></span>", footer_template=foot,
           margin=dict(top="15mm", bottom="16mm", left="0mm", right="0mm"), prefer_css_page_size=False)
    b.close()
print("pdf", dst)
