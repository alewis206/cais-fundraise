# 07 — Risks and Out of Scope

## Risks and mitigations

### LinkedIn ToS violation
**Risk:** automated LinkedIn scraping → Devin or Andrew gets account banned. Catastrophic for warm-intro mapping.
**Mitigation:** the `linkedin_csv` adapter is the only way LinkedIn data enters the system. Manual Sales Navigator exports only. This rule is in `CLAUDE.md` as a hard rule. No exceptions.

### Classifier hallucinates investor backgrounds
**Risk:** the LLM invents details about a prospect's history, leading to wrong tier assignment and embarrassing outreach.
**Mitigation:**
- Structured JSON output with required fields.
- Every classification stores `rationale` and `confidence`.
- Tier 1 candidates re-classified with Opus.
- Sample-audit 20 random Tier 1 records before any outreach.
- Surface confidence in the Google Sheet so users see when the system is unsure.

### Email enrichment returns wrong addresses
**Risk:** Apollo/Hunter returns a stale or wrong email; outreach goes to a dead address or worse, the wrong person.
**Mitigation:** every email has a `email_confidence` score. Sheet flags <80% confidence as "verify manually." Don't trust low-confidence emails for high-stakes outreach.

### Crunchbase API costs balloon
**Risk:** unbounded Crunchbase queries blow through monthly budget.
**Mitigation:**
- Aggressive caching (30 days) on every Crunchbase response.
- Re-fetch only on `--force-refresh` or when stale.
- Monthly spend logged in `api_call_log`. Alert at 80% of budget.

### List grows but quality drops
**Risk:** adding more sources adds noise faster than signal. Tier 1/2 yield dilutes.
**Mitigation:** per-source yield report. Sources producing <5% Tier 1/2 over 100+ prospects are killed (or downgraded to manual-only).

### Devin and Andrew don't actually use the sheet
**Risk:** beautiful tooling, no behavior change.
**Mitigation:**
- Keep the sheet simple. No fancy UI.
- Status enum is short.
- They already use Google Sheets daily; this fits their existing workflow.
- Phase 1 must produce a usable sheet within the first week.

### Rubric drift
**Risk:** the rubric is updated, but old classifications aren't refreshed, leading to inconsistent tiers across the list.
**Mitigation:** every classification stores `prompt_version`. `cais-prospects classify --stale` re-classifies anything whose prompt version is older than the current.

### Cost ceiling breach
**Risk:** a full reclassification costs >$50 because of model misuse or a runaway loop.
**Mitigation:** `classify --all` projects spend before running, prompts for confirmation if >$50. Default model is Sonnet, never Opus for bulk.

## Out of scope (v1)

These are explicitly NOT being built. Don't bend toward them.

- **Automated email sending.** No email integrations. Outreach is composed by humans in their existing tools (Gmail, Superhuman, etc.).
- **Web UI / dashboard.** The Google Sheet is the UI. Resist building anything else.
- **Multi-user access controls.** Single-tenant.
- **CRM features beyond status tracking.** No deal pipeline, no document storage, no SAFE management. Use Carta or Pulley for cap table; Notion or Affinity for full CRM if needed later.
- **Real-time integrations.** No webhooks, no event-driven anything. All flows are CLI-triggered.
- **Browser extensions.** No Chrome extension to enrich on LinkedIn. (And remember: no LinkedIn automation, period.)
- **Investor outreach analytics.** Reply rates, A/B testing on subject lines — out of scope. If wanted, do this manually in the sheet.
- **Public API.** Internal tool only.
- **Mobile app.** No.
- **AI-generated outreach drafts.** Tempting, but no. Human-written outreach is the explicit decision in `CLAUDE.md`.

## Future work (post-raise)

If this system proves valuable beyond the current raise, consider:

- Repurposing for client prospecting (the same 8 buckets logic applies, with a different rubric).
- Annual rubric refresh based on yield data (which categories actually converted).
- Adding integrations only if they're requested by the user, not because they're available.
