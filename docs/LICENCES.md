# Data and source licences

| Source | Licence position on 12 Nov 2026 | What this repo publishes |
|---|---|---|
| Bureau web pages and points table | Copyright in the text; facts free to use | My own summary of criteria and points, with citations and hashes of text captures. No copied pages. |
| Secondary consumer-finance pages (V10, V11) | Copyright in the text | Point values (facts) with citations |
| Bondora public loan dataset | Public download; no explicit reuse licence found. A research record states the raw data cannot be made public under the platform's terms (B02). | Harness code and aggregates of at least 30 loans. **No raw rows.** Investor export downloaded by the author and supplied on 12 Nov 2026; SHA-256 in data/bondora/PROVENANCE.csv. Raw file kept in the gitignored data/bondora/ folder. To do: record the terms shown on the download page, and email Bondora to confirm research use. |
| Legal texts (EUR-Lex, BGBl., Bundestag papers) | Official texts, reuse permitted | Citations and short paraphrase |
| Court and press reports | Copyright in the text | Paraphrase and citation only |

Synthetic fixture (`lab/bondora/fixture.py`, generated in memory when the tests or `make fixture` run; not saved to disk): MIT. It uses Bondora's column names but no Bondora data, and it is not evidence about anyone.

Note for employers: if a dataset licence is non-commercial, the code here can be reused but the results cannot simply be lifted into client work.
