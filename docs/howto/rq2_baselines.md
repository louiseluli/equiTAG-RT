# RQ2 Baselines — TF-IDF+LR and SVD+RF (time-based split)

## Run (smoke vs full)

```bash
# Smoke (fast):
python -m src.modeling.baselines --limit 80000 --top_k 20 --min_cat_count 5000 --svd_components 128 --interpret_k 5

# Full:
python -m src.modeling.baselines --top_k 30 --min_cat_count 3000 --svd_components 256 --rf_estimators 300 --rf_max_depth 20
```
