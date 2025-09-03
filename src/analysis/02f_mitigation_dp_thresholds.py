#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02f_mitigation_dp_thresholds.py

Purpose
-------
Post-processing mitigation to reduce Demographic Parity gaps:
- Learn subgroup-specific thresholds per (namespace, subgroup, class)
  such that PR(group) approaches PR(all) at the base threshold.
- Optionally regularize precision to avoid severe precision drift.
- Produce a predictions CSV fully compatible with downstream fairness pipeline.

Outputs
-------
- reports/metrics/baseline_v1/predictions_test_{model_tag}.csv
- reports/metrics/fairness_v1/dp_thresholds_{model_tag}.csv   (audit)

CLI
---
python -m src.analysis.02f_mitigation_dp_thresholds \
  --base_model lr \
  --model_tag lr_dp \
  --namespaces race_ethnicity gender sexuality nationality hair_color age \
  --min_support 100 \
  --lambda_precision 0.0 \
  --base_threshold 0.5
"""
from __future__ import annotations

import argparse
import math
import sqlite3
from pathlib import Path
from typing import Dict, List, Sequence, Set, Tuple

import numpy as np
import pandas as pd

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
# Metrics & search
# -----------------------------

def _counts_at_threshold(y: np.ndarray, s: np.ndarray, thr: float) -> Tuple[int,int,int,int,int,int]:
    """Return (n, n_pospred, tp, fp, fn, tn)."""
    yhat = (s >= thr).astype(int)
    n = int(yhat.size)
    n_pospred = int((yhat == 1).sum())
    tp = int(((y==1) & (yhat==1)).sum())
    fp = int(((y==0) & (yhat==1)).sum())
    fn = int(((y==1) & (yhat==0)).sum())
    tn = int(((y==0) & (yhat==0)).sum())
    return n, n_pospred, tp, fp, fn, tn

def _rate(num: int, den: int) -> float:
    return (num/den) if den>0 else float("nan")

def _search_threshold_for_group_dp(
    y_all: np.ndarray, s_all: np.ndarray,
    y_grp: np.ndarray, s_grp: np.ndarray,
    base_thr: float = 0.5,
    lambda_precision: float = 0.0
) -> Tuple[float, Dict[str, float]]:
    """
    Minimize |PR_grp(t) - PR_all(base)| + λ * |Prec_grp(t) - Prec_all(base)|.
    Return best t and diagnostic metrics.
    """
    # Overall at base
    nA, nposA, tpA, fpA, fnA, tnA = _counts_at_threshold(y_all, s_all, base_thr)
    pr_all = _rate(nposA, nA)
    prec_all = _rate(tpA, tpA + fpA)

    best_t = base_thr
    best_obj = float("inf")
    best_stats = {}

    for t in np.linspace(0.0, 1.0, 101):
        nG, nposG, tpG, fpG, fnG, tnG = _counts_at_threshold(y_grp, s_grp, t)
        pr_g = _rate(nposG, nG)
        prec_g = _rate(tpG, tpG + fpG)
        # define objective robustly when precision undefined
        obj = abs(pr_g - pr_all)
        if not math.isnan(prec_g) and not math.isnan(prec_all) and lambda_precision > 0:
            obj += lambda_precision * abs(prec_g - prec_all)
        if obj < best_obj:
            best_obj = obj
            best_t = float(t)
            best_stats = {
                "pr_all": pr_all, "prec_all": prec_all,
                "pr_grp": pr_g, "prec_grp": prec_g,
                "npos_all": nposA, "n_all": nA,
                "tp_all": tpA, "fp_all": fpA,
                "npos_grp": nposG, "n_grp": nG,
                "tp_grp": tpG, "fp_grp": fpG,
            }
    return best_t, best_stats

# -----------------------------
# Build post-processed predictions
# -----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Post-process predictions to reduce DP gaps via subgroup thresholds (+precision reg).")
    ap.add_argument("--base_model", type=str, default="lr", help="Base predictions tag (reads predictions_test_{base_model}.csv).")
    ap.add_argument("--model_tag",  type=str, default="lr_dp", help="Tag for post-processed predictions file.")
    ap.add_argument("--namespaces", nargs="+",
                    default=["race_ethnicity","gender","sexuality","nationality","hair_color","age"],
                    help="Namespaces to use for subgroup thresholds.")
    ap.add_argument("--min_support", type=int, default=100, help="Minimum subgroup size to fit a threshold.")
    ap.add_argument("--lambda_precision", type=float, default=0.0, help="Penalty λ for precision deviation.")
    ap.add_argument("--base_threshold", type=float, default=0.5, help="Base threshold for computing overall PR/precision.")
    args = ap.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="DP post-processing (threshold search)")

    metrics_root = cfg.paths.metrics
    base_dir = metrics_root / "baseline_v1"
    preds_csv = base_dir / f"predictions_test_{args.base_model}.csv"
    if not preds_csv.exists():
        raise FileNotFoundError(f"Predictions not found: {preds_csv}")

    labels_path = base_dir / "labels_summary.csv"
    classes = _read_labels_summary(labels_path)

    long_df = _preds_to_long(preds_csv, classes)

    # membership via DB+lexicon
    conn = _connect(cfg.paths.database)
    _ensure_temp_tag_agg(conn)
    vids = long_df["video_id"].drop_duplicates().tolist()
    text_df = _fetch_text_for_ids(conn, vids)
    lex = _compile_lexicon(cfg.paths.root / DEFAULT_LEXICON_REL, boundary="word")
    namespaces = [ns for ns in args.namespaces if ns in lex.compiled]
    mem = _match_membership(text_df, lex, namespaces)  # {vid: {ns:{sg,...}}}

    # learn thresholds per (namespace, subgroup, class)
    thr_map: Dict[Tuple[str,str,str], float] = {}
    audit_rows: List[Dict[str, float]] = []

    for c, g_all in long_df.groupby("class"):
        y_all = g_all["y_true"].values.astype(int)
        s_all = g_all["score"].values.astype(float)
        vid2idx = {int(v): i for i, v in enumerate(g_all["video_id"].values)}

        for ns in namespaces:
            # group video ids by subgroup
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

                t_star, stats = _search_threshold_for_group_dp(
                    y_all, s_all, y_g, s_g,
                    base_thr=args.base_threshold,
                    lambda_precision=args.lambda_precision
                )
                thr_map[(ns, sg, c)] = t_star

                # also record metrics at base threshold for the group
                from_counts_base = _counts_at_threshold(y_g, s_g, args.base_threshold)
                nG, nposG, tpG, fpG, fnG, tnG = from_counts_base
                pr_g_base = _rate(nposG, nG)
                prec_g_base = _rate(tpG, tpG + fpG)

                # and metrics at chosen threshold
                nG2, nposG2, tpG2, fpG2, fnG2, tnG2 = _counts_at_threshold(y_g, s_g, t_star)
                pr_g_t = _rate(nposG2, nG2)
                prec_g_t = _rate(tpG2, tpG2 + fpG2)

                audit_rows.append({
                    "namespace": ns, "subgroup": sg, "class": c,
                    "threshold_base": args.base_threshold,
                    "threshold_star": t_star,
                    "pr_all_base": stats.get("pr_all", float("nan")),
                    "precision_all_base": stats.get("prec_all", float("nan")),
                    "pr_group_base": pr_g_base,
                    "precision_group_base": prec_g_base,
                    "pr_group_star": pr_g_t,
                    "precision_group_star": prec_g_t,
                    "npos_group_base": nposG, "npos_group_star": nposG2,
                    "tp_group_base": tpG, "fp_group_base": fpG,
                    "tp_group_star": tpG2, "fp_group_star": fpG2,
                })

    # apply thresholds conservatively (max of applicable thresholds)
    def _threshold_for(vid: int, cls: str) -> float:
        ths = []
        for ns, sgs in mem.get(int(vid), {}).items():
            for sg in sgs:
                t = thr_map.get((ns, sg, cls))
                if t is not None:
                    ths.append(float(t))
        return float(max(ths)) if ths else float(args.base_threshold)

    # build post-processed predictions
    rows = []
    for vid, g in long_df.groupby("video_id"):
        chosen = []
        chosen_probs = []
        for cls, row in g.set_index("class").iterrows():
            thr = _threshold_for(int(vid), str(cls))
            sc = float(row["score"])
            if sc >= thr:
                chosen.append(str(cls))
                chosen_probs.append(f"{sc:.6f}")
        pred_topk = ";".join(chosen)
        pred_topk_probs = ";".join(chosen_probs)
        true_labels = ";".join([c for c, r in g.groupby("class") if int(r["y_true"].iloc[0]) == 1])
        rows.append((int(vid), true_labels, pred_topk, pred_topk_probs))

    out_df = pd.DataFrame(rows, columns=["video_id","true_labels","pred_topk","pred_topk_probs"])
    out_path = base_dir / f"predictions_test_{args.model_tag}.csv"
    out_df.to_csv(out_path, index=False)

    # write audit CSV
    dp_out = (metrics_root / "fairness_v1") / f"dp_thresholds_{args.model_tag}.csv"
    pd.DataFrame(audit_rows).to_csv(dp_out, index=False)

    print(f"[done] Wrote {out_path}")
    print(f"[done] Threshold audit → {dp_out}")
    print("Next: run fairness on the post-processed file, e.g.:")
    print(f"  python -m src.analysis.02_fairness_eval --model {args.model_tag} --threshold {args.base_threshold} "
          "--namespaces race_ethnicity gender sexuality nationality hair_color age "
          "--intersections ALL2 ALL3 --min_support 100 --limit 80000")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
