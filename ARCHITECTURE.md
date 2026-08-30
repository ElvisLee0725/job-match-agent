# Architecture Decisions

A running log of the *why* behind non-trivial design choices in this project. The README
covers setup and how to use the app; this file covers why it's built the way it is, so a
future session (or a future you) doesn't have to reconstruct the reasoning from `git log`.

Update this when a change is genuinely architectural — a new pattern, a changed core design
choice, a new external dependency's quirks. Routine bug fixes, styling, and small feature
additions that fit an existing pattern don't need an entry.

## Storage: SQLite, not flat files or a heavier DB

Considered flat JSON files (simpler, easier to inspect by hand) and SQLite. Went with
SQLite because the app already needed structured querying (filter postings by company,
look up the latest match run) and SQLAlchemy's ORM makes schema evolution low-friction —
new columns get added via `ALTER TABLE` in place rather than requiring a full data
migration tool. For a single-user personal app this is one of the heavier possible choices,
but it avoids hand-rolling query/filter logic that a flat-file approach would need anyway.

## Matching: direct LLM comparison, no embeddings/vector DB

Per-company job counts are small enough (dozens to low hundreds) to fit structured
summaries of every candidate posting directly in one Claude prompt alongside the profile.
Skipping an embeddings step avoids an extra dependency and a second point of failure, and
produces better rationale quality — an embedding pre-filter can silently exclude a good
match due to phrasing/terminology differences that a full-context LLM comparison wouldn't
miss. Revisit only if a single company's open-role count grows into the many thousands.

## Job sourcing: a `JobSource` interface, bespoke vs. generic implementations

Oracle got a bespoke `JobSource` (`oracle.py`) because their careers site runs on a custom
internal Recruiting Cloud API discovered by inspecting their site's own network requests —
not something any other company shares. Later, Greenhouse and Lever were added as **generic**
sources (`greenhouse.py`, `lever.py`): both platforms host many different companies' job
boards behind the same public API shape, so one implementation each covers every company on
that platform, with the company name as the only parameter. The registry
(`sources/registry.py`) auto-detects which platform a typed company name belongs to by
probing each API in turn, falling back to a clear error suggesting the paste-URL flow if
none match. Amazon (real public JSON API) and Google (server-rendered, scrapeable HTML) were
investigated and confirmed feasible as future bespoke sources, but deliberately not built —
scoped out to keep that pass to Greenhouse/Lever only.

## Location and title filtering: hard code-level filters, not prompt instructions

Originally, seniority and location constraints were just instructions in the matching
prompt ("prefer California roles", "avoid Principal-level titles"). This repeatedly failed
in practice — real runs surfaced Nashville/India postings despite location guidance, and
Principal-level roles despite seniority guidance (confirmed: 47 of 119 cached Oracle
postings contained "Principal", and they kept appearing in top results for a candidate who
explicitly didn't want that level). The fix in both cases was the same: move the constraint
out of the prompt and into a plain-code filter (`location_filter.py`, `title_filter.py`)
applied *before* the ranking prompt is even built, so excluded postings are never shown to
the LLM at all — a hard guarantee instead of a suggestion the model might not follow.

### Location filter details

- `us_only` / `preferred_states` exclude postings that clearly name a non-preferred
  location, but an *ambiguous* one (bare "United States", no specific state) is kept rather
  than excluded, since we can't tell whether it actually requires relocation.
- Multi-location postings (a real Oracle behavior — e.g. requisition 334575 lists both
  Seattle, WA and Santa Clara, CA) are matched against *every* location listed, not just the
  first — an earlier version only checked the first state found and could wrongly exclude a
  posting whose primary location wasn't preferred but whose secondary location was.
- Remote postings (any location string containing "remote", in any format — bare "Remote",
  "US Remote", "Remote - US") are always included regardless of `us_only` or
  `preferred_states`, since remote roles are typically open regardless of specific physical
  location and a bare "Remote" string has no country/state info for the filter to check
  against anyway.

## Oracle URL handling: real API over HTML scraping, everywhere possible

Oracle's careers site (and the underlying "Candidate Experience" app people link to
directly, e.g. from LinkedIn) is a JavaScript-rendered SPA — a plain HTTP fetch returns an
empty shell, not the job content. Rather than treat this as a dead end for the paste-URL
flow, `url_parser.py` detects Oracle job URLs (either the public `careers.oracle.com`
wrapper or the underlying `eeho.fa.us2.oraclecloud.com` app URL) via the job ID embedded in
the URL, and routes them through `OracleJobSource.fetch_posting_by_id()` — the same real API
used for search — instead of the generic fetch-HTML-and-ask-Claude path. This is both more
reliable than scraping and cheaper (no LLM call needed for Oracle links specifically).

## Frontend: Next.js App Router, dark-first with a manual toggle

Next.js was chosen over plain React+Vite mainly for file-based routing matching the app's
natural page structure (profile/jobs/match), not for any SSR-specific need. Theming
initially deferred entirely to `prefers-color-scheme`, which turned out to be the wrong
default for a user who explicitly wanted a dark UI but has a system-level light preference —
replaced with an explicit `[data-theme]` toggle (persisted in `localStorage`, applied via a
blocking pre-hydration script to avoid a flash of the wrong theme) that takes precedence
over system preference when set.

## Known limitations (by design, not oversight)

- Only Oracle, Greenhouse, and Lever companies are searchable; other ATS platforms
  (Workday, etc.) have no stable public API shape across tenants and aren't supported.
- Bulk search results only carry a job's *primary* location — Oracle's secondary-location
  data is only available via a per-job detail fetch, which isn't done for every search
  result (100+ per search) for cost reasons. Only postings added via paste-URL get full
  multi-location data.
- No deployment/CD yet — the app runs locally only. CI (GitHub Actions) validates tests and
  build on every push, but nothing is hosted anywhere.
