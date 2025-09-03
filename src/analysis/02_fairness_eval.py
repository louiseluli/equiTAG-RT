"""
src/analysis/02_fairness_eval.py

Purpose
-------
Compute subgroup and (optional) intersectional fairness metrics for multi-label
category prediction:
- Demographic Parity Difference (DP): P(ŷ=1 | group) - P(ŷ=1 | all)
- Equal Opportunity Difference (EO): TPR(group) - TPR(all), conditioning on y=1
- False Positive Rate Difference (FPR): FPR(group) - FPR(all), conditioning on y=0

For each (namespace, subgroup, class) — and for specified intersections —
we report:
- counts (n_sub, n_pred1, n_y1, n_tp, n_y0, n_fp),
- rates (PR, TPR, FPR),
- differences vs overall,
- two-proportion tests with Holm–Bonferroni p-adjustment across subgroups within
  a (namespace, class, metric).

Additionally, we compute engagement comparisons (if available in DB):
- views, rating, ratings — group vs complement (Welch's t on log1p(views), and
  deltas for rating/ratings), with Holm–Bonferroni correction within namespace.

Inputs
------
- Predictions (from baselines):
  reports/metrics/baseline_v1/predictions_test_{lr|rf}.csv
    columns: video_id, true_labels, pred_topk, pred_topk_probs
- Labels summary:
  reports/metrics/baseline_v1/labels_summary.csv  (category,count)  -- class list
- SQLite DB:
  videos(video_id, title, views, rating, ratings), video_tags(video_id, tag)
  (title + aggregated tags used for lexicon matching; engagement columns for comparisons)
- Lexicon:
  config/protected_terms.json (compiled with src.utils.lexicon_loader)

Outputs
-------
reports/metrics/fairness_v1/
  - summary_{model}.csv
  - details_{model}_{namespace}.csv
  - engagement_{model}_{namespace}.csv
  - details_intersections_{model}_{<comboKey>}.csv           # comboKey like gender*race_ethnicity
  - compare_intersections_vs_marginals_{model}_{<comboKey>}.csv
  - engagement_intersections_{model}_{<comboKey>}.csv
  - markdown/summary_{model}.md
  - summary_intersections_{model}.csv

CLI
---
Example:
python -m src.analysis.02_fairness_eval \
  --model lr \
  --threshold 0.5 \
  --namespaces race_ethnicity gender sexuality nationality hair_color age \
  --intersections ALL2 ALL3 \
  --min_support 100 \
  --limit 80000

Notes
-----
- Threshold applies to TOP-K probs available in predictions CSV: a class is ŷ=1
  if it appears in top-k with prob >= threshold.
- We filter subgroups/intersections by minimum support (--min_support) to avoid
  noisy estimates.
- All merges use plain columns (never index names), preventing ambiguity errors.
"""

from __future__ import annotations
import argparse
import csv
import math
import sqlite3
from dataclasses import dataclass
from itertools import combinations, product
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

def _fetch_text_and_meta_for_ids(conn: sqlite3.Connection, video_ids: Sequence[int], chunk: int = 800) -> pd.DataFrame:
    """
    Fetch title + aggregated tags + engagement (views, rating, ratings)
    for given video_ids. Returns DataFrame columns:
    [video_id, title, tags, views, rating, ratings]
    """
    out: List[pd.DataFrame] = []
    ids = list(map(int, video_ids))
    for i in range(0, len(ids), chunk):
        sub = ids[i:i+chunk]
        q = f"""
            SELECT v.video_id,
                   COALESCE(v.title,'')   AS title,
                   COALESCE(t.tags,'')    AS tags,
                   COALESCE(v.views,0)    AS views,
                   v.rating               AS rating,
                   COALESCE(v.ratings,0)  AS ratings
            FROM videos v
            LEFT JOIN temp_vt_agg t ON t.video_id = v.video_id
            WHERE v.video_id IN ({",".join(str(x) for x in sub)})
        """
        rows = conn.execute(q).fetchall()
        if rows:
            out.append(pd.DataFrame(rows, columns=rows[0].keys()))
    if not out:
        return pd.DataFrame(columns=["video_id","title","tags","views","rating","ratings"])
    df = pd.concat(out, ignore_index=True)
    df["title"] = df["title"].fillna("").astype(str)
    df["tags"] = df["tags"].fillna("").astype(str)
    df["views"] = pd.to_numeric(df["views"], errors="coerce").fillna(0).astype(np.int64)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")  # keep NaN
    df["ratings"] = pd.to_numeric(df["ratings"], errors="coerce").fillna(0).astype(np.int64)
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

    def _split_semicol(s: str) -> List[str]:
        if isinstance(s, float) and math.isnan(s):
            return []
        s = str(s).strip()
        return [] if s == "" else s.split(";")

    df["true_labels_list"] = df["true_labels"].apply(_split_semicol)
    df["pred_labels_list"] = df["pred_topk"].apply(_split_semicol)
    df["pred_probs_list"]  = df["pred_topk_probs"].apply(lambda s: [float(x) for x in _split_semicol(s)])

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

def _parse_intersections(tokens: List[str], namespaces: List[str]) -> List[Tuple[str, ...]]:
    """
    Parse --intersections. Supports:
      - 'ALL2' => all 2-way combos among `namespaces`
      - 'ALL3' => all 3-way combos among `namespaces`
      - explicit patterns with '*' delimiter, e.g., 'gender*race_ethnicity'
    Returns a list of tuples of namespace names, e.g., [('gender','race_ethnicity'), ...]
    """
    combos: Set[Tuple[str, ...]] = set()
    toks = [t.strip() for t in (tokens or []) if str(t).strip()]
    if any(t.upper() == "ALL2" for t in toks):
        combos.update(tuple(sorted(c)) for c in combinations(namespaces, 2))
    if any(t.upper() == "ALL3" for t in toks):
        if len(namespaces) >= 3:
            combos.update(tuple(sorted(c)) for c in combinations(namespaces, 3))
    for t in toks:
        if t.upper() in {"ALL2","ALL3"}:
            continue
        parts = tuple(sorted(p.strip() for p in t.split("*") if p.strip()))
        if len(parts) >= 2 and all(p in namespaces for p in parts):
            combos.add(parts)
    return sorted(combos)

def _iter_intersection_rows_for_class(
    df_c: pd.DataFrame,
    mem: Dict[int, Dict[str, Set[str]]],
    combo: Tuple[str, ...],
) -> Iterable[Tuple[int, str, int, int]]:
    """
    For one class `c`, yield rows (video_id, intersection_label, y_true, y_pred)
    for each video that matches >=1 subgroup in every namespace in `combo`.
    The label format is: "ns1=sg1 & ns2=sg2 [& ns3=sg3]".
    """
    for r in df_c[["video_id", "y_true", "y_pred"]].itertuples(index=False):
        vid = int(r.video_id)
        ms = mem.get(vid, {})
        sets = []
        ok = True
        for ns in combo:
            s = ms.get(ns, set())
            if not s:
                ok = False
                break
            sets.append(sorted(s))
        if not ok:
            continue
        for items in product(*sets):
            parts = [f"{ns}={sg}" for ns, sg in zip(combo, items)]
            label = " & ".join(parts)
            yield (vid, label, int(r.y_true), int(r.y_pred))

# ---------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------

def _safe_div(num: int, den: int) -> float:
    return (num / den) if den > 0 else float("nan")

def _two_prop_pvalue(k1: int, n1: int, k2: int, n2: int) -> float:
    """Two-sided z-test for difference in proportions."""
    if n1 == 0 or n2 == 0:
        return float("nan")
    p1 = k1 / n1
    p2 = k2 / n2
    p = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1/n1 + 1/n2))
    if se == 0:
        return 1.0
    z = (p1 - p2) / se
    # CDF via erf
    phi = 0.5 * (1 + math.erf(z / math.sqrt(2)))
    p_two = 2 * (1 - phi) if z >= 0 else 2 * phi
    return float(min(max(p_two, 0.0), 1.0))

def _holm_bonferroni(pvals: List[float]) -> List[float]:
    """Holm–Bonferroni step-down adjustment (monotone, clipped to [0,1])."""
    m = len(pvals)
    if m == 0:
        return []
    idx = np.argsort(pvals)  # ascending
    adj = np.empty(m, dtype=float)
    for rank, i in enumerate(idx, start=1):
        adj[i] = (m - rank + 1) * (pvals[i] if not np.isnan(pvals[i]) else 1.0)
    ordered = adj[idx]
    for i in range(1, m):
        ordered[i] = max(ordered[i], ordered[i-1])
    adj[idx] = ordered
    return [float(min(1.0, max(0.0, x))) for x in adj.tolist()]

def _welch_t_pvalue(m1, s1, n1, m2, s2, n2) -> float:
    """Two-sided Welch's t-test p-value for difference in means."""
    if n1 <= 1 or n2 <= 1:
        return float("nan")
    se = math.sqrt((s1*s1)/n1 + (s2*s2)/n2)
    if se == 0:
        return 1.0
    t = (m1 - m2) / se
    # Welch-Satterthwaite dof
    v = ((s1*s1)/n1 + (s2*s2)/n2)**2 / (
        ((s1*s1)/n1)**2 / (n1 - 1) + ((s2*s2)/n2)**2 / (n2 - 1)
    )
    # approximate p from t using survival of Student's t:
    # We'll approximate via normal if v is large; else fallback to normal too (OK for large n).
    phi = 0.5 * (1 + math.erf(abs(t) / math.sqrt(2)))
    p_two = 2 * (1 - phi)
    return float(min(max(p_two, 0.0), 1.0))

# ---------------------------------------------------------------------
# Fairness computation
# ---------------------------------------------------------------------

def _per_group_counts(df_ns: pd.DataFrame) -> pd.DataFrame:
    """
    df_ns columns: ['video_id','subgroup','y_true','y_pred','in_group'] (bool)
    Returns tidy table per subgroup after groupby with reset_index to avoid
    'subgroup' being both index and column.
    """
    grp = df_ns.groupby("subgroup", as_index=False)

    # PR (all)
    g_all = grp.apply(lambda g: pd.Series({
        "n_sub": int(g["in_group"].sum()),
        "n_all": int(len(g)),
        "n_pred1": int((g["in_group"] & (g["y_pred"] == 1)).sum()),
        "pr_sub": _safe_div(int((g["in_group"] & (g["y_pred"] == 1)).sum()), int(g["in_group"].sum())),
    })).reset_index(drop=True)

    # Overall rates for this slice (same across subgroups)
    pr_all = float((df_ns["y_pred"] == 1).mean())
    tpr_all = _safe_div(int(((df_ns["y_true"] == 1) & (df_ns["y_pred"] == 1)).sum()),
                        int((df_ns["y_true"] == 1).sum()))
    fpr_all = _safe_div(int(((df_ns["y_true"] == 0) & (df_ns["y_pred"] == 1)).sum()),
                        int((df_ns["y_true"] == 0).sum()))

    # EO (y=1)
    g_y1 = grp.apply(lambda g: pd.Series({
        "n_y1_sub": int((g["in_group"] & (g["y_true"] == 1)).sum()),
        "n_tp": int((g["in_group"] & (g["y_true"] == 1) & (g["y_pred"] == 1)).sum()),
        "tpr_sub": _safe_div(int((g["in_group"] & (g["y_true"] == 1) & (g["y_pred"] == 1)).sum()),
                             int((g["in_group"] & (g["y_true"] == 1)).sum())),
    })).reset_index(drop=True)

    # FPR (y=0)
    g_y0 = grp.apply(lambda g: pd.Series({
        "n_y0_sub": int((g["in_group"] & (g["y_true"] == 0)).sum()),
        "n_fp": int((g["in_group"] & (g["y_true"] == 0) & (g["y_pred"] == 1)).sum()),
        "fpr_sub": _safe_div(int((g["in_group"] & (g["y_true"] == 0) & (g["y_pred"] == 1)).sum()),
                             int((g["in_group"] & (g["y_true"] == 0)).sum())),
    })).reset_index(drop=True)

    out = g_all.merge(g_y1, on="subgroup", how="left").merge(g_y0, on="subgroup", how="left")
    out["pr_all"] = pr_all
    out["tpr_all"] = tpr_all
    out["fpr_all"] = fpr_all
    out["dp_diff"]  = out["pr_sub"]  - out["pr_all"]
    out["eo_diff"]  = out["tpr_sub"] - out["tpr_all"]
    out["fpr_diff"] = out["fpr_sub"] - out["fpr_all"]
    return out

def _attach_pvalues_and_adjust(tbl: pd.DataFrame) -> pd.DataFrame:
    """Attach two-proportion p-values and Holm-adjusted p-values per metric."""
    p_dp: List[float] = []
    p_eo: List[float] = []
    p_fpr: List[float] = []
    for r in tbl.itertuples(index=False):
        # DP: subgroup vs complement
        k1, n1 = int(r.n_pred1), int(r.n_sub)
        k2, n2 = int(tbl["n_pred1"].sum() - k1), int(tbl["n_sub"].sum() - n1)
        p_dp.append(_two_prop_pvalue(k1, n1, k2, n2))
        # EO
        k1, n1 = int(r.n_tp), int(r.n_y1_sub)
        k2, n2 = int(tbl["n_tp"].sum() - k1), int(tbl["n_y1_sub"].sum() - n1)
        p_eo.append(_two_prop_pvalue(k1, n1, k2, n2))
        # FPR
        k1, n1 = int(r.n_fp), int(r.n_y0_sub)
        k2, n2 = int(tbl["n_fp"].sum() - k1), int(tbl["n_y0_sub"].sum() - n1)
        p_fpr.append(_two_prop_pvalue(k1, n1, k2, n2))

    tbl = tbl.copy()
    tbl["p_dp"]  = p_dp
    tbl["p_eo"]  = p_eo
    tbl["p_fpr"] = p_fpr
    tbl["p_dp_adj"]  = _holm_bonferroni(tbl["p_dp"].fillna(1.0).tolist())
    tbl["p_eo_adj"]  = _holm_bonferroni(tbl["p_eo"].fillna(1.0).tolist())
    tbl["p_fpr_adj"] = _holm_bonferroni(tbl["p_fpr"].fillna(1.0).tolist())
    return tbl

# ---------------------------------------------------------------------
# Engagement comparisons (views, rating, ratings)
# ---------------------------------------------------------------------

def _engagement_stats(group_vids: Sequence[int], all_vids: Sequence[int], meta: pd.DataFrame) -> Dict[str, float]:
    """Compute simple group vs complement differences on views/rating/ratings."""
    gset = set(int(v) for v in group_vids)
    aset = set(int(v) for v in all_vids)
    cset = aset - gset
    if not gset or not cset:
        return {
            "n_group": len(gset), "n_comp": len(cset),
            "mean_log_views_group": float("nan"), "mean_log_views_comp": float("nan"),
            "delta_mean_log_views": float("nan"), "p_log_views": float("nan"),
            "mean_rating_group": float("nan"), "mean_rating_comp": float("nan"),
            "delta_mean_rating": float("nan"),
            "mean_ratings_group": float("nan"), "mean_ratings_comp": float("nan"),
            "delta_mean_ratings": float("nan"),
        }
    m = meta.set_index("video_id")
    gv = m.loc[m.index.intersection(gset)]
    cv = m.loc[m.index.intersection(cset)]
    # log1p(views)
    glv = np.log1p(gv["views"].astype(float).values)
    clv = np.log1p(cv["views"].astype(float).values)
    m1, s1, n1 = float(np.nanmean(glv)), float(np.nanstd(glv, ddof=1)), glv.size
    m2, s2, n2 = float(np.nanmean(clv)), float(np.nanstd(clv, ddof=1)), clv.size
    p_lv = _welch_t_pvalue(m1, s1, n1, m2, s2, n2)
    # rating (NaN allowed)
    r1 = gv["rating"].astype(float).values
    r2 = cv["rating"].astype(float).values
    mr1, mr2 = float(np.nanmean(r1)), float(np.nanmean(r2))
    # ratings count
    rc1 = gv["ratings"].astype(float).values
    rc2 = cv["ratings"].astype(float).values
    mrc1, mrc2 = float(np.nanmean(rc1)), float(np.nanmean(rc2))

    return {
        "n_group": int(n1), "n_comp": int(n2),
        "mean_log_views_group": m1, "mean_log_views_comp": m2,
        "delta_mean_log_views": m1 - m2, "p_log_views": p_lv,
        "mean_rating_group": mr1, "mean_rating_comp": mr2,
        "delta_mean_rating": mr1 - mr2,
        "mean_ratings_group": mrc1, "mean_ratings_comp": mrc2,
        "delta_mean_ratings": mrc1 - mrc2,
    }

# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Fairness evaluation (DP/EO/FPR) per subgroup with Holm–Bonferroni, intersections, and engagement comparisons.")
    ap.add_argument("--model", type=str, default="lr", choices=["lr","rf"], help="Which predictions file to use.")
    ap.add_argument("--threshold", type=float, default=0.5, help="Threshold on top-k probabilities to set ŷ=1.")
    ap.add_argument("--namespaces", nargs="+",
                    default=["race_ethnicity","gender","sexuality","nationality","hair_color","age"],
                    help="Namespaces to evaluate from the lexicon.")
    ap.add_argument("--min_support", type=int, default=100, help="Minimum subgroup size (n_sub) to report.")
    ap.add_argument("--limit", type=int, default=None, help="Optional: only process first N video_ids in predictions (for smoke tests).")
    ap.add_argument("--intersections", nargs="*", default=[],
                    help=("Intersection specs. Use ALL2 and/or ALL3 for all 2-way/3-way combos of --namespaces, "
                          "and/or explicit combos like 'gender*race_ethnicity' or 'gender*race_ethnicity*nationality'."))
    args = ap.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="Fairness eval v2 (intersections + engagement)")

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
    if args.limit:
        keep_vids = long_df["video_id"].drop_duplicates().head(int(args.limit))
        long_df = long_df[long_df["video_id"].isin(keep_vids)]

    # DB text + engagement meta
    conn = _connect(cfg.paths.database)
    _ensure_temp_tag_agg(conn)
    vids = long_df["video_id"].drop_duplicates().tolist()
    meta_df = _fetch_text_and_meta_for_ids(conn, vids)

    # Lexicon + membership
    lex = _compile_lexicon(cfg.paths.root / DEFAULT_LEXICON_REL, boundary="word")
    namespaces = [ns for ns in args.namespaces if ns in lex.compiled]
    mem = _match_membership(meta_df[["video_id","title","tags"]], lex, namespaces)  # {vid: {ns: {sg}}}

    # ---------- Subgroup fairness ----------
    summary_rows: List[List] = []
    md_lines: List[str] = [
        "# Fairness Summary\n",
        f"*Model:* **{args.model.upper()}**, *threshold:* **{args.threshold}**\n\n"
    ]
    ns_details: Dict[str, pd.DataFrame] = {}  # store to compare with intersections
    engagement_ns_written: Set[str] = set()

    for ns in namespaces:
        ns_rows: List[pd.DataFrame] = []

        for c in classes:
            df_c = long_df[long_df["class"] == c].copy()
            if df_c.empty:
                continue

            # explode (video_id, subgroup) membership rows
            sg_rows: List[Tuple[int, str, int, int]] = []
            for r in df_c[["video_id","y_true","y_pred"]].itertuples(index=False):
                vid = int(r.video_id)
                sgs = mem.get(vid, {}).get(ns, set())
                if not sgs:
                    continue
                for sg in sgs:
                    sg_rows.append((vid, sg, int(r.y_true), int(r.y_pred)))
            if not sg_rows:
                continue

            df_ns = pd.DataFrame(sg_rows, columns=["video_id","subgroup","y_true","y_pred"])
            df_ns["in_group"] = True

            tbl = _per_group_counts(df_ns)
            tbl = tbl[tbl["n_sub"] >= int(args.min_support)].reset_index(drop=True)
            if tbl.empty:
                continue

            tbl = _attach_pvalues_and_adjust(tbl)
            tbl.insert(0, "class", c)
            tbl.insert(0, "namespace", ns)
            ns_rows.append(tbl)

        if not ns_rows:
            continue

        ns_tbl = pd.concat(ns_rows, ignore_index=True)
        out_ns = fair_dir / f"details_{args.model}_{ns}.csv"
        ns_tbl.to_csv(out_ns, index=False)
        ns_details[ns] = ns_tbl.copy()

        # Namespace summary (worst gaps)
        for c in sorted(ns_tbl["class"].unique()):
            sub_c = ns_tbl[ns_tbl["class"] == c]
            if sub_c.empty:
                continue
            def _pick(metric: str) -> Tuple[str, float, float]:
                s = sub_c.iloc[np.argmax(np.abs(sub_c[metric].fillna(0.0)).values)]
                return (str(s.subgroup), float(s[metric]), float(s.get(metric.replace("_diff","_sub"), np.nan)))
            try:
                g_dp = _pick("dp_diff")
                g_eo = _pick("eo_diff")
                g_fp = _pick("fpr_diff")
            except Exception:
                g_dp = ("", float("nan"), float("nan"))
                g_eo = ("", float("nan"), float("nan"))
                g_fp = ("", float("nan"), float("nan"))
            summary_rows.append([ns, c, *g_dp, *g_eo, *g_fp])

        # Markdown excerpts (top DP gaps)
        md_lines.append(f"## {ns}\n\n")
        md_lines.append(f"- Details: `{out_ns}`\n")
        top_dp = ns_tbl.loc[:, ["class","subgroup","dp_diff","p_dp_adj","n_sub"]].copy()
        top_dp["abs_gap"] = top_dp["dp_diff"].abs()
        top_dp = top_dp.sort_values(["abs_gap","n_sub"], ascending=[False, False]).head(5)
        for cls, subgroup, dp_diff, p_adj, n_sub in top_dp[["class","subgroup","dp_diff","p_dp_adj","n_sub"]].itertuples(index=False, name=None):
            md_lines.append(f"- **DP gap** {dp_diff:+.3f} for `{subgroup}` in class `{cls}` (n={n_sub}); Holm-adj p={p_adj:.3f}")
        md_lines.append("\n")

        # Engagement comparisons per subgroup (once per namespace)
        if ns not in engagement_ns_written:
            eng_rows = []
            # Build group vids per subgroup (across all classes)
            # We'll use membership mem over all vids.
            groups_vids: Dict[str, Set[int]] = {}
            for vid, nsmap in mem.items():
                sgs = nsmap.get(ns, set())
                for sg in sgs:
                    groups_vids.setdefault(sg, set()).add(int(vid))
            # Compute stats + Holm adjust on log-views p-values
            pvals = []
            tmp_rows = []
            all_vids = meta_df["video_id"].tolist()
            for sg, vids_sg in groups_vids.items():
                stats = _engagement_stats(vids_sg, all_vids, meta_df)
                row = {
                    "namespace": ns, "subgroup": sg,
                    **stats
                }
                tmp_rows.append(row)
                pvals.append(row["p_log_views"])
            if tmp_rows:
                adj = _holm_bonferroni([1.0 if (p is None or np.isnan(p)) else p for p in pvals])
                for row, p_adj in zip(tmp_rows, adj):
                    row["p_log_views_adj"] = p_adj
                    eng_rows.append(row)
            if eng_rows:
                pd.DataFrame(eng_rows).sort_values("delta_mean_log_views", ascending=False)\
                    .to_csv(fair_dir / f"engagement_{args.model}_{ns}.csv", index=False)
                engagement_ns_written.add(ns)

    # Global summary (subgroups)
    if summary_rows:
        pd.DataFrame(
            summary_rows,
            columns=[
                "namespace","class",
                "dp_subgroup","dp_diff","dp_sub_rate",
                "eo_subgroup","eo_diff","eo_sub_tpr",
                "fpr_subgroup","fpr_diff","fpr_sub_fpr",
            ],
        ).to_csv(fair_dir / f"summary_{args.model}.csv", index=False)

    # ---------- Intersections ----------
    combos = _parse_intersections(args.intersections, namespaces)
    summary_rows_inters: List[List] = []
    if combos:
        md_lines.append("## Intersections\n\n")
    for combo in combos:
        combo_key = "*".join(combo)
        ix_rows_by_class: List[pd.DataFrame] = []
        # Compute fair tables per class
        for c in classes:
            df_c = long_df[long_df["class"] == c].copy()
            if df_c.empty:
                continue
            ix_rows = list(_iter_intersection_rows_for_class(df_c, mem, combo))
            if not ix_rows:
                continue
            df_ix = pd.DataFrame(ix_rows, columns=["video_id","subgroup","y_true","y_pred"])
            df_ix["in_group"] = True
            tbl = _per_group_counts(df_ix)
            tbl = tbl[tbl["n_sub"] >= int(args.min_support)].reset_index(drop=True)
            if tbl.empty:
                continue
            tbl = _attach_pvalues_and_adjust(tbl)
            tbl.insert(0, "class", c)
            tbl.insert(0, "combo", combo_key)
            ix_rows_by_class.append(tbl)

        if not ix_rows_by_class:
            continue

        ix_tbl = pd.concat(ix_rows_by_class, ignore_index=True)
        out_ix = fair_dir / f"details_intersections_{args.model}_{combo_key}.csv"
        ix_tbl.to_csv(out_ix, index=False)

        # Summaries (worst absolute gaps) per class
        for c in sorted(ix_tbl["class"].unique()):
            sub_c = ix_tbl[ix_tbl["class"] == c]
            if sub_c.empty:
                continue
            def _pick(metric: str) -> Tuple[str, float, float]:
                s = sub_c.iloc[np.argmax(np.abs(sub_c[metric].fillna(0.0)).values)]
                base_col = {"dp_diff":"pr_sub","eo_diff":"tpr_sub","fpr_diff":"fpr_sub"}[metric]
                return (str(s.subgroup), float(s[metric]), float(s[base_col]))
            try:
                g_dp = _pick("dp_diff")
                g_eo = _pick("eo_diff")
                g_fp = _pick("fpr_diff")
            except Exception:
                g_dp = ("", float("nan"), float("nan"))
                g_eo = ("", float("nan"), float("nan"))
                g_fp = ("", float("nan"), float("nan"))
            summary_rows_inters.append([combo_key, c, *g_dp, *g_eo, *g_fp])

        # Markdown pointer
        md_lines.append(f"- Details `{combo_key}`: `{out_ix}`\n")

        # Compare intersections vs marginal subgroups (per constituent namespace)
        compare_rows = []
        metrics_to_compare = [
            ("dp_diff","pr_sub"),
            ("eo_diff","tpr_sub"),
            ("fpr_diff","fpr_sub"),
        ]
        # Build lookups for marginals
        lookups = {ns: ns_details.get(ns, pd.DataFrame()) for ns in combo}
        for r in ix_tbl.itertuples(index=False):
            # parse intersection label into dict
            parts = [p.strip() for p in str(r.subgroup).split("&")]
            ns_sg = {}
            for p in parts:
                if "=" in p:
                    k,v = [x.strip() for x in p.split("=",1)]
                    ns_sg[k] = v
            # gather marginal rows for each constituent ns
            marg_vals = {}
            for ns in combo:
                df_ = lookups.get(ns)
                if df_ is None or df_.empty:
                    marg_vals[ns] = None
                    continue
                sg = ns_sg.get(ns)
                if sg is None:
                    marg_vals[ns] = None
                    continue
                row = df_[(df_["class"] == r._1) & (df_["subgroup"] == sg)]  # r._1 is 'class' (first after combo)
                if row.empty:
                    marg_vals[ns] = None
                else:
                    marg_vals[ns] = row.iloc[0].to_dict()
            # build long-form compare lines
            for m_diff, m_rate in metrics_to_compare:
                rec = {
                    "combo": r.combo, "class": r._1, "intersection": r.subgroup,
                    "metric": m_diff,
                    "intersection_value": getattr(r, m_diff, float("nan")),
                    "intersection_rate": getattr(r, m_rate, float("nan")),
                }
                for ns in combo:
                    mv = marg_vals.get(ns)
                    if mv is None:
                        rec[f"{ns}_marg_value"] = float("nan")
                        rec[f"{ns}_marg_rate"]  = float("nan")
                        rec[f"delta_ix_minus_{ns}"] = float("nan")
                    else:
                        rec[f"{ns}_marg_value"] = float(mv.get(m_diff, float("nan")))
                        rec[f"{ns}_marg_rate"]  = float(mv.get(m_rate, float("nan")))
                        rec[f"delta_ix_minus_{ns}"] = rec["intersection_value"] - rec[f"{ns}_marg_value"]
                compare_rows.append(rec)

        if compare_rows:
            pd.DataFrame(compare_rows).to_csv(
                fair_dir / f"compare_intersections_vs_marginals_{args.model}_{combo_key}.csv",
                index=False
            )

        # Engagement for intersection groups (across all classes)
        eng_rows = []
        all_vids = meta_df["video_id"].tolist()
        # Build mapping: intersection label -> set(video_id)
        label2vids: Dict[str, Set[int]] = {}
        for lab in ix_tbl["subgroup"].unique():
            vids_lab = set(int(v) for v in ix_tbl[ix_tbl["subgroup"] == lab]["subgroup"].index)  # placeholder wrong, fix below
        # Better: rebuild from mem to avoid duplication per class
        # Parse mem and add all videos that match the intersection condition
        for vid, nsmap in mem.items():
            sets = []
            ok = True
            for ns in combo:
                s = nsmap.get(ns, set())
                if not s:
                    ok = False
                    break
                sets.append(sorted(s))
            if not ok:
                continue
            for items in product(*sets):
                lab = " & ".join(f"{ns}={sg}" for ns, sg in zip(combo, items))
                label2vids.setdefault(lab, set()).add(int(vid))
        # Compute stats + Holm adjust
        pvals = []
        tmp_rows = []
        for lab, vids_lab in label2vids.items():
            stats = _engagement_stats(vids_lab, all_vids, meta_df)
            row = {"combo": combo_key, "intersection": lab, **stats}
            tmp_rows.append(row)
            pvals.append(row["p_log_views"])
        if tmp_rows:
            adj = _holm_bonferroni([1.0 if (p is None or np.isnan(p)) else p for p in pvals])
            eng_rows = []
            for row, p_adj in zip(tmp_rows, adj):
                row["p_log_views_adj"] = p_adj
                eng_rows.append(row)
            pd.DataFrame(eng_rows).sort_values("delta_mean_log_views", ascending=False).to_csv(
                fair_dir / f"engagement_intersections_{args.model}_{combo_key}.csv", index=False
            )

    if summary_rows_inters:
        pd.DataFrame(summary_rows_inters, columns=[
            "combo","class",
            "dp_subgroup","dp_diff","dp_sub_rate",
            "eo_subgroup","eo_diff","eo_sub_tpr",
            "fpr_subgroup","fpr_diff","fpr_sub_fpr",
        ]).to_csv(fair_dir / f"summary_intersections_{args.model}.csv", index=False)

    # Markdown file
    with (fair_dir / "markdown" / f"summary_{args.model}.md").open("w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("[done] Fairness evaluation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
