#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02c_fairness_report.py

Purpose
-------
Create a concise, publication-style Markdown report that summarizes the fairness
evaluation artifacts produced by:
  - src/analysis/02_fairness_eval.py
  - src/analysis/02b_fairness_plots.py

The report includes:
- Per-namespace top gaps (DP/EO/FPR) with adjusted p-values
- Subgroup engagement deltas (log views) with adjusted p-values
- Optional intersections summaries if available
- Cross-model comparison (e.g., LR vs RF) to highlight consistent gaps
- Links to the rendered figures (light theme)

Outputs
-------
reports/metrics/fairness_v1/markdown/report_{modelKey}.md
  where {modelKey} is e.g. "lr" or "lr_rf"

CLI
---
python -m src.analysis.02c_fairness_report \
  --models lr rf \
  --top_n 10 \
  --alpha 0.05
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from src.utils.config_loader import (
    load_config as load_project_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)

# ---------------------------------
# IO helpers
# ---------------------------------

def _safe_read_csv(p: Path) -> Optional[pd.DataFrame]:
    try:
        if p.exists():
            return pd.read_csv(p)
    except Exception:
        pass
    return None

def _exists(p: Path) -> bool:
    try:
        return p.exists()
    except Exception:
        return False

# ---------------------------------
# Formatting helpers
# ---------------------------------

def _fmt_gap(x) -> str:
    try:
        if pd.isna(x):
            return "—"
        return f"{float(x):+0.3f}"
    except Exception:
        return "—"

def _fmt_rate(x) -> str:
    try:
        if pd.isna(x):
            return "—"
        return f"{float(x):0.3f}"
    except Exception:
        return "—"

def _fmt_int(x) -> str:
    try:
        if pd.isna(x):
            return "0"
        return f"{int(x)}"
    except Exception:
        return "0"

def _fmt_p(x, alpha: float) -> str:
    try:
        if pd.isna(x):
            return "—"
        x = float(x)
        stars = ""
        if x < 0.001: stars = "***"
        elif x < 0.01: stars = "**"
        elif x < alpha: stars = "*"
        return f"{x:0.3g}{stars}"
    except Exception:
        return "—"

# ---------------------------------
# Report building
# ---------------------------------

def _load_namespace_tables(fair_dir: Path, model: str) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for p in sorted(fair_dir.glob(f"details_{model}_*.csv")):
        ns = p.stem.split(f"details_{model}_", 1)[-1]
        df = _safe_read_csv(p)
        if df is None or df.empty:
            continue
        out[ns] = df
    return out

def _load_namespace_engagement(fair_dir: Path, model: str) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for p in sorted(fair_dir.glob(f"engagement_{model}_*.csv")):
        ns = p.stem.split(f"engagement_{model}_", 1)[-1]
        df = _safe_read_csv(p)
        if df is None or df.empty:
            continue
        out[ns] = df
    return out

def _load_intersections_tables(fair_dir: Path, model: str) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for p in sorted(fair_dir.glob(f"details_intersections_{model}_*.csv")):
        key = p.stem.split(f"details_intersections_{model}_", 1)[-1]
        df = _safe_read_csv(p)
        if df is None or df.empty:
            continue
        out[key] = df
    return out

def _load_intersections_engagement(fair_dir: Path, model: str) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    for p in sorted(fair_dir.glob(f"engagement_intersections_{model}_*.csv")):
        key = p.stem.split(f"engagement_intersections_{model}_", 1)[-1]
        df = _safe_read_csv(p)
        if df is None or df.empty:
            continue
        out[key] = df
    return out

def _make_md_table_top_gaps(df_ns: pd.DataFrame, metric_col: str, p_col: str, top_n: int, alpha: float) -> str:
    # Rank by abs gap, break ties by subgroup size
    d = df_ns.copy()
    if metric_col not in d.columns:
        return "_No data._\n"
    if "n_sub" not in d.columns:
        d["n_sub"] = np.nan

    d["abs"] = d[metric_col].abs()
    d = d.sort_values(["abs", "n_sub"], ascending=[False, False]).head(top_n)
    cols = ["class", "subgroup", "n_sub", metric_col, p_col]
    for c in cols:
        if c not in d.columns:
            d[c] = np.nan

    lines = []
    lines.append("| # | class | subgroup | n | gap | p_adj |")
    lines.append("|---:|:------|:---------|---:|----:|:-----|")
    i = 1
    # Use iterrows to avoid attribute access to reserved word 'class'
    for _, row in d.iterrows():
        cls = str(row["class"])
        sg = str(row["subgroup"])
        n_sub = _fmt_int(row["n_sub"])
        gap = _fmt_gap(row[metric_col])
        p = _fmt_p(row[p_col], alpha) if p_col in d.columns else "—"
        lines.append(f"| {i} | {cls} | `{sg}` | {n_sub} | {gap} | {p} |")
        i += 1
    return "\n".join(lines) + "\n"

def _make_md_table_engagement(df_eng: pd.DataFrame, top_n: int, alpha: float) -> str:
    if df_eng is None or df_eng.empty:
        return "_No data._\n"
    d = df_eng.copy()
    if "delta_mean_log_views" not in d.columns:
        return "_No data._\n"
    d["abs"] = d["delta_mean_log_views"].abs()
    d = d.sort_values(["abs", "n_group"], ascending=[False, False]).head(top_n)
    if "subgroup" not in d.columns and "intersection" in d.columns:
        d["subgroup"] = d["intersection"]

    for c in ["p_log_views_adj", "mean_log_views_group", "mean_log_views_comp", "n_group", "n_comp"]:
        if c not in d.columns:
            d[c] = np.nan

    lines = []
    lines.append("| # | subgroup/intersection | Δ mean log(views) | p_adj | n_g / n_c |")
    lines.append("|---:|:----------------------|------------------:|:------|:----------|")
    i = 1
    for _, row in d.iterrows():
        lab = str(row["subgroup"])
        dv = _fmt_gap(row["delta_mean_log_views"])
        p = _fmt_p(row["p_log_views_adj"], alpha)
        ng = _fmt_int(row["n_group"])
        nc = _fmt_int(row["n_comp"])
        lines.append(f"| {i} | `{lab}` | {dv} | {p} | {ng} / {nc} |")
        i += 1
    return "\n".join(lines) + "\n"

def _link_fig_if_exists(fig_root: Path, rel_path: str) -> str:
    p = fig_root / rel_path
    if _exists(p):
        # Relative path in markdown
        return f"![{rel_path}]({rel_path})"
    return ""

def _combine_key(models: Sequence[str]) -> str:
    return "_".join(models)

# ---------------------------------
# Model comparison
# ---------------------------------

def _compare_models_per_ns(df_a: pd.DataFrame, df_b: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """
    Inner-join on (class, subgroup). Return rows where sign of gaps is consistent
    and both are significant for at least one metric (DP/EO/FPR).
    """
    key_cols = ["class", "subgroup"]
    metrics = [
        ("dp_diff", "p_dp_adj"),
        ("eo_diff", "p_eo_adj"),
        ("fpr_diff", "p_fpr_adj"),
    ]
    out_rows = []
    # restrict to necessary columns
    use_cols = set(key_cols + [m for m,_ in metrics] + [p for _,p in metrics] + ["n_sub"])
    a = df_a[[c for c in df_a.columns if c in use_cols]].copy()
    b = df_b[[c for c in df_b.columns if c in use_cols]].copy()
    merged = a.merge(b, on=key_cols, suffixes=("_a", "_b"))
    if merged.empty:
        return pd.DataFrame()

    for _, r in merged.iterrows():
        row = {"class": r["class"], "subgroup": r["subgroup"]}
        any_keep = False
        for m, p in metrics:
            va = r.get(f"{m}_a", np.nan)
            vb = r.get(f"{m}_b", np.nan)
            pa = r.get(f"{p}_a", np.nan)
            pb = r.get(f"{p}_b", np.nan)
            same_sign = (np.sign(va) == np.sign(vb)) and (not pd.isna(va)) and (not pd.isna(vb))
            sig_both = (not pd.isna(pa) and pa < alpha) and (not pd.isna(pb) and pb < alpha)
            row[f"{m}_a"] = va; row[f"{m}_b"] = vb
            row[f"{p}_a"] = pa; row[f"{p}_b"] = pb
            row[f"{m}_same_sign"] = bool(same_sign)
            row[f"{m}_sig_both"] = bool(sig_both)
            any_keep = any_keep or (same_sign and sig_both)
        if any_keep:
            out_rows.append(row)
    return pd.DataFrame(out_rows)

def _make_md_table_model_compare(df_cmp: pd.DataFrame, model_a: str, model_b: str, top_n: int) -> str:
    if df_cmp is None or df_cmp.empty:
        return "_No consistent significant gaps across models._\n"
    # Rank by the largest absolute DP gap average (as a simple heuristic)
    df = df_cmp.copy()
    for m in ["dp_diff", "eo_diff", "fpr_diff"]:
        df[f"{m}_mean_abs"] = (df[f"{m}_a"].abs() + df[f"{m}_b"].abs()) / 2.0
    df["score"] = df[["dp_diff_mean_abs","eo_diff_mean_abs","fpr_diff_mean_abs"]].max(axis=1)
    df = df.sort_values("score", ascending=False).head(top_n)

    lines = []
    lines.append(f"| # | class | subgroup | {model_a} ΔDP | {model_b} ΔDP | {model_a} ΔEO | {model_b} ΔEO | {model_a} ΔFPR | {model_b} ΔFPR |")
    lines.append("|---:|:------|:---------|-----------:|-----------:|-----------:|-----------:|------------:|------------:|")
    i = 1
    for _, r in df.iterrows():
        lines.append(
            f"| {i} | {r['class']} | `{r['subgroup']}` | "
            f"{_fmt_gap(r['dp_diff_a'])} | {_fmt_gap(r['dp_diff_b'])} | "
            f"{_fmt_gap(r['eo_diff_a'])} | {_fmt_gap(r['eo_diff_b'])} | "
            f"{_fmt_gap(r['fpr_diff_a'])} | {_fmt_gap(r['fpr_diff_b'])} |"
        )
        i += 1
    return "\n".join(lines) + "\n"

# ---------------------------------
# Main
# ---------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Build a Markdown report summarizing fairness metrics/plots.")
    ap.add_argument("--models", nargs="+", required=True, choices=["lr","rf"], help="Models to include (e.g., lr rf).")
    ap.add_argument("--top_n", type=int, default=10, help="Top-N rows for tables.")
    ap.add_argument("--alpha", type=float, default=0.05, help="Significance threshold for p-values.")
    ap.add_argument("--theme", type=str, default="light", choices=["light","dark"], help="Which figure theme to link in the report.")
    args = ap.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    dev = pick_device()
    print_run_header(cfg, dev, note="Fairness report v1")

    fair_dir = cfg.paths.metrics / "fairness_v1"
    fig_root = cfg.paths.reports.parent / "figures" / "fairness_v1" / args.theme
    md_dir = fair_dir / "markdown"
    md_dir.mkdir(parents=True, exist_ok=True)
    model_key = _combine_key(args.models)
    out_md = md_dir / f"report_{model_key}.md"

    # Load per model
    ns_tables: Dict[str, Dict[str, pd.DataFrame]] = {}
    ns_eng: Dict[str, Dict[str, pd.DataFrame]] = {}
    ix_tables: Dict[str, Dict[str, pd.DataFrame]] = {}
    ix_eng: Dict[str, Dict[str, pd.DataFrame]] = {}

    for m in args.models:
        ns_tables[m] = _load_namespace_tables(fair_dir, m)
        ns_eng[m]    = _load_namespace_engagement(fair_dir, m)
        ix_tables[m] = _load_intersections_tables(fair_dir, m)
        ix_eng[m]    = _load_intersections_engagement(fair_dir, m)

    # ---------------- Header ----------------
    lines: List[str] = []
    lines.append("# Fairness Report\n")
    lines.append(f"*Models:* **{', '.join(args.models).upper()}**  \n")
    lines.append(f"*Significance (Holm-adj):* α = **{args.alpha}**  \n")
    lines.append(f"*Figures:* linked from **{args.theme}** theme.  \n")
    lines.append("\n---\n")

    # ---------------- Per model sections ----------------
    for m in args.models:
        lines.append(f"## Model: {m.upper()}\n")

        # Per-namespace tables + figure links
        for ns, df in ns_tables[m].items():
            lines.append(f"### Namespace: `{ns}`\n")

            # Figure links (DP/EO/FPR)
            for metric in ["dp_diff","eo_diff","fpr_diff"]:
                fig_name = f"ns_top_gaps_{metric}_{m}_{ns}.png"
                rel = fig_name
                img_md = _link_fig_if_exists(fig_root, rel)
                if img_md:
                    lines.append(img_md)
                    lines.append("\n")

            # Top gaps tables
            lines.append("**Top ΔDP**\n\n")
            lines.append(_make_md_table_top_gaps(df, "dp_diff", "p_dp_adj", args.top_n, args.alpha))
            lines.append("**Top ΔEO**\n\n")
            lines.append(_make_md_table_top_gaps(df, "eo_diff", "p_eo_adj", args.top_n, args.alpha))
            lines.append("**Top ΔFPR**\n\n")
            lines.append(_make_md_table_top_gaps(df, "fpr_diff", "p_fpr_adj", args.top_n, args.alpha))

            # Engagement (subgroups)
            if ns in ns_eng[m]:
                lines.append("**Engagement — Δ mean log(views)**\n\n")
                # figure link
                fig_name = f"ns_engagement_logviews_{m}_{ns}.png"
                img_md = _link_fig_if_exists(fig_root, fig_name)
                if img_md:
                    lines.append(img_md)
                    lines.append("\n")
                lines.append(_make_md_table_engagement(ns_eng[m][ns], args.top_n, args.alpha))

        # Intersections (if any)
        if ix_tables[m]:
            lines.append("### Intersections (highlights)\n")
            for combo_key, dfx in ix_tables[m].items():
                lines.append(f"#### `{combo_key}`\n")
                # Heatmaps
                for metric in ["dp_diff","eo_diff","fpr_diff"]:
                    fig_name = f"ix_heatmap_{metric}_{m}_{combo_key}.png"
                    img_md = _link_fig_if_exists(fig_root, fig_name)
                    if img_md:
                        lines.append(img_md)
                        lines.append("\n")

                # Engagement intersections
                if combo_key in ix_eng[m]:
                    fig_name = f"ix_engagement_logviews_{m}_{combo_key}.png"
                    img_md = _link_fig_if_exists(fig_root, fig_name)
                    if img_md:
                        lines.append(img_md)
                        lines.append("\n")
                    lines.append(_make_md_table_engagement(ix_eng[m][combo_key], args.top_n, args.alpha))

        lines.append("\n---\n")

    # ---------------- Cross-model comparison ----------------
    if len(args.models) >= 2:
        a, b = args.models[0], args.models[1]
        lines.append(f"## Cross-Model Comparison: {a.upper()} vs {b.upper()}\n")
        # For each namespace present in both models, compare details tables
        common_ns = sorted(set(ns_tables[a].keys()).intersection(set(ns_tables[b].keys())))
        if not common_ns:
            lines.append("_No common namespaces to compare._\n")
        for ns in common_ns:
            df_a = ns_tables[a][ns]
            df_b = ns_tables[b][ns]
            cmp_df = _compare_models_per_ns(df_a, df_b, args.alpha)
            if cmp_df is None or cmp_df.empty:
                continue
            lines.append(f"### `{ns}` — consistent & significant gaps\n")
            lines.append(_make_md_table_model_compare(cmp_df, a.upper(), b.upper(), args.top_n))

        lines.append("\n---\n")

    # ---------------- Save ----------------
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"[done] Wrote report: {out_md}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
