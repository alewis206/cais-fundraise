# 03 — Architecture

## Pipeline

```
┌─────────────────┐
│ Source Adapters │  manual_csv, crunchbase, openvc, linkedin_csv,
└────────┬────────┘  twitter_bio, podcast_guests
         ↓
┌─────────────────┐
│ Raw Prospect DB │  SQLite — see docs/04-data-model.md
└────────┬────────┘
         ↓
┌─────────────────┐
│   Enrichment    │  apollo, hunter (email); twitter (recent activity);
└────────┬────────┘  crunchbase (co-investors, recent investments)
         ↓
┌─────────────────┐
│   Classifier    │  Anthropic-backed. Scores 5 dimensions, assigns tier.
└────────┬────────┘
         ↓
┌─────────────────┐
│ Warm-Path Match │  Cross-ref against client list, LinkedIn 1st-degree,
└────────┬────────┘  YouTube subs, advisor network
         ↓
┌─────────────────┐
│   CRM Output    │  Google Sheet (bidirectional sync)
└─────────────────┘
```

## Component contracts

### Source adapter

Lives in `src/sources/<name>.py`. Implements:

```python
from typing import Iterator, Protocol
from src.models import RawProspect

class SourceAdapter(Protocol):
    name: str

    def fetch(self, **kwargs) -> Iterator[RawProspect]:
        """Yield RawProspect records. Idempotent: running twice does not duplicate."""
        ...
```

Each adapter:
- Reads its own config from `config/sources.yaml`.
- Caches raw responses in `source_cache` table for 30 days.
- Tags every prospect with `candidate_categories: list[str]` per `docs/02`.
- Logs every external API call: `source`, `params` (redacted), `status`, `latency_ms`, `cost_usd` if known.

### Enrichment

Lives in `src/enrichment/<provider>.py`. For each Prospect, attaches:
- **Email** — Apollo or Hunter (fallback chain). Confidence score required.
- **Recent activity** — last 5 tweets if handle known.
- **Recent investments** — Crunchbase, last 12 months.
- **Co-investor graph** — for use in lookalike expansion.

Re-fetch only when record is older than `ENRICHMENT_CACHE_DAYS` (default 30) or `--force-refresh` is passed.

### Classifier

Lives in `src/classifier.py`. Single function:

```python
def classify(prospect: Prospect) -> ClassifierOutput:
    """Score the prospect 1-5 on 5 dimensions and assign tier."""
```

- Default model: `claude-sonnet-4-6` (env: `CLASSIFIER_DEFAULT_MODEL`).
- Tier 1 candidates re-classified with `claude-opus-4-7` for higher confidence (env: `CLASSIFIER_TIER1_MODEL`).
- Prompt template: `prompts/classifier.md`. Must be loaded fresh each run.
- Output: structured JSON. Validate with Pydantic before persisting.
- Persist: rubric scores, composite, tier, rationale, flags, confidence, model used, prompt version (file hash).

### Warm-path matcher

Lives in `src/warm_paths.py`. Single function:

```python
def match_warm_paths(prospect: Prospect) -> list[WarmPath]:
    """Return all warm intro paths to this prospect from CAIS network files."""
```

Match logic in priority order:
1. Exact email match against any network file.
2. Exact name + company match.
3. Fuzzy name match (Levenshtein distance ≤ 2) + company match.
4. Email domain match (e.g., the prospect's email domain matches a known company in network).

Each match emits a `WarmPath` record with `path_type`, `path_detail`, `confidence`.

### Google Sheet sync

Lives in `src/output/google_sheet.py`. Bidirectional.

**System-owned columns (system writes, user reads):**

| Column | Source |
|---|---|
| Prospect ID | DB primary key |
| Name | DB |
| Title | DB |
| Org | DB |
| Email | Enrichment |
| Email Confidence | Enrichment |
| LinkedIn | DB |
| Twitter | DB |
| Categories | Adapter tags (comma-separated) |
| Tier | Classifier |
| Composite | Classifier |
| Services Fit | Classifier |
| AI Literacy | Classifier |
| Operator Depth | Classifier |
| Check Size Fit | Classifier |
| Warm Access | Classifier |
| Rationale | Classifier |
| Warm Paths | Matcher (semicolon-separated) |
| Source | Adapter name |
| Date Added | DB |
| Date Updated | DB |

**User-owned columns (user writes, system reads back):**

| Column | Notes |
|---|---|
| Status | Enum: `not_contacted`, `outreach_sent`, `replied`, `meeting_scheduled`, `pitched`, `due_diligence`, `committed`, `passed`, `do_not_contact`. |
| Last Touch | Date |
| Next Touch | Date |
| Notes | Free text |

**Sync algorithm:**
1. Read the entire sheet.
2. For each row, look up by Prospect ID.
3. Pull user-owned columns into the DB (overwrite local copy).
4. Push system-owned columns from DB to sheet (overwrite sheet copy).
5. Add new rows for any DB prospects not yet in the sheet.
6. Never delete rows from the sheet automatically — flag stale ones in a `STATUS=do_not_contact` column instead.

The sheet is the human UI. Treat it with care.

## Reporting

`cais-prospects report` prints:
- Total prospects, by tier.
- Prospects by source.
- Prospects by status.
- Outreach funnel: sent → replied → meeting → pitched → committed.
- Cost spent on classification this month.
- Sources with <5% Tier 1/2 yield (kill candidates).
