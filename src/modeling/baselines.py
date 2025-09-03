"""
src/modeling/baselines.py

Purpose
-------
Train two reproducible baselines for category prediction from text metadata:
A) TF-IDF + One-vs-Rest Logistic Regression  (strong linear baseline)
B) TF-IDF → TruncatedSVD → One-vs-Rest RandomForest  (dense, interpretable via components)

Both use a time-based split (train/val/test) to prevent temporal leakage.
Outputs include model artifacts, predictions per video_id, and per-class metrics
needed for downstream fairness evaluation.

Inputs (SQLite)
---------------
- videos(video_id, title, publish_date, is_active)
- video_tags(video_id, tag)
- video_categories(video_id, category)

Text feature:
- Combined "doc" = title + " " + aggregated tags (word-bounded lexicon already audited).

Targets
-------
- Multi-label: top-K frequent categories by support (K tunable). Instances may be all-zero (no top-K labels).

Outputs
-------
Folder: reports/metrics/baseline_v1/
- labels_summary.csv                (support per category, selected top-K)
- split_summary.csv                 (rows per split)
- lr_macro_metrics.csv              (macro P/R/F1 on val/test)
- rf_macro_metrics.csv
- lr_per_class_metrics.csv          (per-class P/R/F1 on test)
- rf_per_class_metrics.csv
- predictions_test_lr.csv           (video_id, true_labels, top5_pred, top5_prob)
- predictions_test_rf.csv
- svd_component_terms.csv           (component -> top terms; for interpretability)
- rf_perm_importance.csv            (class -> top components + importance)

Folder: models/baseline_v1/
- tfidf_vectorizer.joblib
- mlb_labels.joblib
- lr_ovr.joblib
- svd_256.joblib
- rf_ovr.joblib

Assumptions
-----------
- Scikit-learn, pandas, scipy available; code guards with helpful errors if missing.
- Publish_date stored as text ISO (YYYY-MM-DD ...) — parsed to pandas datetime.
- Dataset large; CLI provides --limit to sample first for quick runs.

Complexity
----------
- TF-IDF up to ~200k features (sparse); LR with OVR is parallel over classes.
- RF branch uses SVD=256 dense features to avoid memory blow-ups.

Test Notes
----------
- Smoke run: --limit 80000 --top_k 20 --min_cat_count 5000 --svd_components 128 --interpret_k 5
"""

from __future__ import annotations
import argparse
import csv
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple, Iterable, Optional

# Soft deps
try:
    import numpy as np
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import MultiLabelBinarizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.decomposition import TruncatedSVD
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.multiclass import OneVsRestClassifier
    from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
    from sklearn.inspection import permutation_importance
    import joblib
except Exception as e:
    raise SystemExit(
        "Missing dependencies. Please install: pandas scikit-learn scipy joblib numpy\n"
        "Example: pip install 'pandas>=1.5' 'scikit-learn>=1.2' scipy joblib numpy"
    ) from e

from src.utils.config_loader import (
    load_config as load_project_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)

# ------------------------------ DB utils ------------------------------

def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def _ensure_temp_tag_agg(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS temp_vt_agg")
    conn.execute("""
        CREATE TEMP TABLE temp_vt_agg AS
        SELECT video_id, GROUP_CONCAT(tag, ' ') AS tags
        FROM video_tags
        GROUP BY video_id
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_vt_agg_vid ON temp_vt_agg(video_id)")

# ------------------------------ I/O utils -----------------------------

def _write_csv(path: Path, header: List[str], rows: Iterable[Iterable]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def _dump_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

# ------------------------------ Data prep -----------------------------

def _fetch_base_df(conn: sqlite3.Connection, limit: Optional[int]) -> pd.DataFrame:
    base = """
        SELECT v.video_id, v.title, v.publish_date, COALESCE(t.tags,'') AS tags
        FROM videos v
        LEFT JOIN temp_vt_agg t ON t.video_id = v.video_id
        WHERE v.is_active = 1
        ORDER BY v.video_id
    """
    if limit:
        base += f" LIMIT {int(limit)}"
    rows = conn.execute(base).fetchall()
    df = pd.DataFrame(rows, columns=rows[0].keys() if rows else ["video_id","title","publish_date","tags"])
    df["title"] = df["title"].fillna("")
    df["tags"] = df["tags"].fillna("")
    df["doc"] = (df["title"].astype(str) + " " + df["tags"].astype(str)).str.strip()
    # dates
    df["publish_date"] = pd.to_datetime(df["publish_date"], errors="coerce")
    # backfill missing with earliest date to keep in train
    if df["publish_date"].isna().any():
        min_dt = df["publish_date"].dropna().min() if df["publish_date"].notna().any() else pd.Timestamp("2010-01-01")
        df.loc[df["publish_date"].isna(), "publish_date"] = min_dt
    return df

def _labels_for_top_k(conn: sqlite3.Connection, candidates: pd.Series, top_k: int, min_cat_count: int) -> Tuple[Dict[int, List[str]], List[str], pd.DataFrame]:
    """
    Build multi-label dict for selected video_ids and choose top-K categories by support.
    Returns: (vid2labels, classes, summary_df)
    """
    vids = ",".join(map(str, candidates.tolist()))
    q = f"SELECT video_id, category FROM video_categories WHERE video_id IN ({vids})"
    rows = conn.execute(q).fetchall()
    df = pd.DataFrame(rows, columns=["video_id","category"])
    # support
    sup = df["category"].value_counts().reset_index()
    sup.columns = ["category","count"]
    sup = sup[sup["count"] >= min_cat_count].sort_values("count", ascending=False)
    if top_k > 0:
        sup = sup.head(top_k)
    classes = sup["category"].tolist()
    # vid → labels among selected classes
    df_sel = df[df["category"].isin(classes)]
    vid2labels: Dict[int, List[str]] = df_sel.groupby("video_id")["category"].apply(list).to_dict()
    return vid2labels, classes, sup

def _assign_multilabel(df: pd.DataFrame, vid2labels: Dict[int, List[str]]) -> List[List[str]]:
    return [vid2labels.get(int(v), []) for v in df["video_id"].tolist()]

def _time_split(df: pd.DataFrame, train_q: float = 0.70, val_q: float = 0.85) -> pd.Series:
    """
    Split by publish_date quantiles into train/val/test (non-overlapping).
    """
    ords = df["publish_date"].astype(np.int64)  # ns epoch
    q1 = np.quantile(ords, train_q)
    q2 = np.quantile(ords, val_q)
    def _bucket(x):
        xi = int(x.value)
        if xi <= q1:
            return "train"
        elif xi <= q2:
            return "val"
        else:
            return "test"
    return df["publish_date"].apply(_bucket)

# ------------------------------ Modeling -----------------------------

def _train_lr_ovr(X_tr, Y_tr, C: float, max_iter: int, n_jobs: int) -> OneVsRestClassifier:
    base = LogisticRegression(
        solver="saga", penalty="l2", C=C, max_iter=max_iter, n_jobs=n_jobs,
        class_weight="balanced", verbose=0
    )
    return OneVsRestClassifier(base, n_jobs=n_jobs).fit(X_tr, Y_tr)

def _train_rf_svd_ovr(X_tr, Y_tr, n_components: int, n_estimators: int, max_depth: int, n_jobs: int):
    svd = TruncatedSVD(n_components=n_components, random_state=0)
    Z_tr = svd.fit_transform(X_tr)
    rf = RandomForestClassifier(
        n_estimators=n_estimators, max_depth=max_depth, n_jobs=n_jobs,
        class_weight="balanced", random_state=0
    )
    clf = OneVsRestClassifier(rf, n_jobs=n_jobs).fit(Z_tr, Y_tr)
    return svd, clf

def _eval_split(name: str, model, X, Y_true, classes: List[str]) -> Tuple[Dict[str,float], pd.DataFrame]:
    Y_pred = model.predict(X)
    macro = {
        "split": name,
        "precision_macro": precision_score(Y_true, Y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(Y_true, Y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(Y_true, Y_pred, average="macro", zero_division=0),
    }
    # Per-class
    rep = classification_report(Y_true, Y_pred, target_names=classes, output_dict=True, zero_division=0)
    rows = []
    for c in classes:
        d = rep.get(c, {})
        rows.append([name, c, d.get("precision",0.0), d.get("recall",0.0), d.get("f1-score",0.0), d.get("support",0)])
    df = pd.DataFrame(rows, columns=["split","class","precision","recall","f1","support"])
    return macro, df

def _topk_probs(model, X, classes: List[str], k: int = 5) -> Tuple[List[List[str]], List[List[float]]]:
    # LR supports predict_proba; RF in OVR also supports
    probs = model.predict_proba(X)
    # probs is list of arrays per class in OVR; stack to shape (n_samples, n_classes)
    if isinstance(probs, list):
        # sklearn>=1.4 returns list; otherwise np.array
        P = np.column_stack(probs)
    else:
        P = probs
    top_idx = np.argsort(-P, axis=1)[:, :k]
    top_labels = [[classes[j] for j in row] for row in top_idx]
    top_scores = [[float(P[i, j]) for j in row] for i, row in enumerate(top_idx)]
    return top_labels, top_scores

def _save_predictions_csv(path: Path, video_ids: List[int], y_true_bin, classes: List[str], top_labels: List[List[str]], top_scores: List[List[float]]) -> None:
    header = ["video_id", "true_labels", "pred_topk", "pred_topk_probs"]
    rows = []
    ytrue_lbls = [ [classes[j] for j,v in enumerate(row) if v==1] for row in y_true_bin ]
    for vid, t_lbls, p_lbls, p_scores in zip(video_ids, ytrue_lbls, top_labels, top_scores):
        rows.append([int(vid), ";".join(t_lbls), ";".join(p_lbls), ";".join(f"{s:.4f}" for s in p_scores)])
    _write_csv(path, header, rows)

def _svd_component_top_terms(vectorizer: TfidfVectorizer, svd: TruncatedSVD, top_n: int = 20) -> pd.DataFrame:
    """
    Map each SVD component to its top contributing terms (by absolute loading).
    """
    terms = np.array(vectorizer.get_feature_names_out())
    comp = svd.components_  # shape (n_components, n_terms)
    rows = []
    for ci in range(comp.shape[0]):
        weights = comp[ci, :]
        idx = np.argsort(-np.abs(weights))[:top_n]
        top_terms = terms[idx].tolist()
        top_w = weights[idx].tolist()
        rows.append([ci, ";".join(top_terms), ";".join([f"{w:.4f}" for w in top_w])])
    return pd.DataFrame(rows, columns=["component","top_terms","weights"])

# ------------------------------- Main --------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Baseline models: TF-IDF+LR and SVD+RF with time-based split.")
    ap.add_argument("--limit", type=int, default=None, help="Limit #active videos to load (for smoke runs).")
    ap.add_argument("--top_k", type=int, default=30, help="Top-K categories by support to model.")
    ap.add_argument("--min_cat_count", type=int, default=3000, help="Minimum support for a category to be eligible.")
    ap.add_argument("--tfidf_max_features", type=int, default=200_000, help="Max features for TF-IDF (1-2 grams).")
    ap.add_argument("--svd_components", type=int, default=256, help="SVD components for RF branch.")
    ap.add_argument("--rf_estimators", type=int, default=300, help="Trees in RF.")
    ap.add_argument("--rf_max_depth", type=int, default=20, help="Max depth for RF.")
    ap.add_argument("--interpret_k", type=int, default=8, help="#classes to run RF permutation importance on (val split).")
    ap.add_argument("--n_jobs", type=int, default=-1, help="Parallelism for scikit-learn (OVR etc.).")
    args = ap.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="Baselines v1")

    # Paths
    metrics_dir = (cfg.paths.metrics / "baseline_v1"); metrics_dir.mkdir(parents=True, exist_ok=True)
    models_dir  = (cfg.paths.root / "models" / "baseline_v1"); models_dir.mkdir(parents=True, exist_ok=True)

    # DB
    conn = _connect(cfg.paths.database)
    _ensure_temp_tag_agg(conn)

    # Data
    df = _fetch_base_df(conn, args.limit)
    vid2labels, classes, sup_df = _labels_for_top_k(conn, df["video_id"], top_k=args.top_k, min_cat_count=args.min_cat_count)
    _write_csv(metrics_dir / "labels_summary.csv", ["category","count"], sup_df[["category","count"]].itertuples(index=False))

    df["labels"] = _assign_multilabel(df, vid2labels)
    df["split"] = _time_split(df)

    # Split frames
    tr = df[df["split"] == "train"].copy()
    va = df[df["split"] == "val"].copy()
    te = df[df["split"] == "test"].copy()

    # Summaries
    _write_csv(metrics_dir / "split_summary.csv", ["split","rows"], [["train", len(tr)], ["val", len(va)], ["test", len(te)]])

    # Vectorize text (fit on train only)
    tfidf = TfidfVectorizer(
        lowercase=True, ngram_range=(1,2), min_df=5, max_features=args.tfidf_max_features,
        dtype=np.float32
    )
    X_tr = tfidf.fit_transform(tr["doc"].tolist())
    X_va = tfidf.transform(va["doc"].tolist())
    X_te = tfidf.transform(te["doc"].tolist())
    joblib.dump(tfidf, models_dir / "tfidf_vectorizer.joblib")

    # Multi-label binarizer
    mlb = MultiLabelBinarizer(classes=classes)
    Y_tr = mlb.fit_transform(tr["labels"])
    Y_va = mlb.transform(va["labels"])
    Y_te = mlb.transform(te["labels"])
    joblib.dump(mlb, models_dir / "mlb_labels.joblib")

    # ----------------- A) TF-IDF + Logistic Regression OVR -----------------
    lr_ovr = _train_lr_ovr(X_tr, Y_tr, C=4.0, max_iter=1000, n_jobs=args.n_jobs)
    joblib.dump(lr_ovr, models_dir / "lr_ovr.joblib")

    # Evaluate
    macro_va, per_va = _eval_split("val", lr_ovr, X_va, Y_va, classes)
    macro_te, per_te = _eval_split("test", lr_ovr, X_te, Y_te, classes)
    _write_csv(metrics_dir / "lr_macro_metrics.csv", ["split","precision_macro","recall_macro","f1_macro"],
               [[macro_va["split"], macro_va["precision_macro"], macro_va["recall_macro"], macro_va["f1_macro"]],
                [macro_te["split"], macro_te["precision_macro"], macro_te["recall_macro"], macro_te["f1_macro"]]])
    per_te.to_csv(metrics_dir / "lr_per_class_metrics.csv", index=False)

    # Predictions (top-5) on test
    tl_lr, ts_lr = _topk_probs(lr_ovr, X_te, classes, k=5)
    _save_predictions_csv(metrics_dir / "predictions_test_lr.csv", te["video_id"].tolist(), Y_te, classes, tl_lr, ts_lr)

    # ----------------- B) TF-IDF → SVD → RandomForest OVR -----------------
    svd, rf_ovr = _train_rf_svd_ovr(X_tr, Y_tr, n_components=args.svd_components,
                                    n_estimators=args.rf_estimators, max_depth=args.rf_max_depth,
                                    n_jobs=args.n_jobs)
    joblib.dump(svd, models_dir / "svd_256.joblib")
    joblib.dump(rf_ovr, models_dir / "rf_ovr.joblib")

    Z_va = svd.transform(X_va)
    Z_te = svd.transform(X_te)

    # Evaluate
    macro_va_rf, per_va_rf = _eval_split("val", rf_ovr, Z_va, Y_va, classes)
    macro_te_rf, per_te_rf = _eval_split("test", rf_ovr, Z_te, Y_te, classes)
    _write_csv(metrics_dir / "rf_macro_metrics.csv", ["split","precision_macro","recall_macro","f1_macro"],
               [[macro_va_rf["split"], macro_va_rf["precision_macro"], macro_va_rf["recall_macro"], macro_va_rf["f1_macro"]],
                [macro_te_rf["split"], macro_te_rf["precision_macro"], macro_te_rf["recall_macro"], macro_te_rf["f1_macro"]]])
    per_te_rf.to_csv(metrics_dir / "rf_per_class_metrics.csv", index=False)

    # Predictions (top-5) on test
    tl_rf, ts_rf = _topk_probs(rf_ovr, Z_te, classes, k=5)
    _save_predictions_csv(metrics_dir / "predictions_test_rf.csv", te["video_id"].tolist(), Y_te, classes, tl_rf, ts_rf)

    # Interpretability: components → terms
    comp_terms = _svd_component_top_terms(tfidf, svd, top_n=20)
    comp_terms.to_csv(metrics_dir / "svd_component_terms.csv", index=False)

    # Permutation importance on validation (top-K frequent classes)
    # (compute on SVD space; tie back via component_terms table above)
    sup_sorted = sup_df.sort_values("count", ascending=False)["category"].tolist()
    target_classes = sup_sorted[: max(1, args.interpret_k)]
    rows_imp = []
    for cls in target_classes:
        idx = classes.index(cls)
        est = rf_ovr.estimators_[idx]  # base RF for this class
        # Use permutation_importance on validation SVD features
        r = permutation_importance(est, Z_va, Y_va[:, idx], n_repeats=3, random_state=0, n_jobs=args.n_jobs)
        top_idx = np.argsort(-r.importances_mean)[:15]
        for rank, j in enumerate(top_idx, start=1):
            rows_imp.append([cls, rank, int(j), float(r.importances_mean[j]), float(r.importances_std[j])])
    _write_csv(metrics_dir / "rf_perm_importance.csv",
               ["class","rank","component","importance_mean","importance_std"],
               rows_imp)

    print("[done] Baselines v1 trained and evaluated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
