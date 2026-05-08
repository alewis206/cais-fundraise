# cais-prospects

Investor prospecting pipeline for the CAIS raise. CLI in, Google Sheet out.

## What it does

1. Ingests prospects from CSVs and external sources (Crunchbase, OpenVC, Sales Nav exports, etc.).
2. Dedupes inline on canonical name + organization.
3. Classifies each prospect against the CAIS investor rubric using Claude.
4. Enriches with email (Apollo/Hunter) and recent activity (Twitter/Crunchbase).
5. Matches every prospect against CAIS's network for warm intro paths.
6. Syncs everything to a Google Sheet that humans drive outreach from.

The Google Sheet is the UI. There is no web app. There is no automated outreach.

## Status

Phase 1 — Foundation. Manual CSV ingest, stub classifier, write-only Google Sheet sync. See `docs/05-build-phases.md` for the roadmap.

## Quickstart

```bash
# 1. install
pip install -e ".[dev]"

# 2. configure
cp env.example .env
# fill in ANTHROPIC_API_KEY, GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON_PATH

# 3. drop a seed CSV at data/seeds/initial.csv
#    (see data/seeds/example.csv for column shape)
cp data/seeds/example.csv data/seeds/initial.csv  # or write your own

# 4. run the pipeline
cais-prospects ingest manual_csv
cais-prospects classify
cais-prospects sync-sheet
cais-prospects report
```

> **Heads up:** `data/seeds/` and `data/network/` are gitignored. Anything you drop there
> stays on your machine — only `README.md` and `example.csv` are tracked. This is by design:
> the seed list and warm-network CSVs contain personal data on outreach targets and CAIS
> contacts. Per `CLAUDE.md`, LinkedIn data must arrive only via manual Sales Nav exports.

## Layout

```
config/                 source priorities and the investor rubric
data/seeds/             input CSVs — gitignored except README.md and example.csv
data/network/           CAIS warm-network CSVs — gitignored except README.md
docs/                   spec — read these in order, 01 through 07
prompts/                classifier prompt template (Phase 2+)
src/                    code
tests/                  tests
```

## Docs

| Doc | What |
|---|---|
| `docs/01-investor-profile.md` | Five-dimension rubric. Source of truth for tier assignment. |
| `docs/02-target-categories.md` | Eight investor buckets and per-bucket source strategy. |
| `docs/03-architecture.md` | Pipeline shape and component contracts. |
| `docs/04-data-model.md` | SQLite schema, Pydantic models, dedupe rules. |
| `docs/05-build-phases.md` | Phase-by-phase task list. |
| `docs/06-inputs-needed.md` | What humans must provide and when. |
| `docs/07-risks-out-of-scope.md` | What this project will not become. |
