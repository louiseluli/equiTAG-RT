"""
src/analysis/02_fairness_eval.py

Purpose
-------
Compute subgroup (and optional intersectional) fairness metrics for multi-label
category prediction:
- Demographic Parity Difference (DP): P(ŷ=1 | group) - P(ŷ=1 | all)
- Equal Opportunity Difference (EO): TPR(group) - TPR(all), conditioning on y=1
- False Positive Rate Difference (FPR): FPR(group) - FPR(all), conditioning on y=0

For each (namespace, subgroup, class), we report:
- counts (n_sub, n_pos, n_y1, n_tp, n_y0, n_fp),
- rates (PR, TPR, FPR),
- differences vs overall,
- two-proportion tests with Holm–Bonferroni p-adjustment across subgroups within
  a (namespace, class, metric).

The script is deterministic and emits CSV + Markdown summaries suitable for your dissertation.

Inputs
------
- Predictions (from baselines):
  reports/metrics/baseline_v1/predictions_test_{lr|rf}.csv
    columns: video_id, true_labels, pred_topk, pred_topk_probs
- Labels summary:
  reports/metrics/baseline_v1/labels_summary.csv  (category,count)  -- class list
- SQLite DB (to fetch titles+tags for subgroup membership):
  videos, video_tags (temp aggregation), restricted to the video_ids in predictions
- Lexicon:
  config/protected_terms.json (compiled with src.utils.lexicon_loader)

Outputs
-------
reports/metrics/fairness_v1/
  - summary_{model}.csv
  - details_{model}_{namespace}.csv
  - markdown/summary_{model}.md

CLI
---
Example (your run):
python -m src.analysis.02_fairness_eval \
  --threshold 0.5 \
  --namespaces race_ethnicity gender sexuality nationality hair_color age

Notes
-----
- Threshold applies to TOP-K probs available in predictions CSV: a class is ŷ=1
  if it appears in top-k with prob >= threshold.
- We filter subgroups by minimum support (--min_support) to avoid noisy estimates.
- All merges use plain columns (never index names), preventing ambiguity errors.
"""

from __future__ import annotations
import argparse
import csv
import math
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

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

# ---------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------

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
    """
    Fetch title + aggregated tags for the given video_ids (in chunks to avoid
    SQLite parameter limits). Returns DataFrame [video_id, title, tags].
    """
    out: List[pd.DataFrame] = []
    ids = list(map(int, video_ids))
    for i in range(0, len(ids), chunk):
        sub = ids[i:i+chunk]
        q = f"""
            SELECT v.video_id, COALESCE(v.title,'') AS title, COALESCE(t.tags,'') AS tags
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
    df["title"] = df["title"].fillna("").astype(str)
    df["tags"] = df["tags"].fillna("").astype(str)
    return df

# ---------------------------------------------------------------------
# Predictions I/O
# ---------------------------------------------------------------------

def _read_labels_summary(path: Path) -> List[str]:
    df = pd.read_csv(path)
    return df["category"].tolist()

def _read_predictions(path: Path, classes: List[str], threshold: float) -> pd.DataFrame:
    """
    Read predictions CSV and convert to per-class binary GT and ŷ using the threshold.
    Returns a long-form DataFrame with columns:
      video_id, class, y_true (0/1), y_pred (0/1), p (prob if present else 0)
    """
    df = pd.read_csv(path)
    df["video_id"] = df["video_id"].astype(int)

    # Parse "true_labels", "pred_topk", "pred_topk_probs"
    def _split_semicol(s: str) -> List[str]:
        if isinstance(s, float) and math.isnan(s):
            return []
        s = str(s).strip()
        return [] if s == "" else s.split(";")

    df["true_labels_list"] = df["true_labels"].apply(_split_semicol)
    df["pred_labels_list"] = df["pred_topk"].apply(_split_semicol)
    df["pred_probs_list"]  = df["pred_topk_probs"].apply(lambda s: [float(x) for x in _split_semicol(s)])

    # Build long-form rows
    rows: List[Tuple[int,str,int,int,float]] = []
    for vid, t_lbls, p_lbls, p_probs in df[["video_id","true_labels_list","pred_labels_list","pred_probs_list"]].itertuples(index=False):
        p_map = {lab: prob for lab, prob in zip(p_lbls, p_probs)}
        t_set = set(t_lbls)
        for c in classes:
            y_true = 1 if c in t_set else 0
            pr = p_map.get(c, 0.0)
            y_pred = 1 if pr >= threshold else 0
            rows.append((vid, c, y_true, y_pred, pr))
    long_df = pd.DataFrame(rows, columns=["video_id","class","y_true","y_pred","p"])
    return long_df

# ---------------------------------------------------------------------
# Lexicon matching (subgroup membership)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class Membership:
    video_id: int
    ns2sgs: Dict[str, Set[str]]  # namespace -> set(subgroups) matched in title OR tags

def _compile_lexicon(lex_path: Path, boundary: str = "word") -> ProtectedLexicon:
    return ProtectedLexicon.from_json(lex_path).compile(boundary=boundary)

def _match_membership(text_df: pd.DataFrame, lex: ProtectedLexicon, namespaces: List[str]) -> Dict[int, Dict[str, Set[str]]]:
    """
    For each video_id in text_df, return membership per requested namespaces
    (union over title and tags). {vid: {namespace: {sg,...}, ...}}
    """
    out: Dict[int, Dict[str, Set[str]]] = {}
    for row in text_df.itertuples(index=False):
        vid = int(row.video_id)
        title = str(row.title).lower()
        tags  = str(row.tags).lower()
        ns2: Dict[str, Set[str]] = {}
        for ns in namespaces:
            if ns not in lex.compiled:
                continue
            s: Set[str] = set()
            for sg, cg in lex.compiled[ns].groups.items():
                if any(p.search(title) for p in cg.patterns) or any(p.search(tags) for p in cg.patterns):
                    s.add(sg)
            if s:
                ns2[ns] = s
        out[vid] = ns2
    return out

# ---------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------

def _safe_div(num: int, den: int) -> float:
    return (num / den) if den > 0 else float("nan")

def _two_prop_pvalue(k1: int, n1: int, k2: int, n2: int) -> float:
    """
    Two-sided z-test for difference in proportions.
    """
    if n1 == 0 or n2 == 0:
        return float("nan")
    p1 = k1 / n1
    p2 = k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1/n1 + 1/n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    # two-sided
    from math import erf, sqrt
    # Phi(z) via erf
    phi = 0.5 * (1 + erf(z / math.sqrt(2)))
    p_two = 2 * (1 - phi) if z >= 0 else 2 * phi
    return min(max(p_two, 0.0), 1.0)

def _holm_bonferroni(pvals: List[float]) -> List[float]:
    """
    Holm–Bonferroni step-down (more powerful than Bonferroni).
    """
    m = len(pvals)
    idx = np.argsort(pvals)  # ascending
    adj = np.empty(m, dtype=float)
    running_max = 0.0
    for rank, i in enumerate(idx, start=1):
        adj_i = (m - rank + 1) * pvals[i]
        adj[i] = adj_i
    # enforce monotonicity
    ordered = adj[idx]
    for i in range(1, m):
        ordered[i] = max(ordered[i], ordered[i-1])
    # put back into original order and clip
    adj[idx] = ordered
    return [float(min(1.0, max(0.0, x))) for x in adj.tolist()]

# ---------------------------------------------------------------------
# Fairness computation
# ---------------------------------------------------------------------

def _per_group_counts(df_ns: pd.DataFrame, overall_mask: pd.Series) -> pd.DataFrame:
    """
    df_ns columns: ['video_id','class','y_true','y_pred','in_group'] (bool)
    Returns tidy table per subgroup after groupby with **reset_index** to avoid
    'subgroup' as both index and column.
    """
    grp = df_ns.groupby("subgroup", as_index=False)

    # PR (all examples)
    g_all = grp.apply(lambda g: pd.Series({
        "n_sub": int(g["in_group"].sum()),
        "n_all": int(len(g)),
        "n_pred1": int((g["in_group"] & (g["y_pred"] == 1)).sum()),
        "pr_sub": _safe_div(int((g["in_group"] & (g["y_pred"] == 1)).sum()), int(g["in_group"].sum())),
        "pr_all": float((df_ns["y_pred"] == 1).mean()),  # overall within this (namespace,class) slice
    })).reset_index(drop=True)

    # EO (condition y=1)
    mask_y1 = df_ns["y_true"] == 1
    g_y1 = grp.apply(lambda g: pd.Series({
        "n_y1_sub": int((g["in_group"] & (g["y_true"] == 1)).sum()),
        "n_tp": int((g["in_group"] & (g["y_true"] == 1) & (g["y_pred"] == 1)).sum()),
        "tpr_sub": _safe_div(int((g["in_group"] & (g["y_true"] == 1) & (g["y_pred"] == 1)).sum()),
                             int((g["in_group"] & (g["y_true"] == 1)).sum())),
        "tpr_all": _safe_div(int(((df_ns["y_true"] == 1) & (df_ns["y_pred"] == 1)).sum()),
                             int((df_ns["y_true"] == 1).sum())),
    })).reset_index(drop=True)

    # FPR (condition y=0)
    mask_y0 = df_ns["y_true"] == 0
    g_y0 = grp.apply(lambda g: pd.Series({
        "n_y0_sub": int((g["in_group"] & (g["y_true"] == 0)).sum()),
        "n_fp": int((g["in_group"] & (g["y_true"] == 0) & (g["y_pred"] == 1)).sum()),
        "fpr_sub": _safe_div(int((g["in_group"] & (g["y_true"] == 0) & (g["y_pred"] == 1)).sum()),
                             int((g["in_group"] & (g["y_true"] == 0)).sum())),
        "fpr_all": _safe_div(int(((df_ns["y_true"] == 0) & (df_ns["y_pred"] == 1)).sum()),
                             int((df_ns["y_true"] == 0).sum())),
    })).reset_index(drop=True)

    # Merge on column 'subgroup' (no index ambiguity)
    out = g_all.merge(g_y1, on="subgroup", how="left").merge(g_y0, on="subgroup", how="left")
    # Differences
    out["dp_diff"]  = out["pr_sub"]  - out["pr_all"]
    out["eo_diff"]  = out["tpr_sub"] - out["tpr_all"]
    out["fpr_diff"] = out["fpr_sub"] - out["fpr_all"]
    return out

def _attach_pvalues_and_adjust(tbl: pd.DataFrame) -> pd.DataFrame:
    """
    Attach two-proportion p-values and Holm-adjusted p-values for each metric
    across all subgroups in this (namespace, class) slice.
    """
    # DP p-values: compare subgroup vs complement (not 'all') to be conservative
    p_dp: List[float] = []
    p_eo: List[float] = []
    p_fpr: List[float] = []
    for r in tbl.itertuples(index=False):
        # DP
        k1 = int(r.n_pred1)           # successes in subgroup
        n1 = int(r.n_sub)             # subgroup size
        k2 = int(tbl["n_pred1"].sum() - k1)  # successes outside
        n2 = int(tbl["n_sub"].sum() - n1)    # outside size
        p_dp.append(_two_prop_pvalue(k1, n1, k2, n2))

        # EO (y=1)
        k1 = int(r.n_tp)
        n1 = int(r.n_y1_sub)
        k2 = int(tbl["n_tp"].sum() - k1)
        n2 = int(tbl["n_y1_sub"].sum() - n1)
        p_eo.append(_two_prop_pvalue(k1, n1, k2, n2))

        # FPR (y=0)
        k1 = int(r.n_fp)
        n1 = int(r.n_y0_sub)
        k2 = int(tbl["n_fp"].sum() - k1)
        n2 = int(tbl["n_y0_sub"].sum() - n1)
        p_fpr.append(_two_prop_pvalue(k1, n1, k2, n2))

    tbl = tbl.copy()
    tbl["p_dp"]  = p_dp
    tbl["p_eo"]  = p_eo
    tbl["p_fpr"] = p_fpr

    # Holm–Bonferroni within-metric adjustment across subgroups
    tbl["p_dp_adj"]  = _holm_bonferroni(tbl["p_dp"].fillna(1.0).tolist())
    tbl["p_eo_adj"]  = _holm_bonferroni(tbl["p_eo"].fillna(1.0).tolist())
    tbl["p_fpr_adj"] = _holm_bonferroni(tbl["p_fpr"].fillna(1.0).tolist())
    return tbl

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Fairness evaluation (DP/EO/FPR) per subgroup with Holm–Bonferroni.")
    ap.add_argument("--model", type=str, default="lr", choices=["lr", "rf"], help="Which predictions file to use.")
    ap.add_argument("--threshold", type=float, default=0.5, help="Threshold on top-k probabilities to set ŷ=1.")
    ap.add_argument(
        "--namespaces",
        nargs="+",
        default=["race_ethnicity", "gender", "sexuality", "nationality", "hair_color", "age"],
        help="Namespaces to evaluate from the lexicon."
    )
    ap.add_argument("--min_support", type=int, default=100, help="Minimum subgroup size (n_sub) to report.")
    ap.add_argument(
        "--limit", 
        type=int, 
        default=None, 
        help="Optional: only process first N video_ids in predictions (for smoke tests)."
    )
    args = ap.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="Fairness eval v1")

    metrics_root = cfg.paths.metrics
    base_dir = metrics_root / "baseline_v1"
    fair_dir = metrics_root / "fairness_v1"
    (fair_dir / "markdown").mkdir(parents=True, exist_ok=True)

    # Inputs
    labels_path = base_dir / "labels_summary.csv"
    classes = _read_labels_summary(labels_path)

    preds_path = base_dir / f"predictions_test_{args.model}.csv"
    if not preds_path.exists():
        raise FileNotFoundError(f"Predictions not found: {preds_path}")

    long_df = _read_predictions(preds_path, classes, args.threshold)
    
    # Restrict to first N video_ids if requested
    if args.limit:
        keep_vids = long_df["video_id"].drop_duplicates().head(int(args.limit))
        long_df = long_df[long_df["video_id"].isin(keep_vids)]

    # DB text for membership
    conn = _connect(cfg.paths.database)
    _ensure_temp_tag_agg(conn)
    vids = long_df["video_id"].drop_duplicates().tolist()
    text_df = _fetch_text_for_ids(conn, vids)

    # Lexicon + membership
    lex = _compile_lexicon(cfg.paths.root / DEFAULT_LEXICON_REL, boundary="word")
    namespaces = [ns for ns in args.namespaces if ns in lex.compiled]
    mem = _match_membership(text_df, lex, namespaces)  # {vid: {ns: {sg}}}

    # Attach membership per namespace → explode per subgroup
    # We'll loop per namespace to keep memory small and produce per-namespace details
    summary_rows: List[List] = []
    md_lines: List[str] = ["# Fairness Summary\n", f"*Model:* **{args.model.upper()}**, *threshold:* **{args.threshold}**\n\n"]

    for ns in namespaces:
        # For each class, build a tidy frame with 'in_group' mask per subgroup
        ns_rows: List[pd.DataFrame] = []
        
        for c in classes:
            df_c = long_df[long_df["class"] == c].copy()
            if df_c.empty:
                continue

            # For each video, what subgroups (set) under this namespace?
            # Explode into one row per subgroup
            sg_rows: List[Tuple[int, str, int, int]] = []  # (video_id, subgroup, y_true, y_pred)
            
            for r in df_c[["video_id", "y_true", "y_pred"]].itertuples(index=False):
                vid = int(r.video_id)
                sgs = mem.get(vid, {}).get(ns, set())
                if not sgs:
                    # keep a 'no_match' bucket? We skip; fairness focuses on named groups
                    continue
                for sg in sgs:
                    sg_rows.append((vid, sg, int(r.y_true), int(r.y_pred)))
            
            if not sg_rows:
                continue

            df_ns = pd.DataFrame(sg_rows, columns=["video_id", "subgroup", "y_true", "y_pred"])
            # Add in_group flag (always True here), and a complete base including non-members as well?
            # We evaluate subgroup vs overall using totals from df_c.
            df_ns["in_group"] = True

            # Prepare per-group counts and rates; ALWAYS reset_index
            tbl = _per_group_counts(df_ns, overall_mask=(df_c["y_true"] == df_c["y_true"]))  # placeholder; overall computed inside
            
            # Filter by support
            tbl = tbl[tbl["n_sub"] >= int(args.min_support)].reset_index(drop=True)
            if tbl.empty:
                continue

            # Attach p-values + Holm adjustment
            tbl = _attach_pvalues_and_adjust(tbl)
            tbl.insert(0, "class", c)
            tbl.insert(0, "namespace", ns)
            ns_rows.append(tbl)

        if not ns_rows:
            continue

        ns_tbl = pd.concat(ns_rows, ignore_index=True)

        # Save detailed table for the namespace
        out_ns = fair_dir / f"details_{args.model}_{ns}.csv"
        ns_tbl.to_csv(out_ns, index=False)

        # Add to summary (worst gaps per metric for top exposure)
        # pick subgroup with largest absolute diff per class and metric
        for c in sorted(ns_tbl["class"].unique()):
            sub_c = ns_tbl[ns_tbl["class"] == c].copy()
            if sub_c.empty:
                continue
            
            def _pick(metric: str) -> Tuple[str, float, float]:
                s = sub_c.iloc[np.argmax(np.abs(sub_c[metric].fillna(0.0)).values)]
                return (str(s.subgroup), float(s[metric]), float(s.get(metric.replace("_diff", "_sub"), np.nan)))
            
            try:
                g_dp = _pick("dp_diff")
                g_eo = _pick("eo_diff")
                g_fp = _pick("fpr_diff")
            except Exception:
                g_dp = ("", float("nan"), float("nan"))
                g_eo = ("", float("nan"), float("nan"))
                g_fp = ("", float("nan"), float("nan"))
            
            summary_rows.append([ns, c, *g_dp, *g_eo, *g_fp])

        # Markdown section
        md_lines.append(f"## {ns}\n\n")
        md_lines.append(f"- Details: `{out_ns}`\n")
        
        # Top 3 absolute DP gaps across classes
        top_dp = ns_tbl.loc[:, ["class","subgroup","dp_diff","p_dp_adj","n_sub"]].copy()
        top_dp["abs_gap"] = top_dp["dp_diff"].abs()
        top_dp = top_dp.sort_values(["abs_gap","n_sub"], ascending=[False, False]).head(5)
        # Use tuple unpacking to avoid reserved-name attribute issues
        for cls, subgroup, dp_diff, p_adj, n_sub in top_dp[["class","subgroup","dp_diff","p_dp_adj","n_sub"]].itertuples(index=False, name=None):
            md_lines.append(f"- **DP gap** {dp_diff:+.3f} for `{subgroup}` in class `{cls}` (n={n_sub}); Holm-adj p={p_adj:.3f}")
        md_lines.append("\n")
  

    # Global summary CSV
    if summary_rows:
        sum_df = pd.DataFrame(
            summary_rows,
            columns=[
                "namespace", "class",
                "dp_subgroup", "dp_diff", "dp_sub_rate",
                "eo_subgroup", "eo_diff", "eo_sub_tpr",
                "fpr_subgroup", "fpr_diff", "fpr_sub_fpr",
            ]
        )
        sum_df.to_csv(fair_dir / f"summary_{args.model}.csv", index=False)

    # Markdown
    with (fair_dir / "markdown" / f"summary_{args.model}.md").open("w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("[done] Fairness evaluation complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
