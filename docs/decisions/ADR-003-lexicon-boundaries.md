# ADR-003: Lexicon boundaries & wildcard policy

**Status:** Accepted — 2025-09-03

**Decision.**

- Compile regex with **edge** guards `(?<!\w) ... (?!\w)` to avoid substring false positives (e.g., "asian" in "caucasian").
- Multi-word phrases map spaces to `\s+`.
- Allow `*` as wildcard (-> `.*`) for demonyms/variants but keep use limited and reviewed.

**Consequences.**

- Lower false positives and stable counts for fairness metrics.
- Lexicon overlaps are surfaced in `v0_lexicon_audit.json` for transparent reporting.
