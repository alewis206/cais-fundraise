# 04 — Data Model

## SQLite schema

All tables live in `data/prospects.db`. Migrations managed via simple SQL files in `src/migrations/`.

```sql
CREATE TABLE prospects (
    id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL,        -- lowercased, accent-stripped
    display_name TEXT NOT NULL,          -- presentational version
    primary_org TEXT,
    title TEXT,
    email TEXT,
    email_confidence REAL,               -- 0.0 - 1.0 from enrichment provider
    linkedin_url TEXT UNIQUE,
    twitter_handle TEXT,
    crunchbase_url TEXT UNIQUE,
    bio TEXT,
    candidate_categories TEXT,           -- JSON array
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    UNIQUE(canonical_name, primary_org)
);

CREATE INDEX idx_prospects_email ON prospects(email);
CREATE INDEX idx_prospects_canonical ON prospects(canonical_name);

CREATE TABLE source_records (
    id INTEGER PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    source TEXT NOT NULL,                -- adapter name
    source_context_json TEXT,            -- raw payload from source
    fetched_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_source_records_prospect ON source_records(prospect_id);

CREATE TABLE source_cache (
    cache_key TEXT PRIMARY KEY,          -- adapter:hash(params)
    response_json TEXT,
    fetched_at TIMESTAMP NOT NULL
);

CREATE TABLE enrichment_records (
    id INTEGER PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,              -- 'apollo', 'hunter', 'twitter', 'crunchbase'
    payload_json TEXT,
    fetched_at TIMESTAMP NOT NULL,
    UNIQUE(prospect_id, provider)
);

CREATE TABLE classifications (
    id INTEGER PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    services_thesis_fit INTEGER NOT NULL CHECK (services_thesis_fit BETWEEN 1 AND 5),
    ai_literacy INTEGER NOT NULL CHECK (ai_literacy BETWEEN 1 AND 5),
    operator_depth INTEGER NOT NULL CHECK (operator_depth BETWEEN 1 AND 5),
    check_size_fit INTEGER NOT NULL CHECK (check_size_fit BETWEEN 1 AND 5),
    warm_intro_accessibility INTEGER NOT NULL CHECK (warm_intro_accessibility BETWEEN 1 AND 5),
    composite_score INTEGER NOT NULL,
    tier TEXT NOT NULL CHECK (tier IN ('1', '2', '3', 'drop')),
    rationale TEXT,
    flags_json TEXT,                     -- JSON array
    confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
    model_used TEXT NOT NULL,
    prompt_version TEXT NOT NULL,        -- hash of prompts/classifier.md
    classified_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_classifications_prospect ON classifications(prospect_id);
CREATE INDEX idx_classifications_tier ON classifications(tier);

-- Latest classification per prospect — view for convenience.
CREATE VIEW latest_classifications AS
SELECT c.*
FROM classifications c
INNER JOIN (
    SELECT prospect_id, MAX(classified_at) AS latest
    FROM classifications
    GROUP BY prospect_id
) m ON c.prospect_id = m.prospect_id AND c.classified_at = m.latest;

CREATE TABLE warm_paths (
    id INTEGER PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    path_type TEXT NOT NULL,             -- 'client', 'linkedin_1st', 'youtube_sub', 'advisor', 'mutual_2nd'
    path_detail TEXT NOT NULL,           -- e.g., "client:Brendan Patrick (4AM Media)"
    confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
    matched_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_warm_paths_prospect ON warm_paths(prospect_id);

CREATE TABLE outreach_status (
    prospect_id INTEGER PRIMARY KEY REFERENCES prospects(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'not_contacted',
    last_touch_at TIMESTAMP,
    next_touch_at TIMESTAMP,
    notes TEXT,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE api_call_log (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    provider TEXT NOT NULL,              -- 'crunchbase', 'apollo', 'anthropic', etc.
    endpoint TEXT,
    status_code INTEGER,
    latency_ms INTEGER,
    cost_usd REAL,
    error TEXT
);
```

## Pydantic models

Lives in `src/models.py`.

```python
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

class RawProspect(BaseModel):
    """Output of a source adapter, before enrichment or persistence."""
    full_name: str
    primary_org: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    crunchbase_url: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    source: str
    source_context: dict = Field(default_factory=dict)
    candidate_categories: list[str] = Field(default_factory=list)


class Prospect(BaseModel):
    """Persisted prospect. Mirrors the prospects table."""
    id: int
    canonical_name: str
    display_name: str
    primary_org: Optional[str]
    title: Optional[str]
    email: Optional[str]
    email_confidence: Optional[float]
    linkedin_url: Optional[str]
    twitter_handle: Optional[str]
    crunchbase_url: Optional[str]
    bio: Optional[str]
    candidate_categories: list[str]
    created_at: datetime
    updated_at: datetime


class ClassifierOutput(BaseModel):
    services_thesis_fit: int = Field(ge=1, le=5)
    ai_literacy: int = Field(ge=1, le=5)
    operator_depth: int = Field(ge=1, le=5)
    check_size_fit: int = Field(ge=1, le=5)
    warm_intro_accessibility: int = Field(ge=1, le=5)
    composite_score: int = Field(ge=5, le=25)
    tier: Literal["1", "2", "3", "drop"]
    rationale: str
    flags: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]


class WarmPath(BaseModel):
    path_type: Literal["client", "linkedin_1st", "youtube_sub", "advisor", "mutual_2nd"]
    path_detail: str
    confidence: Literal["high", "medium", "low"]


class OutreachStatus(BaseModel):
    status: Literal[
        "not_contacted", "outreach_sent", "replied",
        "meeting_scheduled", "pitched", "due_diligence",
        "committed", "passed", "do_not_contact"
    ] = "not_contacted"
    last_touch_at: Optional[datetime] = None
    next_touch_at: Optional[datetime] = None
    notes: Optional[str] = None
```

## Dedupe rules

**Canonical name normalization:**
1. Lowercase.
2. Strip accents (NFKD normalization).
3. Strip honorifics (Mr, Ms, Dr, Prof, etc.).
4. Strip suffixes (Jr, Sr, II, III, PhD, etc.).
5. Collapse internal whitespace.

**Dedupe key:** `(canonical_name, primary_org_lowered)`.

**Collision behavior:**
1. Find existing prospect by dedupe key.
2. If found, attach a new `source_records` row (don't create new prospect).
3. Merge fields: take non-null from new record only if existing field is null. Never overwrite.
4. Update `updated_at`.

**Edge cases:**
- Same name, no org on either side → match on `linkedin_url` or `email` if available, else create new prospect.
- Same name, different orgs → likely different people; create separate prospects unless `linkedin_url` matches.
- Two `linkedin_url` rows match but names differ slightly → merge under the canonical name with the most occurrences.

Dedupe runs inline during ingestion. There is no separate dedupe pass.
