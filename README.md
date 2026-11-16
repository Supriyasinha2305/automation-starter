# automation-starter

Starter repo for SQValex's AI-Led QE training program, Weeks 8-11 (Test
Automation Coding). Download it from SQValex (Week 8's Practical tab), push it
to a new public repository of your own on GitHub, then write real Playwright +
pytest tests against your own PolicyHub instance and push them — SQValex
verifies your practical checks by reading your repo's file tree and latest
GitHub Actions run through the public GitHub API. It never runs your code
itself.

## What's in here

| Path | What it's for |
|---|---|
| `conftest.py` | Shared fixtures - `base_url` (from `POLICYHUB_URL`), `home_page` |
| `pages/` | Page Object classes wrapping PolicyHub screens (`QuotePage`, `HomePage`, `PolicyPage`) |
| `tests/test_quote_flow.py` | Week 8's working example - submit a quote, confirm a premium renders, confirm binding it updates the home page's policy count |
| `.github/workflows/tests.yml` | Runs the suite on every push |
| `policyhub/` | A vendored, throwaway copy of PolicyHub, used **only by CI** (see below) - don't edit it |

## Setup

```bash
python -m venv venv
# macOS/Linux: source venv/bin/activate
# Windows:     venv\Scripts\activate
pip install -r requirements.txt
playwright install
```

## Running against your own PolicyHub instance

Launch your PolicyHub instance from SQValex (Training > this week's lab has
a **Launch PolicyHub** button), note its URL, then:

```bash
# macOS/Linux
export POLICYHUB_URL=http://127.0.0.1:<your-port>
# Windows PowerShell
$env:POLICYHUB_URL = "http://127.0.0.1:<your-port>"

pytest
```

Never hardcode your instance's URL into a test file - the whole suite reads
it from this one environment variable, which is what lets the exact same
tests run unmodified against your instance, a classmate's, or CI's.

## Why there's a `policyhub/` folder in here

Your own PolicyHub instance runs on your machine and isn't reachable from
GitHub's CI runners. So this repo also vendors a small, throwaway copy of
PolicyHub - used *only* by `.github/workflows/tests.yml` to spin up a fresh,
disposable instance inside the CI runner itself, just long enough to prove
your suite actually passes end to end. Locally, you keep testing against
your own real SQValex-provisioned instance as usual; the vendored copy is
CI-only plumbing, not something to develop against or edit.

## Submitting your practical check

Once you've pushed to your own public GitHub repo, submit its URL on the
relevant week's page in SQValex (Weeks 8-11). SQValex reads your repo's
file tree and latest Actions run via the public GitHub API - each week
checks for a specific, increasing bar:

| Week | What's checked |
|---|---|
| 8 | At least one `test_*.py` file exists |
| 9 | 3+ test files, plus a `conftest.py` with a shared fixture |
| 10 | A `.github/workflows/*.yml` file, and your **latest** Actions run succeeded |
| 11 | 5+ test files, a `conftest.py`, a workflow file, and a green latest run |

Your repo must be **public** for SQValex to read it (GitHub's REST API only
reads public repos here, unauthenticated).
