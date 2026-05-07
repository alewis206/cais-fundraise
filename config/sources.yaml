# config/sources.yaml
#
# Source priorities and per-adapter settings.
# Order matters: `cais-prospects ingest --all` runs in this order.

sources:
  # --- Phase 1 ---
  - name: manual_csv
    enabled: true
    priority: 1
    paths:
      - "data/seeds/initial.csv"
      - "data/seeds/audience_founders.csv"
      - "data/seeds/services_friendly_vcs.csv"
      - "data/seeds/si_cvcs.csv"
    column_mapping:
      name: ["name", "Full Name", "Name"]
      org: ["org", "Company", "Organization"]
      role: ["role", "Title", "Position"]
      linkedin_url: ["linkedin_url", "LinkedIn URL", "LinkedIn"]
      twitter_handle: ["twitter_handle", "Twitter", "X Handle"]
      email: ["email", "Email"]
      categories: ["categories"]

  # --- Phase 3 ---
  - name: linkedin_csv
    enabled: false  # enable in Phase 3
    priority: 2
    paths:
      - "data/seeds/linkedin/"  # ingests every CSV in this directory
    note: "Manual Sales Navigator exports only. Never automate against linkedin.com."

  - name: openvc
    enabled: false
    priority: 3
    csv_path: "data/seeds/openvc.csv"
    refresh_cadence: "quarterly"

  - name: crunchbase
    enabled: false
    priority: 4
    queries:
      - { type: "former_employees", org: "UiPath", role_seniority: "senior" }
      - { type: "former_employees", org: "Automation Anywhere", role_seniority: "senior" }
      - { type: "former_employees", org: "Globant", role_seniority: "senior" }
      - { type: "former_employees", org: "Thoughtworks", role_seniority: "senior" }
      - { type: "active_angels", focus_areas: ["enterprise_saas", "ai", "services"] }
    cache_days: 30

  - name: podcast_guests
    enabled: false
    priority: 5
    podcasts:
      - "My First Million"
      - "Acquired"
      - "The Twenty Minute VC"
      - "Latent Space"
      - "All-In"
      - "Invest Like the Best"

  - name: twitter_bio
    enabled: false
    priority: 6
    bio_searches:
      - "ex-UiPath angel"
      - "former founder AI services"
      - "ex-Globant operator"
    note: "Skip gracefully if no Twitter API access."

# Per-source kill criteria
yield_thresholds:
  min_tier_1_2_yield_pct: 5
  min_prospects_before_evaluation: 100
  action_on_low_yield: "warn"  # values: warn | disable | drop
