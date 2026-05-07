# CLAUDE.md — agent guidance

This is the `cais-prospects` codebase. An agent (you) is helping build and maintain it.

## Read these in order

1. `docs/01-investor-profile.md` — the rubric
2. `docs/02-target-categories.md` — who we're targeting
3. `docs/03-architecture.md` — pipeline shape
4. `docs/04-data-model.md` — schema and Pydantic models
5. `docs/05-build-phases.md` — current phase and acceptance criteria
6. `docs/06-inputs-needed.md` — what the user owes us
7. `docs/07-risks-out-of-scope.md` — what we are NOT building

## Hard rules

- **Never automate anything against linkedin.com.** The only LinkedIn data path is manual Sales Navigator CSV exports landing in `data/seeds/linkedin/` or `data/network/`. Browser automation, headless scraping, and unofficial APIs are all out. Devin's and Andrew's accounts are critical for warm-intro mapping; a ban is catastrophic.
- **Default classifier model is Sonnet.** Only use Opus for the Tier 1 re-classification pass or when explicitly requested.
- **Cost ceiling: prompt before any run that projects >$50.** This applies to `classify --all`, lookalike expansion, and bulk enrichment.
- **No automated outreach.** Email composition and sending stay with humans. We surface data in a sheet; humans send mail.
- **No web UI.** The Google Sheet is the UI. Resist building a dashboard.
- **Single tenant.** Don't add auth, role-based access, or multi-user features.
- **Bidirectional sheet sync respects user-owned columns.** System never overwrites `Status`, `Last Touch`, `Next Touch`, `Notes`. See `docs/03-architecture.md` for the column ownership table.
- **Every classification persists `prompt_version` (file hash of `prompts/classifier.md`).** This lets us re-classify only stale records when the rubric changes.

## Conventions

- Python 3.11+. Type-annotate everything that crosses a module boundary.
- Pydantic for all validated data. SQLite for persistence. Typer for CLI. structlog for logs.
- `src/` is the package root. Tests mirror `src/` layout under `tests/`.
- Commit messages: imperative mood, ≤72-char subject, body explains why if non-obvious.
- Don't pre-emptively build for phases beyond the current one. Phase 1 must work end-to-end before Phase 2 starts.

## Where to add things

- New data source → `src/sources/<name>.py`, register in `config/sources.yaml`.
- New enrichment provider → `src/enrichment/<provider>.py`.
- New CLI command → add to `src/cli.py`.
- Schema change → new file in `src/migrations/`, never edit a committed migration.
- New test → mirror the path under `tests/`.

## When in doubt

Ask the user. They can answer in 30 seconds. Debugging a wrong assumption takes hours.
