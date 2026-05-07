# data/seeds/

Drop seed CSVs here. They are gitignored.

## Expected files

| File | Purpose | Required? |
|---|---|---|
| `initial.csv` | The 50–100 names you already think are great fits. | Phase 1, required |
| `audience_founders.csv` | Curated audience-monetization founders. | Phase 3, recommended |
| `services_friendly_vcs.csv` | The small VC list from `docs/02`. | Phase 3, recommended |
| `si_cvcs.csv` | Systems integrator CVCs. | Phase 3, recommended |
| `openvc.csv` | OpenVC investor CSV export. | Phase 3, recommended |
| `linkedin/*.csv` | Manual Sales Navigator exports. | Phase 3, drives yield |

## CSV column conventions

The `manual_csv` adapter accepts these column names (case-insensitive). Variations are mapped via `config/sources.yaml`.

| Logical field | Accepted column names |
|---|---|
| name | `name`, `Full Name`, `Name` |
| org | `org`, `Company`, `Organization` |
| role | `role`, `Title`, `Position` |
| linkedin_url | `linkedin_url`, `LinkedIn URL`, `LinkedIn` |
| twitter_handle | `twitter_handle`, `Twitter`, `X Handle` |
| email | `email`, `Email` |
| categories | `categories` (comma-separated) |
| source_note | `source_note`, `Notes` |

## LinkedIn export naming

Files in `data/seeds/linkedin/` should follow the naming convention:

```
<category>_<YYYY-MM>.csv
```

Examples:
- `rpa_alumni_2026-05.csv`
- `services_exits_2026-05.csv`
- `operator_angels_2026-05.csv`

The category becomes a tag on every prospect imported from that file.
