"""
src/analysis/01c_rq1_interpretive_brief.py

Purpose
-------
Generate a concise, publication-ready "interpretive brief" for RQ1, with 3–5
bullet insights per namespace. It integrates:
- Coverage (title vs tags),
- Tilt (tags emphasis vs title emphasis),
- Outcome outliers (rating & views),
- Overlaps (Jaccard pairs) when available.

Inputs (expected from prior steps)
----------------------------------
- reports/metrics/v1r_rq1_tables_consolidated.csv
- reports/metrics/v1_overlap_matrix_<namespace>.csv  (optional; created by 01_rq1_categorisation_evidence)

Outputs
-------
- reports/metrics/markdown/v1r_rq1_interpretive_brief.md
- reports/metrics/v1r_rq1_interpretive_brief.csv  (structured findings for traceability)

Assumptions
-----------
- Percent fields in consolidated table (e.g., 'union_share') are strings like "2.34%".
- 'tilt' ∈ {"tags > title","title > tags","balanced"} from prior step.

Design notes
------------
- We cap bullets at 5 per namespace; always aim for ≥3.
- We apply minimum support thresholds to avoid noise.
- Overlap bullets only appear if the relevant matrix exists and has signal.

Fairness & reporting
--------------------
These bullets give narrative scaffolding for the dissertation: coverage patterns,
labelling tilt (platform emphasis), and reception outcomes differences, which
motivate the fairness metrics used in RQ2–RQ3.

"""

from __future__ import annotations
import argparse
import csv
import math
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np

from src.utils.config_loader import (
    load_config as load_project_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)

# ---- Tunable thresholds (documented, easy to justify in Methods) ---------------------
MIN_SUPPORT = 100        # minimum union_n for outcome outlier consideration
TILT_FACTOR = 1.5        # tags:title >= 1.5 -> "tags emphasis"; <= 1/1.5 -> "title emphasis"
OVERLAP_THRESHOLD = 0.25 # Jaccard threshold for "notable" overlap pairs
MAX_BULLETS = 5          # hard cap per namespace (aim 3–5)


def _parse_pct(p: str) -> float:
    """Parse '12.34%' -> 0.1234; empty -> 0.0."""
    if not p:
        return 0.0
    p = p.strip().replace("%", "")
    try:
        return float(p) / 100.0
    except Exception:
        return 0.0


def _read_consolidated(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for r in rdr:
            rows.append(r)
    return rows


def _read_overlap_matrix(path: Path) -> Optional[Tuple[List[str], np.ndarray]]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        rdr = csv.reader(f)
        rows = list(rdr)
    if not rows or len(rows) < 2:
        return None
    labels = rows[0][1:]
    mat = np.array([[float(x) for x in row[1:]] for row in rows[1:]], dtype=float)
    return labels, mat


def _fmt_pct(x: float) -> str:
    return f"{100*x:.2f}%"


def _fmt_ns_caption(ns: str) -> str:
    # nicer display names if desired
    return ns.replace("_", " ")


def _build_namespace_bullets(ns: str, rows: List[Dict[str, str]], overlap_path: Path) -> Tuple[List[str], List[List[str]]]:
    """
    Returns (bullets, csv_rows) where csv_rows are machine-readable findings.
    """
    # Filter to namespace
    rns = [r for r in rows if r["namespace"] == ns]
    if not rns:
        return [], []

    # Compute numeric fields
    for r in rns:
        r["title_n"] = int(float(r["title_n"]))
        r["tags_n"] = int(float(r["tags_n"]))
        r["union_n"] = int(float(r["union_n"]))
        r["title_share_f"] = _parse_pct(r["title_share"])
        r["tags_share_f"] = _parse_pct(r["tags_share"])
        r["union_share_f"] = _parse_pct(r["union_share"])
        r["rating_mean_f"] = float(r["rating_mean"])
        # views_median may be "" for some rows; guard:
        try:
            r["views_median_f"] = float(r["views_median"])
        except Exception:
            r["views_median_f"] = float("nan")

    # Total active videos (robust estimate): median(n/ share) across subgroups with share>0
    totals = [r["union_n"] / r["union_share_f"] for r in rns if r["union_share_f"] > 0]
    total_active = int(np.median(totals)) if totals else None

    bullets: List[str] = []
    csv_findings: List[List[str]] = []

    # 1) Coverage: top 3 by union_n
    top_cov = sorted(rns, key=lambda x: x["union_n"], reverse=True)[:3]
    if top_cov:
        parts = [f"{t['subgroup']} ({t['union_n']:,}" +
                 (f", { _fmt_pct(t['union_share_f'])}" if t['union_share_f']>0 else "") + ")"
                 for t in top_cov]
        bullets.append(f"**Coverage leaders:** {', '.join(parts)}" + (f" out of {total_active:,} videos" if total_active else "") + ".")
        for t in top_cov:
            csv_findings.append([ns, "coverage_top", t["subgroup"], str(t["union_n"]), _fmt_pct(t["union_share_f"])])

    # 2) Tilt: find extremes
    tilt_tags = [r for r in rns if r["tags_n"] >= TILT_FACTOR * max(r["title_n"], 1)]
    tilt_title = [r for r in rns if r["title_n"] >= TILT_FACTOR * max(r["tags_n"], 1)]
    tilt_msgs = []
    if tilt_tags:
        ex = sorted(tilt_tags, key=lambda x: (x["tags_n"] / max(x["title_n"], 1)), reverse=True)[:2]
        ex_msg = "; ".join([f"{e['subgroup']} (tags:title ≈ {e['tags_n']}/{max(e['title_n'],1)})" for e in ex])
        tilt_msgs.append(f"tags emphasis → {ex_msg}")
        for e in ex:
            csv_findings.append([ns, "tilt_tags", e["subgroup"], str(e["tags_n"]), str(e["title_n"])])
    if tilt_title:
        ex = sorted(tilt_title, key=lambda x: (x["title_n"] / max(x["tags_n"], 1)), reverse=True)[:2]
        ex_msg = "; ".join([f"{e['subgroup']} (title:tags ≈ {e['title_n']}/{max(e['tags_n'],1)})" for e in ex])
        tilt_msgs.append(f"title emphasis → {ex_msg}")
        for e in ex:
            csv_findings.append([ns, "tilt_title", e["subgroup"], str(e["title_n"]), str(e["tags_n"])])
    if tilt_msgs:
        bullets.append("**Labelling tilt:** " + " | ".join(tilt_msgs) + ".")

    # 3) Outcome outliers (rating_mean_f), only for subgroups with adequate support
    supported = [r for r in rns if r["union_n"] >= MIN_SUPPORT]
    if len(supported) >= 2:
        mu = float(np.mean([r["rating_mean_f"] for r in supported]))
        sd = float(np.std([r["rating_mean_f"] for r in supported], ddof=1)) or 1.0
        z = [(r, (r["rating_mean_f"] - mu) / sd) for r in supported]
        z_pos = sorted([p for p in z if p[1] > 0], key=lambda x: x[1], reverse=True)[:2]
        z_neg = sorted([p for p in z if p[1] < 0], key=lambda x: x[1])[:2]
        if z_pos:
            msg = "; ".join([f"{r['subgroup']} (↑rating, z≈{zv:.2f}, n={r['union_n']:,})" for r, zv in z_pos])
            bullets.append(f"**Reception (positive):** {msg}.")
            for r, zv in z_pos:
                csv_findings.append([ns, "rating_high", r["subgroup"], f"{r['rating_mean_f']:.3f}", str(r["union_n"])])
        if z_neg:
            msg = "; ".join([f"{r['subgroup']} (↓rating, z≈{zv:.2f}, n={r['union_n']:,})" for r, zv in z_neg])
            bullets.append(f"**Reception (negative):** {msg}.")
            for r, zv in z_neg:
                csv_findings.append([ns, "rating_low", r["subgroup"], f"{r['rating_mean_f']:.3f}", str(r["union_n"])])

    # 4) Overlap pairs (Jaccard)
    overlap = _read_overlap_matrix(overlap_path)
    if overlap is not None:
        labels, mat = overlap
        pairs = []
        n = len(labels)
        for i in range(n):
            for j in range(i+1, n):
                v = mat[i, j]
                if v >= OVERLAP_THRESHOLD:
                    pairs.append((labels[i], labels[j], v))
        pairs.sort(key=lambda x: x[2], reverse=True)
        if pairs:
            top = pairs[:3]
            msg = "; ".join([f"{a}–{b} (J={v:.2f})" for a, b, v in top])
            bullets.append(f"**Frequent co-labelling:** {msg}.")
            for a, b, v in top:
                csv_findings.append([ns, "overlap_pair", f"{a}–{b}", f"{v:.3f}"])

    # Cap bullet count, ensure at least 3 if possible
    if len(bullets) > MAX_BULLETS:
        bullets = bullets[:MAX_BULLETS]

    return bullets, csv_findings


def main() -> int:
    parser = argparse.ArgumentParser(description="RQ1 interpretive brief (bullets per namespace).")
    parser.add_argument("--consolidated", type=str, default=None,
                        help="Path to v1r_rq1_tables_consolidated.csv")
    args = parser.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="RQ1 interpretive brief")

    metrics = cfg.paths.metrics
    cons_path = Path(args.consolidated) if args.consolidated else (metrics / "v1r_rq1_tables_consolidated.csv")
    if not cons_path.exists():
        raise FileNotFoundError(f"Missing consolidated table at {cons_path}")

    rows = _read_consolidated(cons_path)
    namespaces = sorted(set(r["namespace"] for r in rows))

    # Build bullets
    md_dir = metrics / "markdown"
    md_dir.mkdir(parents=True, exist_ok=True)
    md_out = md_dir / "v1r_rq1_interpretive_brief.md"

    csv_out = metrics / "v1r_rq1_interpretive_brief.csv"
    csv_rows: List[List[str]] = []
    csv_header = ["namespace", "kind", "subject", "value1", "value2"]

    with md_out.open("w", encoding="utf-8") as f:
        f.write("# RQ1 Interpretive Brief — Coverage, Tilt, Outcomes, Overlaps\n\n")
        f.write("This brief summarises key patterns to support the fairness analysis that follows.\n\n")
        for ns in namespaces:
            overlap_path = metrics / f"v1_overlap_matrix_{ns}.csv"
            bullets, findings = _build_namespace_bullets(ns, rows, overlap_path)
            if not bullets:
                continue
            f.write(f"## {_fmt_ns_caption(ns)}\n\n")
            for b in bullets:
                f.write(f"- {b}\n")
            f.write("\n")
            csv_rows.extend(findings)

    # Structured CSV for traceability
    with csv_out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(csv_header)
        for r in csv_rows:
            w.writerow(r)

    print("[done] RQ1 interpretive brief created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
