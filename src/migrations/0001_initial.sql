CREATE TABLE IF NOT EXISTS prospects (
    id INTEGER PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    display_name TEXT NOT NULL,
    primary_org TEXT,
    title TEXT,
    email TEXT,
    email_confidence REAL,
    linkedin_url TEXT UNIQUE,
    twitter_handle TEXT,
    crunchbase_url TEXT UNIQUE,
    bio TEXT,
    candidate_categories TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    UNIQUE(canonical_name, primary_org)
);

CREATE INDEX IF NOT EXISTS idx_prospects_email ON prospects(email);
CREATE INDEX IF NOT EXISTS idx_prospects_canonical ON prospects(canonical_name);

CREATE TABLE IF NOT EXISTS source_records (
    id INTEGER PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    source TEXT NOT NULL,
    source_context_json TEXT,
    fetched_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_records_prospect ON source_records(prospect_id);

CREATE TABLE IF NOT EXISTS source_cache (
    cache_key TEXT PRIMARY KEY,
    response_json TEXT,
    fetched_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS enrichment_records (
    id INTEGER PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    provider TEXT NOT NULL,
    payload_json TEXT,
    fetched_at TIMESTAMP NOT NULL,
    UNIQUE(prospect_id, provider)
);

CREATE TABLE IF NOT EXISTS classifications (
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
    flags_json TEXT,
    confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
    model_used TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    classified_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_classifications_prospect ON classifications(prospect_id);
CREATE INDEX IF NOT EXISTS idx_classifications_tier ON classifications(tier);

CREATE VIEW IF NOT EXISTS latest_classifications AS
SELECT c.*
FROM classifications c
INNER JOIN (
    SELECT prospect_id, MAX(classified_at) AS latest
    FROM classifications
    GROUP BY prospect_id
) m ON c.prospect_id = m.prospect_id AND c.classified_at = m.latest;

CREATE TABLE IF NOT EXISTS warm_paths (
    id INTEGER PRIMARY KEY,
    prospect_id INTEGER NOT NULL REFERENCES prospects(id) ON DELETE CASCADE,
    path_type TEXT NOT NULL,
    path_detail TEXT NOT NULL,
    confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
    matched_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_warm_paths_prospect ON warm_paths(prospect_id);

CREATE TABLE IF NOT EXISTS outreach_status (
    prospect_id INTEGER PRIMARY KEY REFERENCES prospects(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'not_contacted',
    last_touch_at TIMESTAMP,
    next_touch_at TIMESTAMP,
    notes TEXT,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS api_call_log (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    provider TEXT NOT NULL,
    endpoint TEXT,
    status_code INTEGER,
    latency_ms INTEGER,
    cost_usd REAL,
    error TEXT
);
