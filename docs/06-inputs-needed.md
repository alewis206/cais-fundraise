# 06 — Inputs Needed

What Devin and Andrew must provide. Organized by phase.

## Before Phase 1 ends

### Seed list of 50–100 names (REQUIRED)
A CSV at `data/seeds/initial.csv` with these columns:

| Column | Required | Notes |
|---|---|---|
| `name` | yes | Full name. |
| `org` | recommended | Current company / fund. |
| `role` | recommended | Title. |
| `linkedin_url` | recommended | Direct URL. |
| `twitter_handle` | optional | With or without `@`. |
| `email` | optional | If you already have it. |
| `source_note` | optional | How you know them or why you flagged them. |
| `categories` | optional | Comma-separated, e.g. `rpa_alumni,operator_angel`. |

Aim for: people you already think are great fits. They become the gold-standard set the system learns from for lookalike expansion.

### Client list (REQUIRED)
At `data/network/clients.csv`:

| Column | Required | Notes |
|---|---|---|
| `org` | yes | Client company name. |
| `primary_contact_name` | yes | Decision-maker / primary relationship. |
| `primary_contact_email` | yes | |
| `deal_size_usd` | optional | For prioritization. |
| `status` | yes | `active`, `past`, `lost`, `prospect`. |
| `notes` | optional | |

Used by the warm-path matcher.

### LinkedIn 1st-degree exports (REQUIRED for warm-paths)
Run Sales Navigator → export connections → drop CSVs into `data/network/`:

- `linkedin_devin.csv`
- `linkedin_andrew.csv`
- `linkedin_nik.csv` (optional)
- `linkedin_allan.csv` (optional)

LinkedIn's standard CSV export columns are fine; the adapter will map them.

### API keys (REQUIRED)
Fill `.env`:

```
ANTHROPIC_API_KEY=          # required for classifier
GOOGLE_SERVICE_ACCOUNT_JSON_PATH=./secrets/google-sa.json
GOOGLE_SHEET_ID=            # the sheet you've created
```

Create the Google service account, share the target sheet with the service account email.

## Before Phase 2 ends

### Final rubric wording
Review `config/investor_profile.yaml`. Adjust scoring criteria if anything is off. The classifier prompt depends on this.

### Email enrichment provider keys (REQUIRED for emails)
At least one of:

```
APOLLO_API_KEY=
HUNTER_API_KEY=
```

Apollo's free tier allows ~50 lookups/month. Hunter's allows ~25/month. For 500+ prospects you'll likely need a paid tier; $49/mo on Apollo is sufficient.

## Before Phase 3 ends

### Crunchbase API access (HIGH VALUE)
```
CRUNCHBASE_API_KEY=
```

This is the single most leveraged paid tool. Without it, the RPA / services-exit categories are much harder to populate. ~$49–99/mo.

### OpenVC export (FREE)
Download the OpenVC investor CSV manually and drop at `data/seeds/openvc.csv`. Refresh quarterly.

### Sales Navigator manual exports
For each target search, run the search in Sales Navigator, export results to CSV, drop into `data/seeds/linkedin/`. Naming convention: `<category>_<date>.csv`, e.g.:
- `data/seeds/linkedin/rpa_alumni_2026-05.csv`
- `data/seeds/linkedin/services_exits_2026-05.csv`

The adapter ingests everything in that directory.

### Twitter / X API access (OPTIONAL)
```
TWITTER_BEARER_TOKEN=
```

Useful for bio enrichment and "angel investor" search. Skip gracefully if not available.

### Audience-founder seed list (RECOMMENDED)
Devin already knows many of these — list at `data/seeds/audience_founders.csv`. Same columns as `initial.csv`.

### Curated VC and CVC lists (RECOMMENDED)
- `data/seeds/services_friendly_vcs.csv` — list from `docs/02`.
- `data/seeds/si_cvcs.csv` — list from `docs/02`.

## Before Phase 4 ends

### YouTube subscriber export (OPTIONAL)
If technically feasible. YouTube API restricts subscriber list access — you may need YouTube Studio export, which has limited fields.

If available: `data/network/youtube_subscribers.csv`.

### Advisor list (RECOMMENDED)
At `data/network/advisors.csv`:

| Column | Notes |
|---|---|
| `name` | |
| `org` | |
| `email` | |
| `relationship` | how they advise CAIS |
| `network_strength` | `high`, `medium`, `low` — how willing/able they are to make introductions |

### Tier 1 outreach intent (NICE TO HAVE)
A short note describing what an "ideal first email from Devin" would emphasize for Tier 1 prospects. Helps the classifier prompt understand what makes a Tier 1.

## Summary checklist

| Item | Phase | Required? |
|---|---|---|
| `data/seeds/initial.csv` (50–100 names) | 1 | yes |
| `data/network/clients.csv` | 1 | yes |
| `data/network/linkedin_devin.csv` | 1 | yes |
| `data/network/linkedin_andrew.csv` | 1 | yes |
| `ANTHROPIC_API_KEY` | 1 | yes |
| Google Sheet + service account | 1 | yes |
| `APOLLO_API_KEY` or `HUNTER_API_KEY` | 2 | yes |
| Rubric review | 2 | yes |
| `CRUNCHBASE_API_KEY` | 3 | high value |
| OpenVC export CSV | 3 | recommended |
| Sales Nav category exports | 3 | yes (drives Phase 3 yield) |
| `data/seeds/audience_founders.csv` | 3 | recommended |
| `data/seeds/services_friendly_vcs.csv` | 3 | recommended |
| `data/seeds/si_cvcs.csv` | 3 | recommended |
| `TWITTER_BEARER_TOKEN` | 3 | optional |
| `data/network/youtube_subscribers.csv` | 4 | optional |
| `data/network/advisors.csv` | 4 | recommended |
