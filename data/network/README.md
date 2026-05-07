# data/network/

CAIS network files used by the warm-path matcher. Gitignored.

## Expected files

| File | Purpose | Required? |
|---|---|---|
| `clients.csv` | Past and current CAIS clients. | Phase 1, required |
| `linkedin_devin.csv` | Devin's LinkedIn 1st-degree (Sales Nav export). | Phase 1, required |
| `linkedin_andrew.csv` | Andrew's LinkedIn 1st-degree. | Phase 1, required |
| `linkedin_nik.csv` | Nik's connections. | Optional |
| `linkedin_allan.csv` | Allan's connections. | Optional |
| `youtube_subscribers.csv` | YouTube subscriber export. | Phase 4, optional |
| `advisors.csv` | Advisor list with network strength. | Phase 4, recommended |

## clients.csv columns

| Column | Required? |
|---|---|
| `org` | yes |
| `primary_contact_name` | yes |
| `primary_contact_email` | yes |
| `deal_size_usd` | optional |
| `status` | yes — `active`, `past`, `lost`, `prospect` |
| `notes` | optional |

## advisors.csv columns

| Column | Required? |
|---|---|
| `name` | yes |
| `org` | yes |
| `email` | yes |
| `relationship` | yes |
| `network_strength` | yes — `high`, `medium`, `low` |

## LinkedIn exports

Standard LinkedIn Sales Navigator CSV export columns are fine. The adapter maps them automatically.
