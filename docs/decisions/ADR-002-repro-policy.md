# ADR-002: Reproducibility & Device Policy

**Status:** Accepted — 2025-09-03

**Context.** Consistent seeds and device setup are necessary to ensure comparable results across fairness-sensitive experiments.

**Decision.**

- Use a central module `src/utils/config_loader.py` to:
  - Load project config and resolve paths.
  - Set global seed **75** (never 42) and deterministic flags where feasible.
  - Prefer **MPS** (Apple Silicon) > **CUDA** > **CPU**; avoid fp16 on MPS; set `torch.set_float32_matmul_precision('medium')`.

**Consequences.**

- All scripts share the same run header and reproducibility guarantees.
- Easier comparison of baseline vs mitigation runs in the dissertation.
