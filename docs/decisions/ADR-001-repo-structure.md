### `docs/decisions/ADR-001-repo-structure.md`

```markdown
# ADR-001: Repository Structure & First Artifact Strategy

**Status:** Accepted — 2025-09-03

**Context.** We must meet CE901 standards: replicable pipeline, clear docs, fair ML evaluation. Baseline proof of data integrity is required before modeling.

**Decision.** Use a conventional, analysis-first structure:

- `src/setup` for integrity/bootstrap tools.
- `reports/metrics` as the single sink for machine artifacts (CSV/JSON).
- Vendored legacy collectors under `src/collect` to be refactored later.

**Consequences.**

- Easy narrative: Data → Integrity → EDA → Modeling → Fairness → Mitigation.
- Artifacts ready for dissertation figures/tables; minimal friction to proceed.
```
