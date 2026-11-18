"""Build the one-page decision memo and the landscape crosswalk PDFs.
Usage: python tools/build_pdfs.py [--named]"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
named = "--named" in sys.argv
if named:
    b = ROOT / "private" / "build"
    review, memo = b / "Third_Party_Model_Review_NAMED_PRIVATE.pdf", b / "Third_Party_Model_Decision_Memo_NAMED_PRIVATE.pdf"
    cw_html, cw_pdf = b / "crosswalk_named_PRIVATE.html", b / "Third_Party_Model_Crosswalk_NAMED_PRIVATE.pdf"
else:
    b = ROOT / "deliverables"
    review, memo = b / "Third_Party_Model_Review.pdf", b / "Third_Party_Model_Decision_Memo.pdf"
    cw_html, cw_pdf = b / "crosswalk.html", b / "Third_Party_Model_Crosswalk_OnePage.pdf"

with sync_playwright() as p:
    try:
        br = p.chromium.launch()
    except Exception:  # fall back to a system Chrome
        br = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    pg = br.new_page()
    pg.goto(cw_html.resolve().as_uri(), wait_until="networkidle")
    pg.pdf(path=str(cw_pdf), landscape=True, format="A4", print_background=True, prefer_css_page_size=True)
    br.close()
w = PdfWriter()
w.add_page(PdfReader(str(review)).pages[1])  # page 0 is the cover
w.write(str(memo))
print("built", memo.name, "and", cw_pdf.name)
