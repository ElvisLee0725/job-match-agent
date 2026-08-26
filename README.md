# Job Match Agent

[![CI](https://github.com/ElvisLee0725/job-match-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/ElvisLee0725/job-match-agent/actions/workflows/ci.yml)

A personal tool that takes your resume, background, and behavioral-interview answers,
searches a target company's real open roles, and ranks the top 3 that best fit your
profile — with a plain-language explanation of why.

Currently supports **Oracle** (via their real Recruiting Cloud search API) plus a
generic "paste a job URL" flow for any single posting (e.g. a LinkedIn link).

## How it works

1. **Profile** — upload a resume (PDF/txt) + background notes + sample behavioral
   answers. Claude structures it into skills, seniority, domains, and a summary.
2. **Jobs** — search a company's open roles (built from your profile's seniority +
   top skills), or paste a specific job posting URL to add it directly.
3. **Matches** — cached postings are filtered by your location preferences (US-only /
   preferred states, applied in code, not left to the LLM), then Claude ranks the
   remaining candidates and returns the top 3 with a fit score and rationale.

## Project layout

```
backend/    FastAPI + SQLite + Anthropic SDK
frontend/   Next.js (App Router) + TypeScript
```

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
uvicorn app.main:app --port 8000
```

API docs (Swagger UI) at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App at `http://localhost:3000`. It expects the backend at `http://localhost:8000`
(configurable via `frontend/.env.local` → `NEXT_PUBLIC_API_BASE_URL`).

## Testing

```bash
cd backend
source .venv/bin/activate
pytest                              # unit + integration — offline, mocked, fast
python tests/manual/try_oracle_scrape.py   # hits the real live Oracle API
python tests/manual/try_resume_parse.py    # real Claude call
python tests/manual/try_match.py           # full real end-to-end run
```

The manual scripts are the only ones that touch real external services (Oracle's API,
Claude). Everything under `tests/unit/` and `tests/integration/` runs offline with all
external calls mocked.

### Continuous Integration

`.github/workflows/ci.yml` runs on every push/PR to `master`: the backend job installs
deps and runs `pytest` (offline suite only — the manual scripts that hit real services
never run in CI), and the frontend job runs `eslint` + `next build`. No secrets are
required since all external calls in the automated suite are mocked.

## Known limitations

- Only Oracle is implemented as a job source; adding another company means writing a
  new `JobSource` in `backend/app/sources/` and registering it in `registry.py`.
- The "paste a job URL" flow can't read JavaScript-rendered pages (it fetches plain
  HTML) — it'll return a clear error rather than garbage data if a page has no
  extractable text.
- Match results use short snippets from search, not full job descriptions, even for
  the final top 3.
- No deployment — everything runs locally; both servers need to be started manually.
