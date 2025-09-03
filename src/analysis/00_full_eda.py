"""
src/analysis/00_full_eda.py

Purpose
-------
Comprehensive, reproducible EDA over the RedTube metadata for:
1) Dataset profile & distributions (duration, views, ratings, title length).
2) Temporal trends (monthly volume, median rating, median views).
3) Tags & categories coverage (top-N, long tail) + export of frequency tables.
4) Protected subgroup analysis using the compiled lexicon:
   - Coverage in titles vs tags
   - Intersectional cross-tabs (e.g., gender x race_ethnicity)
   - Collocations between protected subgroups and stereotype_terms (counts & PMI)
5) Tag co-occurrence PMI among frequent tags (top-K, min-count thresholds).

Outputs (all reproducible)
--------------------------
CSV (reports/metrics/):
- v0eda_dataset_profile.csv
- v0eda_monthly_summary.csv
- v0eda_top_tags.csv
- v0eda_top_categories.csv
- v0eda_intersection_gender_race.csv
- v0eda_colloc_stereotypes.csv
- v0eda_tag_cooccurrence_pmi.csv

Figures (reports/figures/, both light & dark variants):
- v0eda_hist_views_{light|dark}.png
- v0eda_hist_rating_{light|dark}.png
- v0eda_hist_duration_{light|dark}.png
- v0eda_hist_title_len_{light|dark}.png
- v0eda_monthly_counts_{light|dark}.png
- v0eda_monthly_rating_median_{light|dark}.png
- v0eda_top_tags_{light|dark}.png
- v0eda_top_categories_{light|dark}.png
- v0eda_intersection_gender_race_{light|dark}.png  (stacked bars)

Design notes
------------
- Uses only matplotlib (no seaborn). No explicit colormaps; no viridis.
- Exposes CLI parameters to control runtime on large DBs.
- Reuses temp aggregation patterns to keep memory low (streaming/batched).

Links to RQs
------------
- RQ1: Current categorisation (coverage; temporal; top tags/categories).
- RQ2-3: Provides clean, joined corpora stats for model features & group metrics.
- RQ4: Collocation & PMI signal potential mitigation targets.
- RQ5: Quantifies areas of societal concern (e.g., stereotypes co-labelling).

"""

from __future__ import annotations
import argparse
import csv
import math
import sqlite3
from collections import defaultdict, Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

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


# ---------------------------- DB helpers ----------------------------

def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def ensure_temp_tag_agg(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS temp_vt_agg")
    conn.execute("""
        CREATE TEMP TABLE temp_vt_agg AS
        SELECT video_id, GROUP_CONCAT(tag, ' ') AS tags
        FROM video_tags
        GROUP BY video_id
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_vt_agg_vid ON temp_vt_agg(video_id)")

# ------------------------- generic I/O utils ------------------------

def write_csv(path: Path, header: List[str], rows: Iterable[Iterable]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)

def _save_dual(save_stem: Path, draw_fn) -> None:
    # Light
    plt.style.use("default")
    fig = plt.figure(figsize=(10, 6), dpi=150)
    try:
        draw_fn()
        fig.tight_layout()
        fig.savefig(f"{save_stem}_light.png")
    finally:
        plt.close(fig)
    # Dark
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(10, 6), dpi=150)
    try:
        draw_fn()
        fig.tight_layout()
        fig.savefig(f"{save_stem}_dark.png")
    finally:
        plt.close(fig)

# ------------------------------ EDA ---------------------------------

def dataset_profile(conn: sqlite3.Connection, out_metrics: Path) -> Dict[str, float]:
    q = """
        SELECT
            COUNT(*) AS n_all,
            SUM(is_active=1) AS n_active,
            AVG(duration) AS duration_mean,
            AVG(views) AS views_mean,
            AVG(rating) AS rating_mean,
            SUM(ratings) AS ratings_votes
        FROM videos
    """
    row = conn.execute(q).fetchone()
    profile = {
        "n_all": int(row["n_all"] or 0),
        "n_active": int(row["n_active"] or 0),
        "duration_mean": float(row["duration_mean"] or 0.0),
        "views_mean": float(row["views_mean"] or 0.0),
        "rating_mean": float(row["rating_mean"] or 0.0),
        "ratings_votes": int(row["ratings_votes"] or 0),
    }
    write_csv(out_metrics / "v0eda_dataset_profile.csv",
              ["metric", "value"],
              profile.items())
    return profile

def histograms(conn: sqlite3.Connection, figures_dir: Path, limit: Optional[int]) -> None:
    base = "SELECT duration, views, rating, LENGTH(COALESCE(title,'')) AS title_len FROM videos WHERE is_active=1"
    if limit:
        base += f" LIMIT {int(limit)}"
    rows = conn.execute(base).fetchall()
    dur = np.array([r["duration"] for r in rows if r["duration"] is not None], dtype=float)
    vw  = np.array([r["views"] for r in rows if r["views"] is not None], dtype=float)
    rt  = np.array([r["rating"] for r in rows if r["rating"] is not None], dtype=float)
    tl  = np.array([r["title_len"] for r in rows], dtype=float)

    def draw_hist(data, title, xlabel, log=False):
        def _d():
            if log:
                data_pos = data[data > 0]
                plt.hist(np.log10(data_pos+1), bins=50)
                plt.xlabel(f"log10({xlabel}+1)")
            else:
                plt.hist(data, bins=50)
                plt.xlabel(xlabel)
            plt.ylabel("count")
            plt.title(title)
        return _d

    if len(vw) > 0:
        _save_dual(figures_dir / "v0eda_hist_views", draw_hist(vw, "Views distribution", "views", log=True))
    if len(rt) > 0:
        _save_dual(figures_dir / "v0eda_hist_rating", draw_hist(rt, "Rating distribution", "rating (0-100?)", log=False))
    if len(dur) > 0:
        _save_dual(figures_dir / "v0eda_hist_duration", draw_hist(dur, "Duration distribution", "seconds", log=False))
    if len(tl) > 0:
        _save_dual(figures_dir / "v0eda_hist_title_len", draw_hist(tl, "Title length distribution", "characters", log=False))

def monthly_trends(conn: sqlite3.Connection, figures_dir: Path, metrics_dir: Path) -> None:
    # publish_date appears as TEXT; keep month granularity
    q = """
        SELECT SUBSTR(publish_date,1,7) AS ym, 
               COUNT(*) AS n, 
               AVG(rating) AS rating_mean,
               CAST(AVG(views) AS FLOAT) AS views_mean,
               CAST(MEDIAN(views) AS FLOAT) AS views_median
        FROM videos
        WHERE is_active=1 AND publish_date IS NOT NULL
        GROUP BY ym
        ORDER BY ym
    """
    # SQLite default lacks MEDIAN; fallback to approximate via percentile
    conn.create_aggregate("MEDIAN", 1, _MedianAgg)
    rows = conn.execute(q).fetchall()
    write_csv(metrics_dir / "v0eda_monthly_summary.csv",
              ["ym","n","rating_mean","views_mean","views_median"],
              [(r["ym"], r["n"], r["rating_mean"], r["views_mean"], r["views_median"]) for r in rows])

    ym = [r["ym"] for r in rows]
    n  = [r["n"] for r in rows]
    rmean = [r["rating_mean"] for r in rows]
    vmed  = [r["views_median"] for r in rows]

    def draw_counts():
        x = np.arange(len(ym))
        plt.plot(x, n, linewidth=2)
        plt.xticks(x[::max(1, len(x)//12)], [ym[i] for i in range(0,len(ym), max(1,len(ym)//12))], rotation=45, ha="right")
        plt.ylabel("videos per month")
        plt.title("Monthly active videos")
    _save_dual(figures_dir / "v0eda_monthly_counts", draw_counts)

    def draw_rating_med():
        x = np.arange(len(ym))
        plt.plot(x, rmean, linewidth=2)
        plt.xticks(x[::max(1, len(x)//12)], [ym[i] for i in range(0,len(ym), max(1,len(ym)//12))], rotation=45, ha="right")
        plt.ylabel("mean rating")
        plt.title("Monthly mean rating (active videos)")
    _save_dual(figures_dir / "v0eda_monthly_rating_median", draw_rating_med)

class _MedianAgg:
    def __init__(self):
        self.data = []
    def step(self, value):
        if value is not None:
            self.data.append(float(value))
    def finalize(self):
        if not self.data:
            return None
        arr = np.array(self.data, dtype=float)
        return float(np.median(arr))

def top_tags_categories(conn: sqlite3.Connection, figures_dir: Path, metrics_dir: Path,
                        top_k: int, min_count: int) -> None:
    # Top tags
    q_tags = f"""
        SELECT tag AS name, COUNT(*) AS c
        FROM video_tags
        GROUP BY tag
        HAVING c >= {int(min_count)}
        ORDER BY c DESC
        LIMIT {int(top_k)}
    """
    tags = conn.execute(q_tags).fetchall()
    write_csv(metrics_dir / "v0eda_top_tags.csv", ["tag","count"], [(r["name"], r["c"]) for r in tags])

    # Top categories
    q_cat = f"""
        SELECT category AS name, COUNT(*) AS c
        FROM video_categories
        GROUP BY category
        ORDER BY c DESC
        LIMIT {int(top_k)}
    """
    cats = conn.execute(q_cat).fetchall()
    write_csv(metrics_dir / "v0eda_top_categories.csv", ["category","count"], [(r["name"], r["c"]) for r in cats])

    def draw_bar(items, title, xlabel, save_stem):
        labels = [r["name"] for r in items][::-1]
        counts = [r["c"] for r in items][::-1]
        def _d():
            y = np.arange(len(labels))
            plt.barh(y, counts)
            plt.yticks(y, labels)
            plt.xlabel(xlabel)
            plt.title(title)
        _save_dual(figures_dir / save_stem, _d)

    if tags:
        draw_bar(tags[:50], "Top tags (head of distribution)", "count", "v0eda_top_tags")
    if cats:
        draw_bar(cats[:50], "Top categories (head of distribution)", "count", "v0eda_top_categories")

# ---------------- Protected-group EDA (intersection & collocations) ------------------

@dataclass(frozen=True)
class Match:
    vid: int
    ns2title: Dict[str, Set[str]]
    ns2tags: Dict[str, Set[str]]

def _iter_active_with_tags(conn: sqlite3.Connection, limit: Optional[int], batch_size: int) -> Iterable[List[sqlite3.Row]]:
    base = """
        SELECT v.video_id, v.title, COALESCE(t.tags,'') AS tags
        FROM videos v
        LEFT JOIN temp_vt_agg t ON t.video_id = v.video_id
        WHERE v.is_active = 1
        ORDER BY v.video_id
    """
    if limit:
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

def lexicon_match(rows: List[sqlite3.Row], lex: ProtectedLexicon) -> List[Match]:
    out: List[Match] = []
    for r in rows:
        vid = int(r["video_id"])
        title = (r["title"] or "").lower()
        tags = (r["tags"] or "").lower()
        ns2title: Dict[str, Set[str]] = defaultdict(set)
        ns2tags: Dict[str, Set[str]] = defaultdict(set)
        for ns, cns in lex.compiled.items():
            for sg, cg in cns.groups.items():
                if any(p.search(title) for p in cg.patterns):
                    ns2title[ns].add(sg)
                if any(p.search(tags) for p in cg.patterns):
                    ns2tags[ns].add(sg)
        out.append(Match(vid, ns2title, ns2tags))
    return out

def intersection_gender_race(matches: Iterable[Match], metrics_dir: Path, figures_dir: Path) -> None:
    # Build per-video sets and then cross-tab counts
    cnt: Dict[Tuple[str,str], int] = Counter()
    for m in matches:
        g = m.ns2title.get("gender", set()) | m.ns2tags.get("gender", set())
        r = m.ns2title.get("race_ethnicity", set()) | m.ns2tags.get("race_ethnicity", set())
        for gg in g:
            for rr in r:
                cnt[(gg, rr)] += 1

    # CSV
    rows = [("gender","race_ethnicity","n_videos")]
    rows += [(g, r, n) for (g, r), n in sorted(cnt.items(), key=lambda x: (-x[1], x[0][0], x[0][1]))]
    write_csv(metrics_dir / "v0eda_intersection_gender_race.csv", rows[0], rows[1:])

    # Figure (stacked bars by gender)
    genders = sorted({g for (g, _), _ in cnt.items()})
    races   = sorted({r for (_, r), _ in cnt.items()})
    mat = np.zeros((len(genders), len(races)), dtype=float)
    for i, g in enumerate(genders):
        for j, r in enumerate(races):
            mat[i, j] = cnt.get((g, r), 0)

    def _draw():
        x = np.arange(len(genders))
        bottom = np.zeros(len(genders))
        for j, r in enumerate(races):
            vals = mat[:, j]
            plt.bar(x, vals, bottom=bottom, label=r)
            bottom += vals
        plt.xticks(x, genders, rotation=0)
        plt.ylabel("videos")
        plt.title("Intersection: gender × race_ethnicity (matched in title OR tags)")
        plt.legend(fontsize=8, ncol=2)
    _save_dual(figures_dir / "v0eda_intersection_gender_race", _draw)

def collocations_with_stereotypes(matches: Iterable[Match], metrics_dir: Path) -> None:
    # Count co-appearance between each subgroup (from any namespace except stereotype_terms)
    # and stereotype_terms subgroups, per video (OR over title/tags).
    colloc: Dict[Tuple[str, str], int] = Counter()
    left_freq: Dict[str, int] = Counter()     # subgroup (e.g., race 'black')
    right_freq: Dict[str, int] = Counter()    # stereotype subgroup (e.g., 'violence_degradation')
    videos_any = 0

    for m in matches:
        videos_any += 1
        # union sets
        ns2 = defaultdict(set)
        for ns, s in m.ns2title.items(): ns2[ns] |= s
        for ns, s in m.ns2tags.items():  ns2[ns] |= s

        stereos = ns2.get("stereotype_terms", set())
        # Left candidates = all subgroups except stereotype_terms
        left = set()
        for ns, sgs in ns2.items():
            if ns == "stereotype_terms": 
                continue
            left |= {f"{ns}:{sg}" for sg in sgs}

        # Count
        for L in left:
            left_freq[L] += 1
        for S in stereos:
            right_freq[S] += 1
        for L in left:
            for S in stereos:
                colloc[(L, S)] += 1

    # Compute PMI using videos_any as universe (standard, simple)
    rows = []
    for (L, S), c in colloc.items():
        p_xy = c / max(1, videos_any)
        p_x  = left_freq[L] / max(1, videos_any)
        p_y  = right_freq[S] / max(1, videos_any)
        denom = p_x * p_y if p_x > 0 and p_y > 0 else np.nan
        pmi = float(np.log2(p_xy / denom)) if denom and p_xy > 0 else float("-inf")
        rows.append((L, S, c, left_freq[L], right_freq[S], pmi))

    rows.sort(key=lambda x: (-x[5], -x[2]))
    write_csv(metrics_dir / "v0eda_colloc_stereotypes.csv",
              ["left_subgroup","stereotype_group","co_videos","left_videos","stereo_videos","PMI"],
              rows)

# ------------------------- Tag co-occurrence PMI --------------------

def tag_pmi(conn: sqlite3.Connection, metrics_dir: Path, top_k: int, min_tag_count: int, min_pair_count: int) -> None:
    # Select frequent tags (top_k with min_count)
    conn.execute("DROP TABLE IF EXISTS temp_top_tags")
    conn.execute(f"""
        CREATE TEMP TABLE temp_top_tags AS
        SELECT tag, COUNT(*) AS c
        FROM video_tags
        GROUP BY tag
        HAVING c >= {int(min_tag_count)}
        ORDER BY c DESC
        LIMIT {int(top_k)}
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_top_tags_tag ON temp_top_tags(tag)")

    conn.execute("DROP TABLE IF EXISTS temp_vtt")
    conn.execute("""
        CREATE TEMP TABLE temp_vtt AS
        SELECT vt.video_id, vt.tag
        FROM video_tags vt
        JOIN temp_top_tags tt ON tt.tag = vt.tag
        GROUP BY vt.video_id, vt.tag
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_vtt_vid ON temp_vtt(video_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_temp_vtt_tag ON temp_vtt(tag)")

    # Frequencies
    tag_freq = {r["tag"]: r["c"] for r in conn.execute("SELECT tag, COUNT(*) AS c FROM temp_vtt GROUP BY tag").fetchall()}
    n_videos = conn.execute("SELECT COUNT(DISTINCT video_id) AS n FROM temp_vtt").fetchone()["n"] or 1

    # Co-occurrence (upper triangle)
    q_pairs = f"""
        SELECT a.tag AS t1, b.tag AS t2, COUNT(*) AS c
        FROM temp_vtt a
        JOIN temp_vtt b ON a.video_id = b.video_id AND a.tag < b.tag
        GROUP BY a.tag, b.tag
        HAVING c >= {int(min_pair_count)}
    """
    rows = conn.execute(q_pairs).fetchall()
    out = []
    for r in rows:
        t1, t2, c = r["t1"], r["t2"], int(r["c"])
        p_xy = c / n_videos
        p_x  = tag_freq.get(t1, 0) / n_videos
        p_y  = tag_freq.get(t2, 0) / n_videos
        denom = p_x * p_y if p_x > 0 and p_y > 0 else np.nan
        pmi = float(np.log2(p_xy / denom)) if denom and p_xy > 0 else float("-inf")
        out.append((t1, t2, c, tag_freq.get(t1, 0), tag_freq.get(t2, 0), pmi))
    out.sort(key=lambda x: (-x[5], -x[2]))
    write_csv(metrics_dir / "v0eda_tag_cooccurrence_pmi.csv",
              ["tag1","tag2","co_videos","tag1_videos","tag2_videos","PMI"],
              out)

# ------------------------------- Main -------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Full EDA: profile, trends, tags/categories, intersections, PMI.")
    ap.add_argument("--limit", type=int, default=None, help="Optional limit of active videos for sampling")
    ap.add_argument("--batch_size", type=int, default=20000, help="Batch size for lexicon matching")
    ap.add_argument("--top_k", type=int, default=500, help="Top-K frequent tags to consider")
    ap.add_argument("--min_tag_count", type=int, default=1000, help="Min per-tag count for PMI pool")
    ap.add_argument("--min_pair_count", type=int, default=50, help="Min co-occurrence count for PMI edges")
    args = ap.parse_args()

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="Full EDA")

    # Connect & prep
    conn = connect(cfg.paths.database)
    ensure_temp_tag_agg(conn)

    metrics_dir = cfg.paths.metrics
    figures_dir = cfg.paths.figures

    # 1) Profile + histograms
    prof = dataset_profile(conn, metrics_dir)
    histograms(conn, figures_dir, limit=args.limit)

    # 2) Monthly trends
    monthly_trends(conn, figures_dir, metrics_dir)

    # 3) Top tags & categories (heads)
    top_tags_categories(conn, figures_dir, metrics_dir, top_k=args.top_k, min_count=args.min_tag_count)

    # 4) Protected-group EDA (intersection, collocations)
    # Load lexicon
    lex_path = cfg.paths.root / DEFAULT_LEXICON_REL
    if not lex_path.exists():
        raise FileNotFoundError(f"Lexicon file not found: {lex_path}")
    lex = ProtectedLexicon.from_json(lex_path).compile(boundary="word")

    # Stream videos for matching
    all_matches: List[Match] = []
    processed = 0
    for batch in _iter_active_with_tags(conn, limit=args.limit, batch_size=args.batch_size):
        all_matches.extend(lexicon_match(batch, lex))
        processed += len(batch)
        if processed % (args.batch_size * 2) == 0:
            print(f"[prog] matched {processed} videos for protected-group EDA...")

    # Intersection: gender x race_ethnicity
    intersection_gender_race(all_matches, metrics_dir, figures_dir)

    # Collocations with stereotype terms
    collocations_with_stereotypes(all_matches, metrics_dir)

    # 5) Tag co-occurrence PMI (frequent tags)
    tag_pmi(conn, metrics_dir, top_k=args.top_k, min_tag_count=args.min_tag_count, min_pair_count=args.min_pair_count)

    print("[done] Full EDA complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
