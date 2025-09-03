# RQ3 Fairness Evaluation — Subgroups, Intersections, and Engagement

## Run (examples)

```bash
# Subgroups only
python -m src.analysis.02_fairness_eval \
  --model lr --threshold 0.5 \
  --namespaces race_ethnicity gender sexuality nationality hair_color age \
  --min_support 100 --limit 80000

# Subgroups + all 2-way and 3-way intersections
python -m src.analysis.02_fairness_eval \
  --model lr --threshold 0.5 \
  --namespaces race_ethnicity gender sexuality nationality hair_color age \
  --intersections ALL2 ALL3 \
  --min_support 100 --limit 80000

# Explicit combos
python -m src.analysis.02_fairness_eval \
  --model rf --threshold 0.5 \
  --namespaces race_ethnicity gender nationality \
  --intersections gender*race_ethnicity gender*race_ethnicity*nationality
```

# RQ3 Fairness Evaluation — Subgroups, Intersections, and Engagement

## Run (examples)

```bash
# Subgroups only
python -m src.analysis.02_fairness_eval \
  --model lr --threshold 0.5 \
  --namespaces race_ethnicity gender sexuality nationality hair_color age \
  --min_support 100 --limit 80000

# Subgroups + all 2-way and 3-way intersections
python -m src.analysis.02_fairness_eval \
  --model lr --threshold 0.5 \
  --namespaces race_ethnicity gender sexuality nationality hair_color age \
  --intersections ALL2 ALL3 \
  --min_support 100 --limit 80000

# Explicit combos
python -m src.analysis.02_fairness_eval \
  --model rf --threshold 0.5 \
  --namespaces race_ethnicity gender nationality \
  --intersections gender*race_ethnicity gender*race_ethnicity*nationality
```
