"""
src/analysis/01b_rq1_tables_report.py

Purpose
-------
Build publication-ready RQ1 tables by merging coverage (title vs tags) and outcomes
(views/rating) per protected subgroup, with useful derived indicators.

Inputs (from v1 evidence pack)
------------------------------
- reports/metrics/v1_coverage_by_field.csv
    columns: namespace,subgroup,field,n_videos,share
- reports/metrics/v1_subgroup_outcomes.csv
    columns: namespace,subgroup,n_videos,share,views_mean,views_median,rating_mean,rating_median

Outputs
-------
CSV:
- reports/metrics/v1r_rq1_tables_consolidated.csv
- reports/metrics/v1r_rq1_tables_<namespace>.csv

Markdown:
- reports/metrics/markdown/v1r_rq1_tables.md   (multi-section, one per namespace)

LaTeX:
- reports/metrics/latex/v1r_rq1_tables_<namespace>.tex

Notes
-----
- We DO NOT create new plots here (your figures already export in light/dark).
- We avoid any colormap choices (none used).
- 'tilt' indicates relative emphasis in platform labelling: tags vs title.
"""

from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple, List

from src.utils.config_loader import (
    load_config as load_project_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)

def _read_cov(path: Path) -> Dict[Tuple[str, str, str], Tuple[int, float]]:
    data: Dict[Tuple[str, str, str], Tuple[int, float]] = {}
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            ns = row["namespace"]
            sg = row["subgroup"]
            field = row["field"]  # title|tags
            n = int(float(row["n_videos"]))  # tolerate scientific notation
            share = float(row["share"])
            data[(ns, sg, field)] = (n, share)
    return data

def _read_outcomes(path: Path) -> Dict[Tuple[str, str], Dict[str, float]]:
    data: Dict[Tuple[str, str], Dict[str, float]] = {}
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            ns = row["namespace"]
            sg = row["subgroup"]
            data[(ns, sg)] = {
                "n_union": int(float(row["n_videos"])),
                "share_union": float(row["share"]),
                "views_mean": float(row["views_mean"]),
                "views_median": float(row["views_median"]),
                "rating_mean": float(row["rating_mean"]),
                "rating_median": float(row["rating_median"]),
            }
    return data

def _safe_ratio(a: int, b: int) -> float:
    if b == 0:
        return float("inf") if a > 0 else 1.0
    return a / b

def _tilt_label(tags_n: int, title_n: int) -> str:
    r = _safe_ratio(tags_n, title_n)
    # Three-way: strong/balanced thresholds chosen for interpretability in tables
    if r >= 1.5:
        return "tags > title"
    if r <= (1/1.5):
        return "title > tags"
    return "balanced"

def _write_csv(path: Path, header: List[str], rows: List[List]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def _fmt_pct(x: float) -> str:
    return f"{100*x:.2f}%" if x == x else ""

def main() -> int:
    parser = argparse.ArgumentParser(description="RQ1 narrative tables (merge coverage + outcomes).")
    args = parser.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="RQ1 narrative tables")

    metrics = cfg.paths.metrics
    cov_path = metrics / "v1_coverage_by_field.csv"
    out_path = metrics / "v1_subgroup_outcomes.csv"
    if not cov_path.exists() or not out_path.exists():
        raise FileNotFoundError("Missing v1 metrics. Run '01_rq1_categorisation_evidence.py' first.")

    cov = _read_cov(cov_path)
    outc = _read_outcomes(out_path)

    # Build consolidated rows
    consolidated: List[List] = []
    per_ns_rows: Dict[str, List[List]] = defaultdict(list)

    # Collect namespaces/subgroups present in outcomes (union-based definition)
    keys = sorted(outc.keys())  # (ns, sg)
    for (ns, sg) in keys:
        title_n, title_share = cov.get((ns, sg, "title"), (0, 0.0))
        tags_n, tags_share   = cov.get((ns, sg, "tags"),  (0, 0.0))

        o = outc[(ns, sg)]
        tilt = _tilt_label(tags_n, title_n)

        row = [
            ns, sg,
            title_n, _fmt_pct(title_share),
            tags_n, _fmt_pct(tags_share),
            o["n_union"], _fmt_pct(o["share_union"]),
            f"{o['rating_mean']:.3f}", f"{o['views_median']:.0f}",
            tilt
        ]
        consolidated.append(row)
        per_ns_rows[ns].append(row)

    # Sort within each namespace by union count desc
    for ns in per_ns_rows:
        per_ns_rows[ns].sort(key=lambda r: int(r[6]), reverse=True)
    consolidated.sort(key=lambda r: (r[0], -int(r[6]), r[1]))

    header = [
        "namespace", "subgroup",
        "title_n", "title_share",
        "tags_n", "tags_share",
        "union_n", "union_share",
        "rating_mean", "views_median",
        "tilt"
    ]

    # Write CSVs
    _write_csv(metrics / "v1r_rq1_tables_consolidated.csv", header, consolidated)
    for ns, rows in per_ns_rows.items():
        _write_csv(metrics / f"v1r_rq1_tables_{ns}.csv", header, rows)

    # Write Markdown (pretty, sectioned)
    md_dir = metrics / "markdown"
    md_dir.mkdir(parents=True, exist_ok=True)
    md = md_dir / "v1r_rq1_tables.md"
    with md.open("w", encoding="utf-8") as f:
        f.write("# RQ1 Narrative Tables — Coverage & Outcomes\n\n")
        f.write("**Note:** ‘tilt’ indicates relative emphasis in platform labelling (tags vs title). ")
        f.write("Shares are relative to the total number of active videos analysed.\n\n")
        for ns in sorted(per_ns_rows.keys()):
            f.write(f"## {ns}\n\n")
            f.write("| subgroup | title_n | title_share | tags_n | tags_share | union_n | union_share | rating_mean | views_median | tilt |\n")
            f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|\n")
            for r in per_ns_rows[ns]:
                _, sg, t_n, t_s, g_n, g_s, u_n, u_s, r_m, v_med, tilt = r
                f.write(f"| {sg} | {t_n} | {t_s} | {g_n} | {g_s} | {u_n} | {u_s} | {r_m} | {v_med} | {tilt} |\n")
            f.write("\n")

    # Write LaTeX (minimal)
    tex_dir = metrics / "latex"
    tex_dir.mkdir(parents=True, exist_ok=True)
    for ns, rows in per_ns_rows.items():
        tex = tex_dir / f"v1r_rq1_tables_{ns}.tex"
        with tex.open("w", encoding="utf-8") as f:
            f.write(r"\begin{tabular}{lrrrrrrrrl}" + "\n")
            f.write(r"\toprule" + "\n")
            f.write(r"subgroup & title\_n & title\_% & tags\_n & tags\_% & union\_n & union\_% & rating\_mean & views\_median & tilt \\" + "\n")
            f.write(r"\midrule" + "\n")
            for r in rows:
                _, sg, t_n, t_s, g_n, g_s, u_n, u_s, r_m, v_med, tilt = r
                f.write(f"{sg} & {t_n} & {t_s} & {g_n} & {g_s} & {u_n} & {u_s} & {r_m} & {v_med} & {tilt} \\\n")
            f.write(r"\bottomrule" + "\n")
            f.write(r"\end{tabular}" + "\n")

    print("[done] RQ1 narrative tables created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
