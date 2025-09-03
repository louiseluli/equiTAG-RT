# RQ1 Evidence Pack — How to Run

## 1) Produce raw metrics + figures

```bash
python -m src.analysis.01_rq1_categorisation_evidence --limit 10000 --batch_size 5000  # smoke
python -m src.analysis.01_rq1_categorisation_evidence --batch_size 20000               # full
```

Outputs:
reports/metrics/v1*coverage_by_field.csv
reports/metrics/v1_subgroup_outcomes.csv
reports/metrics/v1_overlap_matrix*<namespace>.csv
Figures (two versions each): reports/figures/\*\_{light|dark}.png

## 3) Generate interpretive brief

```bash
python -m src.analysis.01c_rq1_interpretive_brief
Outputs:
Markdown: reports/metrics/markdown/v1r_rq1_interpretive_brief.md
CSV: reports/metrics/v1r_rq1_interpretive_brief.csv
Use these bullets to draft Chapter 4–5 commentary (coverage skews, labelling tilt, reception differentials, co-labelling).

```
