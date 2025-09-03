"""
src/analysis/01_rq1_categorisation_evidence.py

Purpose
-------
RQ1 Evidence Pack: quantify how videos are currently categorised via titles/tags and
expose potential bias vectors via subgroup coverage, outcomes, and overlaps.

Inputs
------
- SQLite DB at cfg.paths.database (tables: videos, video_tags).
- Compiled lexicon from src.utils.lexicon_loader (protected_terms.json).

Outputs (CSV)
-------------
- reports/metrics/v1_coverage_by_field.csv
    columns: [namespace, subgroup, field, n_videos, share]
- reports/metrics/v1_subgroup_outcomes.csv
    columns: [namespace, subgroup, n_videos, share, views_mean, views_median, rating_mean, rating_median]
- reports/metrics/v1_overlap_matrix_<namespace>.csv
    square matrix of Jaccard overlaps between subgroups (based on matched videos)

Outputs (Figures: light + dark)
-------------------------------
- reports/figures/v1_coverage_<namespace>_{light|dark}.png
- reports/figures/v1_outcomes_<namespace>_{light|dark}.png

Assumptions
-----------
- video_tags has (video_id INTEGER, tag TEXT).
- We aggregate tags per video via GROUP_CONCAT once for efficiency.

Failure Modes
-------------
- If lexicon or DB missing -> clear error.
- If a namespace has <2 subgroups, overlap plot is skipped.

Complexity
----------
- Streaming batches; memory is O(batch_size).
- One-time temp aggregation for tags.

Test Notes
----------
- Use --limit 10000 for a fast run.
- Figures intentionally avoid specifying any colormap (no 'viridis').
"""

from __future__ import annotations
import argparse
import csv
import math
import sqlite3
from collections import defaultdict, Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Iterable, Set

import numpy as np
import matplotlib.pyplot as plt

from src.utils.config_loader import (
    load_config as load_project_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)
from src.utils.lexicon_loader import ProtectedLexicon, DEFAULT_LEXICON_REL

# --------------------------------------------------------------------------------------
# Data access
# --------------------------------------------------------------------------------------

def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def ensure_temp_tag_agg(conn: sqlite3.Connection) -> None:
    """
    Create a temp table with aggregated tags per video for fast joins.
    """
    conn.execute("DROP TABLE IF EXISTS temp_vt_agg")
    conn.execute("""
        CREATE TEMP TABLE temp_vt_agg AS
        SELECT video_id, GROUP_CONCAT(tag, ' ') AS tags
        FROM video_tags
        GROUP BY video_id
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_vt_agg_vid ON temp_vt_agg(video_id)")

def iter_video_batches(conn: sqlite3.Connection, limit: int | None, batch_size: int) -> Iterable[List[sqlite3.Row]]:
    """
    Yield batches of videos with aggregated tags.
    """
    base = """
        SELECT v.video_id, v.title, v.views, v.rating, v.ratings, v.is_active, COALESCE(t.tags, '') AS tags
        FROM videos v
        LEFT JOIN temp_vt_agg t ON t.video_id = v.video_id
        WHERE v.is_active = 1
        ORDER BY v.video_id
    """
    if limit is not None:
        base += f" LIMIT {int(limit)}"
    cur = conn.execute(base)
    batch: List[sqlite3.Row] = []
    for row in cur:
        batch.append(row)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

# --------------------------------------------------------------------------------------
# Matching logic
# --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class MatchResult:
    vid: int
    title_hits: Dict[str, Set[str]]   # ns -> {subgroups}
    tags_hits: Dict[str, Set[str]]    # ns -> {subgroups}
    views: int
    rating: float

def match_batch(rows: List[sqlite3.Row], lex: ProtectedLexicon) -> List[MatchResult]:
    out: List[MatchResult] = []
    for r in rows:
        vid = int(r["video_id"])
        title = (r["title"] or "").lower()
        tags  = (r["tags"]  or "").lower()
        views = int(r["views"] or 0)
        rating = float(r["rating"] or 0.0)
        title_hits: Dict[str, Set[str]] = defaultdict(set)
        tags_hits: Dict[str, Set[str]] = defaultdict(set)

        for ns, cns in lex.compiled.items():
            for sg, cg in cns.groups.items():
                # title
                if any(p.search(title) for p in cg.patterns):
                    title_hits[ns].add(sg)
                # tags
                if any(p.search(tags) for p in cg.patterns):
                    tags_hits[ns].add(sg)

        out.append(MatchResult(vid, title_hits, tags_hits, views, rating))
    return out

# --------------------------------------------------------------------------------------
# Aggregations
# --------------------------------------------------------------------------------------

def aggregate_coverage(results: Iterable[MatchResult], namespaces: List[str]) -> List[Tuple[str, str, str, int]]:
    """
    Returns rows of (namespace, subgroup, field, n_videos), where field in {"title","tags"}.
    """
    counts: Dict[Tuple[str, str, str], int] = Counter()
    for m in results:
        for ns in namespaces:
            for sg in m.title_hits.get(ns, set()):
                counts[(ns, sg, "title")] += 1
            for sg in m.tags_hits.get(ns, set()):
                counts[(ns, sg, "tags")] += 1

    rows: List[Tuple[str, str, str, int]] = []
    for (ns, sg, field), n in sorted(counts.items()):
        rows.append((ns, sg, field, n))
    return rows

def aggregate_outcomes(results: Iterable[MatchResult], namespaces: List[str]) -> List[Tuple[str, str, int, float, float, float, float]]:
    """
    For each subgroup (in any field), compute outcome summaries.
    If a video hits the subgroup in either title or tags, it counts for that subgroup.
    """
    buckets: Dict[Tuple[str, str], List[Tuple[int, float]]] = defaultdict(list)  # (ns, sg) -> [(views, rating), ...]
    for m in results:
        for ns in namespaces:
            sgs = set()
            sgs |= m.title_hits.get(ns, set())
            sgs |= m.tags_hits.get(ns, set())
            for sg in sgs:
                buckets[(ns, sg)].append((m.views, m.rating))

    rows: List[Tuple[str, str, int, float, float, float, float]] = []
    for (ns, sg), vals in sorted(buckets.items()):
        v = np.array([x for x, _ in vals], dtype=float)
        r = np.array([y for _, y in vals], dtype=float)
        n = len(vals)
        views_mean, views_median = float(np.nanmean(v)), float(np.nanmedian(v))
        rating_mean, rating_median = float(np.nanmean(r)), float(np.nanmedian(r))
        rows.append((ns, sg, n, views_mean, views_median, rating_mean, rating_median))
    return rows

def build_overlap(results: Iterable[MatchResult], namespace: str) -> Tuple[List[str], np.ndarray]:
    """
    Build Jaccard overlap matrix for a given namespace using sets of video_ids per subgroup.
    """
    sets_by_sg: Dict[str, Set[int]] = defaultdict(set)
    for m in results:
        sgs = set()
        sgs |= m.title_hits.get(namespace, set())
        sgs |= m.tags_hits.get(namespace, set())
        for sg in sgs:
            sets_by_sg[sg].add(m.vid)

    subgroups = sorted(sets_by_sg.keys())
    if len(subgroups) < 2:
        return subgroups, np.zeros((len(subgroups), len(subgroups)))

    n = len(subgroups)
    mat = np.zeros((n, n), dtype=float)
    for i, sgi in enumerate(subgroups):
        Ai = sets_by_sg[sgi]
        for j, sgj in enumerate(subgroups):
            Aj = sets_by_sg[sgj]
            inter = len(Ai & Aj)
            union = len(Ai | Aj) or 1
            mat[i, j] = inter / union
    return subgroups, mat

# --------------------------------------------------------------------------------------
# Plotting (two themes: light/dark)
# --------------------------------------------------------------------------------------

def _save_dual_themes(save_path_stem: Path, plot_fn) -> None:
    """
    Call plot_fn() to draw on current figure/axes. Save two versions:
    *_light.png and *_dark.png using matplotlib styles (no colormap specified).
    """
    # Light
    plt.style.use("default")
    fig = plt.figure(figsize=(10, 6), dpi=150)
    try:
        plot_fn()
        fig.tight_layout()
        fig.savefig(f"{save_path_stem}_light.png")
    finally:
        plt.close(fig)

    # Dark
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(10, 6), dpi=150)
    try:
        plot_fn()
        fig.tight_layout()
        fig.savefig(f"{save_path_stem}_dark.png")
    finally:
        plt.close(fig)

def plot_coverage_bar(ns: str, cov_rows: List[Tuple[str, str, str, int]], total: int, out_dir: Path) -> None:
    """
    Bar chart of coverage by subgroup (stacked title vs tags).
    """
    # pivot counts
    from collections import defaultdict
    counts = defaultdict(lambda: {"title": 0, "tags": 0})
    for _ns, sg, field, n in cov_rows:
        if _ns != ns:
            continue
        counts[sg][field] = n
    subgroups = sorted(counts.keys())
    title_vals = [counts[sg]["title"] for sg in subgroups]
    tags_vals  = [counts[sg]["tags"]  for sg in subgroups]

    def _draw():
        x = np.arange(len(subgroups))
        width = 0.6
        plt.bar(x, tags_vals, width=width, label="tags")
        plt.bar(x, title_vals, width=width, bottom=tags_vals, label="title")
        plt.xticks(x, subgroups, rotation=45, ha="right")
        plt.ylabel("videos (count)")
        plt.title(f"Coverage by subgroup • {ns} (N={total:,})")
        plt.legend()

    _save_dual_themes(out_dir / f"v1_coverage_{ns}", _draw)

def plot_outcomes_bar(ns: str, out_rows: List[Tuple[str, str, int, float, float, float, float]], total: int, out_dir: Path) -> None:
    """
    Bar chart of subgroup mean rating (and annotate n).
    """
    rows = [r for r in out_rows if r[0] == ns]
    if not rows:
        return
    rows.sort(key=lambda x: x[5], reverse=True)  # sort by rating_mean desc

    labels = [r[1] for r in rows]
    n_vals = [r[2] for r in rows]
    rating_mean = [r[5] for r in rows]
    views_median = [r[4] for r in rows]

    def _draw():
        x = np.arange(len(labels))
        plt.bar(x, rating_mean, width=0.6)
        for xi, n in zip(x, n_vals):
            plt.text(xi, rating_mean[labels.index(labels[int(xi)])] + 0.1, f"n={n}", ha="center", va="bottom", fontsize=8, rotation=90)
        plt.xticks(x, labels, rotation=45, ha="right")
        plt.ylabel("mean rating")
        plt.title(f"Subgroup outcomes • {ns} (N={total:,})")

    _save_dual_themes(out_dir / f"v1_outcomes_{ns}", _draw)

# --------------------------------------------------------------------------------------
# CSV writers
# --------------------------------------------------------------------------------------

def write_csv(path: Path, header: List[str], rows: Iterable[Tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="RQ1 Evidence Pack: coverage, outcomes, overlaps.")
    parser.add_argument("--lexicon", type=str, default=None, help="Path to protected_terms.json")
    parser.add_argument("--boundary", type=str, default="word", choices=["word", "edge", "none"])
    parser.add_argument("--limit", type=int, default=None, help="Optional limit of active videos for quick runs")
    parser.add_argument("--batch_size", type=int, default=20000, help="Batch size for matching")
    args = parser.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="RQ1 evidence pack")

    # Load lexicon
    lex_path = Path(args.lexicon) if args.lexicon else (cfg.paths.root / DEFAULT_LEXICON_REL)
    if not lex_path.exists():
        raise FileNotFoundError(f"Lexicon file not found: {lex_path}")
    lex = ProtectedLexicon.from_json(lex_path).compile(boundary=args.boundary)

    # DB connect + tag aggregation
    conn = connect(cfg.paths.database)
    ensure_temp_tag_agg(conn)

    # Iterate & match
    namespaces = sorted(list(lex.compiled.keys()))
    total_active = conn.execute("SELECT COUNT(*) FROM videos WHERE is_active = 1").fetchone()[0]
    total = min(total_active, args.limit) if args.limit is not None else total_active

    all_results: List[MatchResult] = []
    processed = 0
    for batch in iter_video_batches(conn, limit=args.limit, batch_size=args.batch_size):
        res = match_batch(batch, lex)
        all_results.extend(res)
        processed += len(batch)
        if processed % (args.batch_size * 2) == 0 or processed == total:
            print(f"[prog] matched {processed}/{total} videos...")

    # Aggregations
    cov_rows = aggregate_coverage(all_results, namespaces)  # ns,sg,field,n
    # add shares
    cov_rows_with_share = [(ns, sg, field, n, n / total if total else 0.0) for (ns, sg, field, n) in cov_rows]
    out_rows = aggregate_outcomes(all_results, namespaces)  # ns,sg,n,views_mean,views_median,rating_mean,rating_median
    out_rows_with_share = [(ns, sg, n, n / total if total else 0.0, vm, vmed, rm, rmed)
                           for (ns, sg, n, vm, vmed, rm, rmed) in out_rows]

    # Write CSVs
    metrics_dir = cfg.paths.metrics
    write_csv(metrics_dir / "v1_coverage_by_field.csv",
              ["namespace", "subgroup", "field", "n_videos", "share"],
              cov_rows_with_share)
    write_csv(metrics_dir / "v1_subgroup_outcomes.csv",
              ["namespace", "subgroup", "n_videos", "share", "views_mean", "views_median", "rating_mean", "rating_median"],
              out_rows_with_share)

    # Overlap matrices + plots
    figures_dir = cfg.paths.figures
    for ns in namespaces:
        # Figures: coverage stacked bars and outcome bars
        plot_coverage_bar(ns, cov_rows, total, figures_dir)
        plot_outcomes_bar(ns, out_rows, total, figures_dir)

        # Overlap CSV
        labels, mat = build_overlap(all_results, ns)
        if len(labels) >= 2:
            # Save numeric matrix
            mpath = metrics_dir / f"v1_overlap_matrix_{ns}.csv"
            write_csv(mpath, [""] + labels, [(labels[i], *mat[i, :].tolist()) for i in range(len(labels))])

    print("[done] RQ1 evidence pack complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
