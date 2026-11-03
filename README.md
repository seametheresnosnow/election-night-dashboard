# 2026 Election Night Dashboard

A mobile-friendly Streamlit starter for national, Maine, and Vermont election results.

## Deploy without installing Python

1. Sign in to GitHub and create a **new public repository** named `election-night-dashboard`.
2. Choose **Add file → Upload files** and upload `app.py`, `requirements.txt`, `README.md`, and the `data` folder contents, preserving the folder structure. GitHub's browser upload supports dragging the unzipped folder contents; confirm `data/sample.csv` and `data/template.csv` appear in the repository.
3. Visit https://share.streamlit.io/ and sign in using GitHub.
4. Select **Create app → Deploy a public app from GitHub**, choose your repository, branch `main`, and entrypoint `app.py`.
5. Deploy and open the provided app URL.

## Running locally (optional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Live results

The starter app deliberately **does not claim to have a verified election-results API**. Use Upload CSV to provide results or Public CSV URL for a legally accessible machine-readable feed. A public CSV URL is re-fetched when you click Refresh data or rerun the page; it is cached for 60 seconds. It does not run unattended or persist snapshots. Do not use a webpage URL that serves HTML instead of CSV.

Schema: `timestamp_utc,region,state,race,geography,candidate,party,votes`.

Each row is a cumulative candidate total at a particular timestamp and a nonoverlapping geographic unit. To show change over time, append complete snapshots with new timestamps. Do not mix state totals and counties in the same race.

The included sample numbers and candidate labels are **fictional**.

## Cautions

- Never infer a winner from an incomplete count.
- Do not treat shares among listed candidates as official shares if candidates are missing.
- Maine ranked-choice rounds may require separate reporting and cannot be inferred from first-choice totals.
- Streamlit Community Cloud local files are ephemeral; use an external persistent store for unattended collection.
- Check permissions and rate limits before using a third-party data feed.
