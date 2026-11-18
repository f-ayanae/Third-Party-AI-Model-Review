PY ?= python
.PHONY: all register lab test render pdf calc named lint clean bondora fixture download
all: lab register test render pdf calc lint

register: ; $(PY) evidence/build_register.py
lab: ; $(PY) lab/run_lab.py
test: ; $(PY) -m pytest -q
render: ; cd src && $(PY) -m assurance.render
pdf:
	$(PY) tools/to_pdf.py deliverables/review.html deliverables/Third_Party_Model_Review.pdf
	$(PY) tools/build_pdfs.py
calc: ; $(PY) tools/build_calculator.py
lint: ; $(PY) tools/prose_lint.py

# Private named version: needs private/named_config.py and private/vendor_overlay.json
named:
	$(PY) evidence/build_register.py --named
	cd src && $(PY) -m assurance.render --named
	$(PY) tools/to_pdf.py private/build/review_named_PRIVATE.html private/build/Third_Party_Model_Review_NAMED_PRIVATE.pdf "PRIVATE named version for interviews only. Not an audit, validation or legal opinion."
	$(PY) tools/build_pdfs.py --named

# Bondora proxy run: make bondora CSV=/path/to/LoanData.csv
bondora:
	$(PY) lab/bondora/outcomes.py --file $(CSV)
	$(PY) lab/bondora/charts.py
fixture: ; cd lab/bondora && $(PY) outcomes.py --fixture

clean: ; rm -rf deliverables/* lab/out/* .pytest_cache

download: ; $(PY) lab/bondora/download.py
