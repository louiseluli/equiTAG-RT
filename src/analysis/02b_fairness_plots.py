#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02b_fairness_plots.py

Purpose
-------
Generate polished light + dark figures from the fairness artifacts created by
`src/analysis/02_fairness_eval.py`. Never uses 'viridis'. Outputs PNGs.

What it makes
-------------
reports/figures/fairness_v1/<theme>/
  - ns_top_gaps_{metric}_{model}_{namespace}.png            # per-namespace top gaps (DP/EO/FPR)
  - ns_engagement_logviews_{model}_{namespace}.png          # subgroup engagement bars
  - ix_heatmap_{metric}_{model}_{comboKey}.png              # intersections heatmap (DP/EO/FPR)
  - ix_engagement_logviews_{model}_{comboKey}.png           # intersections engagement bars

CLI
---
python -m src.analysis.02b_fairness_plots \
  --model lr_eo \
  --top_n 15 \
  --themes both \
  --include_intersections \
  --dpi 200

Notes
-----
- Figures use diverging palettes (coolwarm/RdBu) and categorical (tab20).
- If a particular CSV is missing, it is silently skipped.
- Uses project config for paths, so outputs align with the rest of the repo.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.utils.config_loader import (
    load_config as load_project_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)

# -----------------------------
# Theming
# -----------------------------

def _apply_theme(theme: str):
    """Light/Dark rcParams (no viridis)."""
    theme = theme.lower()
    base = {
        "font.size": 11,
        "axes.grid": True,
        "grid.linewidth": 0.6,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.frameon": False,
        "figure.autolayout": False,                 # we control layout explicitly
        "figure.constrained_layout.use": False,     # avoid CL warnings
    }
    if theme == "dark":
        dark = {
            "figure.facecolor": "#0f1115",
            "axes.facecolor":   "#0f1115",
            "savefig.facecolor":"#0f1115",
            "axes.edgecolor":   "#e6e6e6",
            "axes.labelcolor":  "#e6e6e6",
            "xtick.color":      "#e6e6e6",
            "ytick.color":      "#e6e6e6",
            "text.color":       "#f2f2f2",
            "grid.color":       "#b0b0b0",
        }
        plt.rcParams.update({**base, **dark})
    else:  # light
        light = {
            "figure.facecolor": "white",
            "axes.facecolor":   "white",
            "savefig.facecolor":"white",
            "axes.edgecolor":   "#222222",
            "axes.labelcolor":  "#111111",
            "xtick.color":      "#111111",
            "ytick.color":      "#111111",
            "text.color":       "#111111",
            "grid.color":       "#777777",
        }
        plt.rcParams.update({**base, **light})

def _diverging_cmap(name: str = "coolwarm"):
    return plt.get_cmap(name)

# -----------------------------
# IO helpers
# -----------------------------

def _safe_read_csv(p: Path) -> Optional[pd.DataFrame]:
    try:
        if p.exists():
            return pd.read_csv(p)
    except Exception:
        pass
    return None

def _ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Plot primitives
# -----------------------------

def _annotate_sig(ax, xs: np.ndarray, ys: np.ndarray, pvals: Optional[np.ndarray], threshold: float = 0.05):
    if pvals is None:
        return
    for x, y, p in zip(xs, ys, pvals):
        if pd.isna(p):
            continue
        mark = ""
        if p < 0.001: mark = "***"
        elif p < 0.01: mark = "**"
        elif p < 0.05: mark = "*"
        if mark:
            ax.text(x, y, f" {mark}", va="center", ha="left", fontsize=10)

def _barh_diverging(ax, labels: List[str], values: np.ndarray, title: str, xlabel: str):
    order = np.argsort(np.abs(values))[::-1]
    labels = [labels[i] for i in order]
    values = values[order]
    y = np.arange(len(values))
    vmax = float(np.nanmax(np.abs(values))) if len(values) else 1.0
    cmap = _diverging_cmap("coolwarm")
    norm = plt.Normalize(-vmax, vmax)
    colors = [cmap(norm(v)) for v in values]
    ax.barh(y, values, color=colors, edgecolor="none")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.axvline(0, color="#888888", linewidth=0.8)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    # generous left margin for long labels
    plt.subplots_adjust(left=0.30)

def _heatmap(ax, data: np.ndarray, x_labels: List[str], y_labels: List[str], title: str, vlabel: str):
    if data.size == 0:
        ax.set_title(title + " (no data)")
        ax.axis("off")
        return
    vmax = np.nanmax(np.abs(data)) if np.isfinite(data).any() else 1.0
    cmap = _diverging_cmap("RdBu_r")
    im = ax.imshow(data, aspect="auto", cmap=cmap, vmin=-vmax, vmax=vmax, interpolation="nearest")
    ax.set_xticks(np.arange(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=45, ha="right")
    ax.set_yticks(np.arange(len(y_labels)))
    ax.set_yticklabels(y_labels)
    ax.set_title(title)
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(vlabel)
    plt.subplots_adjust(bottom=0.22, left=0.18, right=0.98, top=0.92)

# -----------------------------
# Plotters (namespaces)
# -----------------------------

def plot_namespace_top_gaps(figdir: Path, model: str, namespace: str, df_ns: pd.DataFrame, top_n: int, dpi: int):
    metrics = [("dp_diff","p_dp_adj","Δ Demographic Parity"),
               ("eo_diff","p_eo_adj","Δ Equal Opportunity"),
               ("fpr_diff","p_fpr_adj","Δ False Positive Rate")]
    for m_col, p_col, m_title in metrics:
        if m_col not in df_ns.columns:
            continue
        d = df_ns.copy()
        d["label"] = d["class"].astype(str) + ": " + d["subgroup"].astype(str)
        d["abs"] = d[m_col].abs()
        d = d.sort_values(["abs","n_sub"], ascending=[False, False]).head(top_n)
        if d.empty:
            continue

        # dynamic height
        fig_h = max(4.5, 0.44*len(d))
        fig, ax = plt.subplots(figsize=(10, fig_h))
        _barh_diverging(ax, d["label"].tolist(), d[m_col].values,
                        title=f"{namespace} — Top {len(d)} | {m_title} (model: {model})",
                        xlabel=m_title)
        pvals = d[p_col].values if p_col in d.columns else None
        xs = d[m_col].values
        ys = np.arange(len(d))
        _annotate_sig(ax, xs, ys, pvals, threshold=0.05)
        out = figdir / f"ns_top_gaps_{m_col}_{model}_{namespace}.png"
        fig.savefig(out, dpi=dpi, bbox_inches="tight")
        plt.close(fig)

def plot_namespace_engagement(figdir: Path, model: str, namespace: str, df_eng: pd.DataFrame, dpi: int):
    if df_eng is None or df_eng.empty:
        return
    d = df_eng.copy().sort_values("delta_mean_log_views", ascending=False)
    labels = d["subgroup"].astype(str).tolist()
    vals = d["delta_mean_log_views"].values
    pvals = d["p_log_views_adj"].values if "p_log_views_adj" in d.columns else None

    fig_h = max(4.5, 0.44*len(d))
    fig, ax = plt.subplots(figsize=(10, fig_h))
    _barh_diverging(ax, labels, vals,
                    title=f"{namespace} — Engagement Δ log(views) (model: {model})",
                    xlabel="Δ mean log(views) vs complement")
    xs = vals; ys = np.arange(len(vals))
    _annotate_sig(ax, xs, ys, pvals)
    out = figdir / f"ns_engagement_logviews_{model}_{namespace}.png"
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

# -----------------------------
# Plotters (intersections)
# -----------------------------

def plot_intersection_heatmaps(figdir: Path, model: str, combo_key: str, df_ix: pd.DataFrame, top_n: int, dpi: int):
    if df_ix is None or df_ix.empty:
        return
    # Keep top_n columns (intersection labels) by max abs gap across metrics
    keep_cols = {}
    for m_col in ["dp_diff","eo_diff","fpr_diff"]:
        if m_col not in df_ix.columns:
            continue
        tmp = (df_ix[["subgroup", m_col]]
               .groupby("subgroup", as_index=False)[m_col]
               .agg(lambda s: np.nanmax(np.abs(s))))
        tmp = tmp.sort_values(m_col, ascending=False).head(top_n)
        for s in tmp["subgroup"].tolist():
            keep_cols[s] = 1
    cols_kept = sorted(keep_cols.keys())
    if not cols_kept:
        cols_kept = df_ix["subgroup"].drop_duplicates().head(top_n).tolist()

    for m_col, m_title in [("dp_diff","Δ Demographic Parity"),
                           ("eo_diff","Δ Equal Opportunity"),
                           ("fpr_diff","Δ False Positive Rate")]:
        if m_col not in df_ix.columns:
            continue
        piv = (df_ix[df_ix["subgroup"].isin(cols_kept)]
               .pivot_table(index="class", columns="subgroup", values=m_col, aggfunc="mean"))
        # Order columns by max abs
        order = np.argsort(np.nanmax(np.abs(piv.values), axis=0))[::-1]
        piv = piv.iloc[:, order]
        data = piv.values
        x_labels = [str(c) for c in piv.columns]
        y_labels = [str(r) for r in piv.index]

        fig_w = min(18, 2 + 0.38*len(x_labels))
        fig_h = min(10, 1 + 0.44*len(y_labels))
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        _heatmap(ax, data, x_labels, y_labels,
                 title=f"{combo_key} — {m_title} (model: {model})",
                 vlabel=m_title)
        out = figdir / f"ix_heatmap_{m_col}_{model}_{combo_key}.png"
        fig.savefig(out, dpi=dpi, bbox_inches="tight")
        plt.close(fig)

def plot_intersection_engagement(figdir: Path, model: str, combo_key: str, df_eng_ix: pd.DataFrame, top_n: int, dpi: int):
    if df_eng_ix is None or df_eng_ix.empty:
        return
    d = df_eng_ix.copy()
    d["abs"] = d["delta_mean_log_views"].abs()
    d = d.sort_values(["abs","n_group"], ascending=[False, False]).head(top_n)
    labels = d["intersection"].astype(str).tolist()
    vals = d["delta_mean_log_views"].values
    pvals = d["p_log_views_adj"].values if "p_log_views_adj" in d.columns else None

    fig_h = max(4.5, 0.46*len(d))
    fig, ax = plt.subplots(figsize=(12, fig_h))
    _barh_diverging(ax, labels, vals,
                    title=f"{combo_key} — Engagement Δ log(views) (model: {model})",
                    xlabel="Δ mean log(views) vs complement")
    xs = vals; ys = np.arange(len(vals))
    _annotate_sig(ax, xs, ys, pvals)
    out = figdir / f"ix_engagement_logviews_{model}_{combo_key}.png"
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)

# -----------------------------
# Main
# -----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Make light/dark plots for fairness + engagement (no viridis).")
    ap.add_argument("--model", type=str, default="lr",
                    help="Model tag used in fairness CSVs (e.g., lr, rf, lr_eo).")
    ap.add_argument("--top_n", type=int, default=15, help="Top-N items for bar/heatmap trimming.")
    ap.add_argument("--themes", type=str, default="both", choices=["light","dark","both"], help="Which theme(s) to render.")
    ap.add_argument("--include_intersections", action="store_true", help="Render intersection plots if available.")
    ap.add_argument("--dpi", type=int, default=200, help="Output DPI.")
    args = ap.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="Fairness plots v1")

    metrics_root = cfg.paths.metrics
    fair_dir = metrics_root / "fairness_v1"
    fig_root = cfg.paths.reports.parent / "figures" / "fairness_v1"
    themes = ["light","dark"] if args.themes == "both" else [args.themes]
    for th in themes:
        _apply_theme(th)
        outdir = fig_root / th
        _ensure_dir(outdir)

        # --- Subgroup plots (per namespace) ---
        for p in sorted(fair_dir.glob(f"details_{args.model}_*.csv")):
            # filename like details_lr_eo_race_ethnicity.csv
            namespace = p.stem.split(f"details_{args.model}_", 1)[-1]
            df_ns = _safe_read_csv(p)
            if df_ns is None or df_ns.empty:
                continue
            plot_namespace_top_gaps(outdir, args.model, namespace, df_ns, args.top_n, args.dpi)

        # --- Engagement (per namespace) ---
        for p in sorted(fair_dir.glob(f"engagement_{args.model}_*.csv")):
            namespace = p.stem.split(f"engagement_{args.model}_", 1)[-1]
            df_eng = _safe_read_csv(p)
            if df_eng is None or df_eng.empty:
                continue
            plot_namespace_engagement(outdir, args.model, namespace, df_eng, args.dpi)

        # --- Intersections ---
        if args.include_intersections:
            for p in sorted(fair_dir.glob(f"details_intersections_{args.model}_*.csv")):
                # filename like details_intersections_lr_eo_gender*race_ethnicity.csv
                combo_key = p.stem.split(f"details_intersections_{args.model}_", 1)[-1]
                df_ix = _safe_read_csv(p)
                if df_ix is None or df_ix.empty:
                    continue
                plot_intersection_heatmaps(outdir, args.model, combo_key, df_ix, args.top_n, args.dpi)

            for p in sorted(fair_dir.glob(f"engagement_intersections_{args.model}_*.csv")):
                combo_key = p.stem.split(f"engagement_intersections_{args.model}_", 1)[-1]
                df_eng_ix = _safe_read_csv(p)
                if df_eng_ix is None or df_eng_ix.empty:
                    continue
                plot_intersection_engagement(outdir, args.model, combo_key, df_eng_ix, args.top_n, args.dpi)

    print("[done] Fairness plots rendered.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
