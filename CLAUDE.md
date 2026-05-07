# 05 — Build Phases

Four phases. Each is shippable. Check tasks off as you complete them.

---

## Phase 1 — Foundation

**Goal:** end-to-end pipeline runs with a manual CSV in, a stub classifier, and a Google Sheet out.

### Tasks

- [ ] Initialize repo: `pyproject.toml` with deps (`httpx`, `pydantic`, `pydantic-settings`, `typer`, `gspread`, `anthropic`, `structlog`, `pytest`).
- [ ] Create `src/config.py` — `pydantic-settings` reading `.env`.
- [ ] Create `src/db.py` — SQLite connection + migration runner. Apply schema from `docs/04-data-model.md`.
- [ ] Create `src/models.py` — Pydantic models per `docs/04-data-model.md`.
- [ ] Implement canonical-name normalization in `src/utils/names.py`.
- [ ] Implement dedupe-on-insert helper in `src/db.py`.
- [ ] Implement `src/sources/base.py` — `SourceAdapter` Protocol.
- [ ] Implement `src/sources/manual_csv.py` — reads CSVs from `data/seeds/`.
- [ ] Implement stub `src/classifier.py` — returns fixed `ClassifierOutput` with composite=15, tier="2". This is replaced in Phase 2; the goal here is to wire the pipeline.
- [ ] Implement `src/output/google_sheet.py` — write-only sync (system-owned columns from `docs/03`).
- [ ] Implement `src/cli.py` with commands: `ingest`, `classify`, `sync-sheet`, `report`.
- [ ] Wire structlog with sensible defaults.
- [ ] Tests: `tests/sources/test_manual_csv.py`, `tests/test_dedupe.py`, `tests/test_models.py`.
- [ ] Write `data/seeds/README.md` explaining expected CSV column names.

### Acceptance

- Drop a 100-row CSV with columns `name, org, role, linkedin_url, source_note` into `data/seeds/initial.csv`.
- Run `cais-prospects ingest manual_csv && cais-prospects classify && cais-prospects sync-sheet`.
- Google Sheet shows 100 rows, all classified at tier 2 (stub), system-owned columns populated.
- Re-running ingestion does not duplicate rows.

---

## Phase 2 — Real classifier and enrichment

**Goal:** every prospect is scored by Claude with rationale, has email attached, and the sheet sync is bidirectional.

### Tasks

- [ ] Write `prompts/classifier.md` — full classifier prompt template that loads `config/investor_profile.yaml` content at runtime. Versioned via file-content hash.
- [ ] Replace `src/classifier.py` stub with real implementation:
  - Load prompt template, substitute prospect data.
  - Call Anthropic API with structured JSON output.
  - Validate response against `ClassifierOutput`.
  - Persist with `model_used` and `prompt_version`.
  - Log cost per call to `api_call_log`.
- [ ] Add Tier 1 re-classification with `claude-opus-4-7` for any prospect whose Sonnet classification produced tier="1" with confidence != "high".
- [ ] Implement `src/enrichment/apollo.py` — given a prospect, fetch email + confidence. Cache for 30 days.
- [ ] Implement `src/enrichment/hunter.py` — fallback chain when Apollo returns no email.
- [ ] Implement `src/enrichment/twitter.py` — fetch bio + last 5 tweets if handle known. Skip gracefully if no Twitter API access.
- [ ] CLI command: `cais-prospects enrich [--prospect-id N] [--force-refresh]`.
- [ ] Make sheet sync bidirectional. User-owned columns flow back into `outreach_status` table.
- [ ] Add cost ceiling check: if running `classify --all` would exceed $50 of projected spend, prompt for confirmation.
- [ ] Tests: `tests/test_classifier.py` with mocked Anthropic; `tests/test_enrichment_apollo.py` with mocked HTTP.

### Acceptance

- The 100 seeds from Phase 1 now have real scores, tier assignments, rationale, and emails (where Apollo/Hunter found them).
- Edit `Status` and `Notes` in the Google Sheet, run `sync-sheet`, confirm the DB picks up the changes and a re-sync doesn't clobber them.
- Total Anthropic spend for 100 prospects classified is under $5.

---

## Phase 3 — External sources

**Goal:** the prospect list grows from seeds-only to 500+ via real source adapters.

### Tasks

- [ ] Implement `src/sources/crunchbase.py`:
  - Search by org (e.g., "former founder of UiPath").
  - Search by category (current angel investors).
  - Cache responses.
- [ ] Implement `src/sources/openvc.py`:
  - Ingest OpenVC investor CSV export. (Free; periodic manual refresh.)
- [ ] Implement `src/sources/linkedin_csv.py`:
  - Ingest CSVs from `data/seeds/linkedin/` (manual Sales Nav exports).
  - Map LinkedIn export columns to `RawProspect`.
  - **Reminder: this adapter NEVER hits LinkedIn directly. CSV ingest only.**
- [ ] Implement `src/sources/podcast_guests.py`:
  - For a configured list of podcasts (in `config/sources.yaml`), scrape guest lists.
  - Yield guest names + episode context.
- [ ] Implement `src/sources/twitter_bio.py`:
  - Run targeted bio searches (e.g., "ex-UiPath" + "angel"). Yield candidate names.
  - Skip gracefully if no Twitter API access.
- [ ] Implement co-investor lookalike expansion in `src/lookalike.py`:
  - Given Tier 1 prospects, query Crunchbase for frequent co-investors.
  - Add as candidates with tag `lookalike:<seed_id>`.
- [ ] Update CLI: `cais-prospects ingest --all` runs adapters per `config/sources.yaml` priority.
- [ ] Add per-source yield reporting: `cais-prospects report` shows Tier 1/2 yield per source.

### Acceptance

- Total prospects in DB: 500+.
- Dedupe is clean: no obvious duplicates in the sheet.
- Lookalike expansion produces ≥ 20 new candidates from Tier 1 seeds.
- Per-source report shows yield variance — at least one source has clearly higher Tier 1/2 yield than others.

---

## Phase 4 — Warm paths and polish

**Goal:** every prospect that has a warm path through CAIS's network is flagged. Reporting is useful. Future agents can pick this up.

### Tasks

- [ ] Implement `src/warm_paths.py`:
  - Load network files from `data/network/`.
  - For each prospect, run match logic per `docs/03` (email exact → name+company exact → fuzzy name+company → email domain).
  - Persist matches with confidence.
- [ ] CLI: `cais-prospects match-warm-paths`.
- [ ] Update sheet sync to include `Warm Paths` column.
- [ ] Implement `src/reporting.py`:
  - Total by tier, by source, by status.
  - Outreach funnel (sent → replied → meeting → pitched → committed).
  - Spend this month.
  - Sources to consider killing.
- [ ] Write `docs/RUNBOOK.md` — how to run a refresh, how to add a new source, how to update the rubric.
- [ ] Update `CLAUDE.md` with anything learned during the build.
- [ ] Final dedupe audit: spot-check 50 random rows in the sheet.

### Acceptance

- At least 30% of prospects in the DB have at least one warm path identified.
- All Tier 1 prospects have either a warm path or a `cold_only_acceptable` flag explicitly set.
- `cais-prospects report` produces a useful one-screen summary.
- A new agent reading `CLAUDE.md` + `SPEC.md` + `docs/RUNBOOK.md` could refresh the list end-to-end.

---

## Notes for the agent building this

- Don't try to build phases in parallel. Phase 1 has to be solid before Phase 2 is useful.
- If you find yourself wanting to skip the stub classifier in Phase 1 and go straight to the real one — don't. The stub forces the pipeline shape to be correct before LLM costs accrue.
- If a source adapter is producing low-quality results, kill it. Don't add complexity to compensate.
- When in doubt, ask the user. The user can answer in 30 seconds; debugging a wrong assumption takes hours.
