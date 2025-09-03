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
