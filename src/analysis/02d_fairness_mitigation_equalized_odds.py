#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02d_fairness_mitigation_equalized_odds.py

Purpose
-------
Post-processing mitigation to reduce Equal Opportunity (TPR) gaps:
- Learn subgroup-specific thresholds per (namespace, subgroup, class)
- Apply thresholds to prediction scores to create a new predictions CSV
  compatible with the rest of the pipeline.

Outputs
-------
reports/metrics/baseline_v1/predictions_test_{model_tag}.csv
reports/metrics/fairness_v1/eo_thresholds_{model_tag}.csv       # audit table

CLI
---
python -m src.analysis.02d_fairness_mitigation_equalized_odds \
  --base_model lr \
  --model_tag lr_eo \
  --namespaces race_ethnicity gender sexuality nationality hair_color age \
  --min_support 100 \
  --lambda_fpr 0.5 \
  --base_threshold 0.5

Notes
-----
- Use the same --base_threshold here that you plan to use as --threshold in
  src.analysis.02_fairness_eval to keep "overall" reference rates aligned.
"""

from __future__ import annotations
import argparse
import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

import numpy as np
import pandas as pd
import sqlite3

from src.utils.config_loader import (
    load_config as load_project_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)
from src.utils.lexicon_loader import ProtectedLexicon, DEFAULT_LEXICON_REL

# -----------------------------
# DB & lexicon helpers
# -----------------------------

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

def _fetch_text_for_ids(conn: sqlite3.Connection, video_ids: Sequence[int], chunk: int = 800) -> pd.DataFrame:
    out = []
    ids = list(map(int, video_ids))
    for i in range(0, len(ids), chunk):
        sub = ids[i:i+chunk]
        q = f"""
            SELECT v.video_id,
                   COALESCE(v.title,'') AS title,
                   COALESCE(t.tags,'')  AS tags
            FROM videos v
            LEFT JOIN temp_vt_agg t ON t.video_id = v.video_id
            WHERE v.video_id IN ({",".join(str(x) for x in sub)})
        """
        rows = conn.execute(q).fetchall()
        if rows:
            out.append(pd.DataFrame(rows, columns=rows[0].keys()))
    if not out:
        return pd.DataFrame(columns=["video_id","title","tags"])
    df = pd.concat(out, ignore_index=True)
    for col in ["title","tags"]:
        df[col] = df[col].fillna("").astype(str).str.lower()
    return df

def _compile_lexicon(lex_path: Path, boundary: str = "word") -> ProtectedLexicon:
    return ProtectedLexicon.from_json(lex_path).compile(boundary=boundary)

def _match_membership(text_df: pd.DataFrame, lex: ProtectedLexicon, namespaces: List[str]) -> Dict[int, Dict[str, Set[str]]]:
    out: Dict[int, Dict[str, Set[str]]] = {}
    for row in text_df.itertuples(index=False):
        vid = int(row.video_id)
        ns2: Dict[str, Set[str]] = {}
        for ns in namespaces:
            if ns not in lex.compiled:
                continue
            s: Set[str] = set()
            for sg, cg in lex.compiled[ns].groups.items():
                if any(p.search(row.title) for p in cg.patterns) or any(p.search(row.tags) for p in cg.patterns):
                    s.add(sg)
            if s:
                ns2[ns] = s
        out[vid] = ns2
    return out

# -----------------------------
# Predictions I/O
# -----------------------------

def _split_semicol(s: str) -> List[str]:
    if isinstance(s, float) and math.isnan(s):
        return []
    s = str(s).strip()
    return [] if s == "" else s.split(";")

def _read_labels_summary(path: Path) -> List[str]:
    df = pd.read_csv(path)
    return df["category"].tolist()

def _preds_to_long(preds_csv: Path, classes: List[str]) -> pd.DataFrame:
    df = pd.read_csv(preds_csv)
    df["video_id"] = df["video_id"].astype(int)
    df["true_labels_list"] = df["true_labels"].apply(_split_semicol)
    df["pred_labels_list"] = df["pred_topk"].apply(_split_semicol)
    df["pred_probs_list"]  = df["pred_topk_probs"].apply(lambda s: [float(x) for x in _split_semicol(s)])

    rows = []
    for vid, t_lbls, p_lbls, p_probs in df[["video_id","true_labels_list","pred_labels_list","pred_probs_list"]].itertuples(index=False):
        t_set = set(t_lbls)
        p_map = {lab: prob for lab, prob in zip(p_lbls, p_probs)}
        for c in classes:
            y = 1 if c in t_set else 0
            s = float(p_map.get(c, 0.0))
            rows.append((vid, c, y, s))
    out = pd.DataFrame(rows, columns=["video_id","class","y_true","score"])
    return out

# -----------------------------
# EO objective + search
# -----------------------------

def _counts_at_threshold(y: np.ndarray, s: np.ndarray, thr: float) -> Tuple[int,int,int,int]:
    yhat = (s >= thr).astype(int)
    tp = int(((y==1) & (yhat==1)).sum())
    fn = int(((y==1) & (yhat==0)).sum())
    fp = int(((y==0) & (yhat==1)).sum())
    tn = int(((y==0) & (yhat==0)).sum())
    return tp, fn, fp, tn

def _rate(x: int, n: int) -> float:
    return x/n if n>0 else float("nan")

def _search_threshold_for_group(y_all: np.ndarray, s_all: np.ndarray,
                                y_grp: np.ndarray, s_grp: np.ndarray,
                                base_thr: float = 0.5, lambda_fpr: float = 0.5) -> float:
    """Minimize |TPR_grp(t)-TPR_all(base)| + λ|FPR_grp(t)-FPR_all(base)| over t∈{0.00..1.00}."""
    tp, fn, fp, tn = _counts_at_threshold(y_all, s_all, base_thr)
    tpr_all = _rate(tp, tp+fn)
    fpr_all = _rate(fp, fp+tn)

    best_t = base_thr
    best_obj = float("inf")
    for t in np.linspace(0.0, 1.0, 101):
        tp_g, fn_g, fp_g, tn_g = _counts_at_threshold(y_grp, s_grp, t)
        tpr_g = _rate(tp_g, tp_g+fn_g)
        fpr_g = _rate(fp_g, fp_g+tn_g)
        if math.isnan(tpr_g) or math.isnan(fpr_g):
            continue
        obj = abs(tpr_g - tpr_all) + lambda_fpr * abs(fpr_g - fpr_all)
        if obj < best_obj:
            best_obj = obj
            best_t = float(t)
    return best_t

# -----------------------------
# Build post-processed predictions
# -----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Post-process predictions to reduce EO gaps via subgroup thresholds.")
    ap.add_argument("--base_model", type=str, default="lr",
                    help="Model tag to read from reports/metrics/baseline_v1/predictions_test_{base_model}.csv")
    ap.add_argument("--model_tag",  type=str, default="lr_eo",
                    help="Tag for the new, post-processed predictions file.")
    ap.add_argument("--namespaces", nargs="+",
                    default=["race_ethnicity","gender","sexuality","nationality","hair_color","age"],
                    help="Namespaces to use for subgroup thresholds.")
    ap.add_argument("--lambda_fpr", type=float, default=0.5,
                    help="Penalty λ for FPR deviation in the EO objective.")
    ap.add_argument("--min_support", type=int, default=100,
                    help="Minimum subgroup size to fit a threshold.")
    ap.add_argument("--base_threshold", type=float, default=0.5,
                    help="Reference threshold used to compute TPR/FPR(all). Keep in sync with 02_fairness_eval --threshold.")
    args = ap.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="EO post-processing (threshold search)")

    metrics_root = cfg.paths.metrics
    base_dir = metrics_root / "baseline_v1"
    fair_dir = metrics_root / "fairness_v1"
    (fair_dir).mkdir(parents=True, exist_ok=True)

    labels_path = base_dir / "labels_summary.csv"
    classes = _read_labels_summary(labels_path)

    preds_csv = base_dir / f"predictions_test_{args.base_model}.csv"
    if not preds_csv.exists():
        raise FileNotFoundError(f"Predictions not found: {preds_csv}")

    long_df = _preds_to_long(preds_csv, classes)

    # membership via DB+lexicon
    conn = _connect(cfg.paths.database)
    _ensure_temp_tag_agg(conn)
    vids = long_df["video_id"].drop_duplicates().tolist()
    text_df = _fetch_text_for_ids(conn, vids)
    lex = _compile_lexicon(cfg.paths.root / DEFAULT_LEXICON_REL, boundary="word")
    namespaces = [ns for ns in args.namespaces if ns in lex.compiled]
    mem = _match_membership(text_df, lex, namespaces)  # {vid: {ns: {sg,...}}}

    # learn thresholds per (namespace, subgroup, class)
    thr_map: Dict[Tuple[str,str,str], float] = {}  # (ns,sg,class) -> thr
    base_thr = float(args.base_threshold)
    learned = 0
    for c, g_all in long_df.groupby("class"):
        y_all = g_all["y_true"].values.astype(int)
        s_all = g_all["score"].values.astype(float)
        vid2idx = dict((int(v), i) for i, v in enumerate(g_all["video_id"].values))
        for ns in namespaces:
            sg2vids: Dict[str, List[int]] = {}
            for vid in g_all["video_id"].unique():
                for sg in mem.get(int(vid), {}).get(ns, set()):
                    sg2vids.setdefault(sg, []).append(int(vid))
            for sg, sg_vids in sg2vids.items():
                if len(sg_vids) < args.min_support:
                    continue
                idx = [vid2idx[v] for v in sg_vids if v in vid2idx]
                if not idx:
                    continue
                y_g = y_all[idx]
                s_g = s_all[idx]
                t = _search_threshold_for_group(y_all, s_all, y_g, s_g,
                                                base_thr=base_thr, lambda_fpr=args.lambda_fpr)
                thr_map[(ns, sg, c)] = float(t)
                learned += 1

    # audit: write thresholds table
    if thr_map:
        rows = [{"namespace": ns, "subgroup": sg, "class": cl, "threshold": thr}
                for (ns, sg, cl), thr in thr_map.items()]
        pd.DataFrame(rows).sort_values(["namespace","subgroup","class"]).to_csv(
            fair_dir / f"eo_thresholds_{args.model_tag}.csv", index=False
        )

    # apply thresholds (conservative if multiple applicable)
    def _threshold_for(vid: int, cls: str) -> float:
        ths = []
        for ns, sgs in mem.get(int(vid), {}).items():
            for sg in sgs:
                t = thr_map.get((ns, sg, cls))
                if t is not None:
                    ths.append(float(t))
        if not ths:
            return base_thr
        return float(max(ths))

    # build new top-k lists per video (sorted by score desc, filtered by thr)
    out_rows = []
    for vid, g in long_df.groupby("video_id"):
        g_sorted = g.sort_values("score", ascending=False)
        chosen = []
        chosen_probs = []
        for cls, score in zip(g_sorted["class"].values, g_sorted["score"].values):
            thr = _threshold_for(int(vid), str(cls))
            if float(score) >= thr:
                chosen.append(str(cls))
                chosen_probs.append(f"{float(score):.6f}")
        # true labels from this vid (order not critical)
        true_labels = ";".join(sorted([str(cls) for cls, yy in zip(g["class"].values, g["y_true"].values) if int(yy) == 1]))
        pred_topk = ";".join(chosen)
        pred_topk_probs = ";".join(chosen_probs)
        out_rows.append((int(vid), true_labels, pred_topk, pred_topk_probs))

    out_df = pd.DataFrame(out_rows, columns=["video_id","true_labels","pred_topk","pred_topk_probs"])
    out_path = base_dir / f"predictions_test_{args.model_tag}.csv"
    out_df.to_csv(out_path, index=False)
    print(f"[done] Wrote {out_path}")
    print(f"[info] Learned thresholds: {learned} cells across (namespace, subgroup, class).")
    print("Next: run fairness on the post-processed file, e.g.:")
    print(f"  python -m src.analysis.02_fairness_eval --model {args.model_tag} --threshold {args.base_threshold} "
          "--namespaces race_ethnicity gender sexuality nationality hair_color age "
          "--intersections ALL2 ALL3 --min_support 100 --limit 80000")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
