# 02 — Target Categories

Eight buckets of investors. Each has a defined acquisition strategy and an associated source adapter.

## Bucket priority

1. **CAIS internal warm network** — highest conversion. Manual seed only.
2. **Operator angels with services backgrounds** — high conversion, accessible.
3. **RPA / automation veterans** — high thesis alignment.
4. **Tech-enabled / AI-enabled services exits** — strong fit.
5. **Audience-monetization founders** — Devin's distribution moat resonates here.
6. **Foundation-model lab alumni with liquidity** — small slice but high signal.
7. **AI services-friendly VCs** — small universe; enumerate manually.
8. **Systems integrator CVCs** — strategic, slower cycle.

## Per-bucket spec

### 1. CAIS internal warm network
**Source:** `manual_csv` adapter ingesting:
- `data/network/clients.csv` — past and current CAIS clients.
- `data/network/youtube_subscribers.csv` — exported subscriber list (if technically feasible).
- `data/network/linkedin_devin.csv`, `linkedin_andrew.csv`, `linkedin_nik.csv`, `linkedin_allan.csv`.
- `data/network/advisors.csv` — known advisors and their networks.

Tagged `category: internal_warm` so the classifier weights warm-intro accessibility heavily.

### 2. Operator angels with services backgrounds
**Examples to surface:** ex-McKinsey/Bain/BCG operators turned investors, ex-Accenture partners, BPO operators (Genpact, WNS, EXL alumni at MD+ level), digital agency founders post-exit.

**Adapter:** `crunchbase` (search for people with "founder" + services-industry past employers, currently active as angels) + `linkedin_csv` manual exports + `openvc` operator-angel filter.

Tag: `operator_angel`.

### 3. RPA / automation veterans
**Examples to surface:** UiPath alumni (Daniel Dines, Param Kahlon, others post-IPO), Automation Anywhere alumni, Blue Prism alumni, Workato early team, Zapier early team, Tray.io alumni, Make.com alumni, Pega/Appian/ServiceNow early product/eng leads.

**Adapter:** `crunchbase` (organization → former employees → currently angel-investing), `linkedin_csv` (Sales Nav exports), `twitter_bio` (search for "ex-UiPath" + "angel" type bios).

Tag: `rpa_alumni`.

### 4. Tech-enabled / AI-enabled services exits
**Examples to surface:** Globant, EPAM, Endava, Thoughtworks, Pivotal Labs, Slalom, West Monroe, R/GA, Huge, AKQA, Big Spaceship, Work & Co, Palantir Forward Deployed alumni, Scale AI services-team alumni.

**Adapter:** Same as RPA — Crunchbase + LinkedIn manual + curated lists.

Tag: `services_exit`.

### 5. Audience-monetization founders
**Examples to surface:** Justin Welsh, Sahil Lavingia, Dru Riley, Codie Sanchez, Nathan Barry (ConvertKit), Cody Schneider, Greg Isenberg (LCA / Late Checkout), Andrew Wilkinson (Tiny), Jesse Pujji.

Plus creator-economy VCs: Slow Ventures, Audacious, Animal.

**Adapter:** Curated. Devin already knows many of these — list them in `data/seeds/audience_founders.csv`.

Tag: `audience_founder`.

### 6. Foundation-model lab alumni with liquidity
**Examples to surface:** Anthropic, OpenAI, Scale AI, Cohere, Mistral early employees who have publicly disclosed angel investments.

**Adapter:** `linkedin_csv` (Sales Nav: title contains "founding" + company in this list) + `twitter_bio` (cross-reference public angel announcements). Manual curation of high-confidence names.

Tag: `lab_alumni`.

### 7. AI services-friendly VCs
**Curated list (start here):** Active Capital (Austin), Operator Collective, South Park Commons, Mucker Capital, Bloomberg Beta, Tola Capital, Ensemble VC, Slow Ventures, Madrona (selectively), WndrCo.

**Adapter:** Manual entry in `data/seeds/services_friendly_vcs.csv`. Not large enough to scrape.

Tag: `services_vc`.

### 8. Systems integrator CVCs
**Curated list:** Accenture Ventures, Deloitte Ventures, EY Ventures, Cognizant, Capgemini Ventures, Booz Allen Ventures, Globant Ventures.

**Adapter:** Manual entry in `data/seeds/si_cvcs.csv`.

Tag: `si_cvc`.

## Lookalike expansion (cross-cutting)

After Phase 2, given the highest-confidence Tier 1 prospects, run lookalike expansion:

- **Co-investor graph (Crunchbase):** for each Tier 1 angel, fetch other angels who frequently co-invest. Add as candidates with tag `lookalike:<seed_name>`.
- **Twitter follow graph (if API access):** mutual followers of multiple Tier 1 prospects.

Lookalikes go through the same enrichment + classifier pipeline. They don't bypass scoring.

## Source priority config

The order above maps to `config/sources.yaml`. Bucket 1 runs first (manual seeds), then 2–6 in parallel where possible, then 7–8.
