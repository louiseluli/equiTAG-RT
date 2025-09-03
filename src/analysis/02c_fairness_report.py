#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02c_fairness_report.py

Purpose
-------
Create a single Markdown report that ties together:
- Accuracy metrics per model (macro/micro F1, AUROC, AUPRC; Brier; ECE)
- Fairness summaries (counts of significant gaps, top gaps per namespace)
- Intersections overview (if available)

Inputs
------
- baseline predictions: reports/metrics/baseline_v1/predictions_test_{model}.csv
- labels summary:       reports/metrics/baseline_v1/labels_summary.csv
- fairness artifacts:   reports/metrics/fairness_v1/*.csv

Outputs
-------
- reports/metrics/fairness_v1/markdown/report_{models}.md

CLI
---
python -m src.analysis.02c_fairness_report \
  --models lr rf --top_n 10 --alpha 0.05
"""

from __future__ import annotations
import argparse
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import math
import numpy as np
import pandas as pd

from src.utils.config_loader import (
    load_config as load_project_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)

# -----------------------------
# Small metrics helpers (no sklearn)
# -----------------------------

def _f1_from_counts(tp: int, fp: int, fn: int) -> float:
    p = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    r = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return (2*p*r)/(p+r) if (p+r) > 0 else 0.0

def _auc_mann_whitney(y_true: np.ndarray, scores: np.ndarray) -> float:
    """AUROC via Mann–Whitney U. Ties handled by average ranks."""
    y = y_true.astype(int)
    n1 = int(y.sum())
    n0 = int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    # rank scores ascending; average ranks for ties
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    i = 0
    while i < len(scores):
        j = i
        while j + 1 < len(scores) and scores[order[j+1]] == scores[order[i]]:
            j += 1
        # average rank for ties (1-based ranks)
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j+1):
            ranks[order[k]] = avg_rank
        i = j + 1
    # sum ranks of positives
    s_pos = ranks[y == 1].sum()
    auc = (s_pos - n1 * (n1 + 1) / 2.0) / (n1 * n0)
    return float(auc)

def _average_precision(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Simple AP (area under PR) using precision at distinct thresholds."""
    y = y_true.astype(int)
    if y.sum() == 0:
        return float("nan")
    order = np.argsort(-scores, kind="mergesort")
    y_sorted = y[order]
    tp = 0
    fp = 0
    precisions = []
    recalls = []
    total_pos = int(y.sum())
    last_score = None
    for i, yi in enumerate(y_sorted, start=1):
        # threshold changes at every position (because scores sorted)
        if yi == 1:
            tp += 1
        else:
            fp += 1
        precisions.append(tp / (tp + fp))
        recalls.append(tp / total_pos)
    # integrate precision-recall with step rule
    ap = 0.0
    prev_r = 0.0
    for p, r in zip(precisions, recalls):
        ap += p * (r - prev_r)
        prev_r = r
    return float(ap)

def _brier_score(y_true: np.ndarray, scores: np.ndarray) -> float:
    y = y_true.astype(float)
    p = scores.astype(float)
    return float(np.mean((p - y)**2))

def _ece(y_true: np.ndarray, scores: np.ndarray, n_bins: int = 10) -> float:
    """Expected Calibration Error (equal-width bins in [0,1])."""
    if len(scores) == 0:
        return float("nan")
    bins = np.linspace(0.0, 1.0, n_bins+1)
    indices = np.digitize(scores, bins) - 1
    ece = 0.0
    total = len(scores)
    for b in range(n_bins):
        mask = (indices == b)
        if not np.any(mask):
            continue
        conf = np.mean(scores[mask])
        acc = np.mean(y_true[mask])
        w = np.mean(mask)
        ece += w * abs(conf - acc)
    return float(ece)

# -----------------------------
# Predictions -> long form
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

def _accuracy_summary(long_df: pd.DataFrame, threshold: float = 0.5) -> Dict[str, float]:
    """Compute macro/micro F1, macro AUROC/AUPRC, Brier, ECE (overall across class-video pairs)."""
    # overall arrays
    y_all = long_df["y_true"].values.astype(int)
    s_all = long_df["score"].values.astype(float)

    # Brier/ECE overall
    brier = _brier_score(y_all, s_all)
    ece   = _ece(y_all, s_all, n_bins=10)

    # per-class metrics
    macro_f1 = []
    aurocs = []
    auprcs = []
    tp_sum=fp_sum=fn_sum=0

    for c, g in long_df.groupby("class"):
        y = g["y_true"].values.astype(int)
        s = g["score"].values.astype(float)
        # F1 at threshold
        yhat = (s >= threshold).astype(int)
        tp = int(((y==1) & (yhat==1)).sum())
        fp = int(((y==0) & (yhat==1)).sum())
        fn = int(((y==1) & (yhat==0)).sum())
        macro_f1.append(_f1_from_counts(tp, fp, fn))
        tp_sum += tp; fp_sum += fp; fn_sum += fn
        # AUROC/AUPRC
        au = _auc_mann_whitney(y, s)
        ap = _average_precision(y, s)
        if not math.isnan(au): aurocs.append(au)
        if not math.isnan(ap): auprcs.append(ap)

    macro_f1_val = float(np.mean(macro_f1)) if macro_f1 else float("nan")
    micro_f1_val = _f1_from_counts(tp_sum, fp_sum, fn_sum)
    macro_auroc  = float(np.mean(aurocs)) if aurocs else float("nan")
    macro_auprc  = float(np.mean(auprcs)) if auprcs else float("nan")

    return {
        "macro_f1@0.5": macro_f1_val,
        "micro_f1@0.5": micro_f1_val,
        "macro_auroc": macro_auroc,
        "macro_auprc": macro_auprc,
        "brier": brier,
        "ece": ece,
    }

# -----------------------------
# Fairness reading/summaries
# -----------------------------

def _safe_read_csv(p: Path) -> Optional[pd.DataFrame]:
    try:
        if p.exists():
            return pd.read_csv(p)
    except Exception:
        pass
    return None

def _fairness_namespace_summaries(fair_dir: Path, model: str, alpha: float) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Return summary_{model}.csv + dict(namespace->details df)."""
    summary = _safe_read_csv(fair_dir / f"summary_{model}.csv")
    ns_map: Dict[str, pd.DataFrame] = {}
    for p in sorted(fair_dir.glob(f"details_{model}_*.csv")):
        ns = p.stem.split(f"details_{model}_", 1)[-1]
        df = _safe_read_csv(p)
        if df is not None and not df.empty:
            ns_map[ns] = df
    # add counts of significant gaps by metric per namespace
    # (Holm-adjusted p-values)
    sig_rows = []
    for ns, df in ns_map.items():
        for m, col in [("DP","p_dp_adj"),("EO","p_eo_adj"),("FPR","p_fpr_adj")]:
            if col in df.columns:
                n_sig = int((df[col] < alpha).sum())
            else:
                n_sig = 0
            sig_rows.append({"namespace": ns, "metric": m, "n_significant": n_sig})
    sig = pd.DataFrame(sig_rows)
    return summary, ns_map

def _fairness_intersections(fair_dir: Path, model: str, alpha: float) -> Dict[str, Dict[str,int]]:
    """Return {combo_key: {'DP':n, 'EO':n, 'FPR':n}} counts of significant gaps across all intersection files."""
    out: Dict[str, Dict[str,int]] = {}
    for p in sorted(fair_dir.glob(f"details_intersections_{model}_*.csv")):
        combo = p.stem.split(f"details_intersections_{model}_",1)[-1]
        df = _safe_read_csv(p)
        if df is None or df.empty:
            continue
        counts = {}
        counts["DP"]  = int((df.get("p_dp_adj", pd.Series([]))  < alpha).sum())
        counts["EO"]  = int((df.get("p_eo_adj", pd.Series([]))  < alpha).sum())
        counts["FPR"] = int((df.get("p_fpr_adj", pd.Series([])) < alpha).sum())
        out[combo] = counts
    return out

def _top_gaps_table(df_ns: pd.DataFrame, metric_col: str, top_n: int) -> pd.DataFrame:
    d = df_ns.copy()
    if metric_col not in d.columns:
        return pd.DataFrame()
    d["abs"] = d[metric_col].abs()
    d = d.sort_values(["abs","n_sub"], ascending=[False, False]).head(top_n)
    keep_cols = ["class","subgroup",metric_col,"n_sub"]
    if f"p_{metric_col.split('_')[0]}_adj" in d.columns:  # p_dp_adj, p_eo_adj, p_fpr_adj
        keep_cols.append(f"p_{metric_col.split('_')[0]}_adj")
    return d[keep_cols]

# -----------------------------
# Markdown rendering
# -----------------------------

def _fmt(x: float, nd=3) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "NA"
    return f"{x:.{nd}f}"

def _df_to_md_table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_(no rows)_\n"
    cols = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"]*len(cols)) + "|")
    for r in df.itertuples(index=False, name=None):
        cells = []
        for v in r:
            if isinstance(v, float):
                cells.append(_fmt(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"

# -----------------------------
# Main
# -----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate Markdown fairness report with accuracy × fairness dashboard.")
    ap.add_argument("--models", nargs="+", required=True, help="List of models to summarize, e.g., lr rf")
    ap.add_argument("--alpha", type=float, default=0.05, help="Holm-adjusted significance level.")
    ap.add_argument("--top_n", type=int, default=10, help="Top-N gaps per namespace/metric to display.")
    args = ap.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="Fairness report v1")

    metrics_root = cfg.paths.metrics
    base_dir = metrics_root / "baseline_v1"
    fair_dir = metrics_root / "fairness_v1"
    out_md = fair_dir / "markdown" / f"report_{'_'.join(args.models)}.md"

    md: List[str] = []
    md.append("# Fairness × Accuracy Report\n")
    md.append(f"_Models:_ **{', '.join(args.models)}**  \n")
    md.append(f"_Significance (Holm-adj):_ α = **{args.alpha}**  \n")
    md.append("\n---\n")

    # ---------- ACCURACY ----------
    md.append("## Accuracy Summary\n")
    labels_path = base_dir / "labels_summary.csv"
    classes = _read_labels_summary(labels_path)
    acc_rows = []
    for m in args.models:
        preds_csv = base_dir / f"predictions_test_{m}.csv"
        if not preds_csv.exists():
            continue
        long_df = _preds_to_long(preds_csv, classes)
        acc = _accuracy_summary(long_df, threshold=0.5)
        acc_rows.append({"model": m, **acc})
    if acc_rows:
        acc_df = pd.DataFrame(acc_rows)
        md.append(_df_to_md_table(acc_df))
    else:
        md.append("_No predictions found; skipping accuracy._\n")
    md.append("\n---\n")

    # ---------- FAIRNESS ----------
    md.append("## Fairness Summary (Subgroups)\n")
    for m in args.models:
        md.append(f"### Model: `{m}`\n")
        summary, ns_map = _fairness_namespace_summaries(fair_dir, m, args.alpha)

        # Counts of significant gaps per namespace
        sig_rows = []
        for ns, df in ns_map.items():
            for met, col in [("DP","p_dp_adj"),("EO","p_eo_adj"),("FPR","p_fpr_adj")]:
                n_sig = int((df.get(col, pd.Series([])) < args.alpha).sum())
                sig_rows.append({"namespace": ns, "metric": met, "n_significant": n_sig})
        if sig_rows:
            md.append("**Number of significant subgroup gaps by metric (Holm-adj):**\n\n")
            md.append(_df_to_md_table(pd.DataFrame(sig_rows)))
        else:
            md.append("_(No subgroup details found.)_\n")

        # Top gaps per namespace
        for ns, df in ns_map.items():
            md.append(f"\n#### {ns}\n")
            for mcol, nice in [("dp_diff","Δ Demographic Parity"),
                               ("eo_diff","Δ Equal Opportunity"),
                               ("fpr_diff","Δ False Positive Rate")]:
                top_tbl = _top_gaps_table(df, mcol, args.top_n)
                if top_tbl.empty:
                    md.append(f"- _No rows for {nice}_\n")
                else:
                    md.append(f"**Top {min(args.top_n, len(top_tbl))} by {nice}:**\n\n")
                    md.append(_df_to_md_table(top_tbl))
        md.append("\n")

    # ---------- INTERSECTIONS ----------
    md.append("\n---\n")
    md.append("## Intersections Overview\n")
    for m in args.models:
        md.append(f"### Model: `{m}`\n")
        counts = _fairness_intersections(fair_dir, m, args.alpha)
        if not counts:
            md.append("_(No intersection files found.)_\n")
            continue
        rows = []
        for combo, d in counts.items():
            rows.append({"combo": combo, "DP_sig": d.get("DP",0), "EO_sig": d.get("EO",0), "FPR_sig": d.get("FPR",0)})
        md.append(_df_to_md_table(pd.DataFrame(rows)))
        md.append("\n")

    # write
    out_md.write_text("\n".join(md), encoding="utf-8")
    print(f"[done] Wrote {out_md}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
