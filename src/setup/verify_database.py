"""
src/setup/verify_database.py

Purpose
-------
Sanity-check and profile the SQLite database used in this project. This produces:
1) JSON profile with table schemas, indices, foreign keys, row counts.
2) A small CSV sample of videos with aggregated tags (for quick EDA sanity).
3) Console output summarising key findings.

Inputs
------
- config/config.yaml: paths.database -> SQLite file location.

Outputs
-------
- reports/metrics/v0_db_profile.json
- reports/metrics/v0_sample_videos.csv

Assumptions
-----------
- Schema includes (at least): videos, video_tags, video_categories, category_status, collection_state, audit_terms.
- `video_tags` has columns (video_id INTEGER, tag TEXT).
- No `tags` lookup table is required (we aggregate from `video_tags.tag`).

Failure Modes
-------------
- Missing DB file or unreadable path -> exits with non-zero code.
- Missing expected tables -> records in "schema_diffs" and prints warnings (continues).
- Very large DB: only small samples are materialised to CSV to avoid memory issues.

Complexity
----------
- O(1) memory except for small samples; queries are counted/aggregated in SQL.

Test Notes
----------
- Run on a small copied DB; verify both artifacts are created.
- Check JSON "tables" entries and that row counts look plausible.
"""

from __future__ import annotations
import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Tuple

try:
    import yaml  # pyyaml
except ImportError:
    print("Please install pyyaml (pip install pyyaml)", file=sys.stderr)
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"
METRICS_DIR = PROJECT_ROOT / "reports" / "metrics"


@dataclass
class ColumnInfo:
    cid: int
    name: str
    type: str
    notnull: int
    dflt_value: Any
    pk: int


@dataclass
class IndexInfo:
    name: str
    unique: int
    origin: str
    partial: int


@dataclass
class TableProfile:
    row_count: int
    columns: List[ColumnInfo]
    indices: List[IndexInfo]
    foreign_keys: List[Dict[str, Any]]


def load_config(cfg_path: Path) -> Dict[str, Any]:
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    with cfg_path.open("r") as f:
        return yaml.safe_load(f)


def connect_sqlite(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    # Default connection; WAL etc. not required for read-only profiling
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> List[str]:
    sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    return [r["name"] for r in conn.execute(sql).fetchall()]


def pragma_table_info(conn: sqlite3.Connection, table: str) -> List[ColumnInfo]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [ColumnInfo(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]


def pragma_index_list(conn: sqlite3.Connection, table: str) -> List[IndexInfo]:
    rows = conn.execute(f"PRAGMA index_list({table})").fetchall()
    return [IndexInfo(r["name"], r["unique"], r["origin"], r["partial"]) for r in rows]


def pragma_foreign_keys(conn: sqlite3.Connection, table: str) -> List[Dict[str, Any]]:
    rows = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
    return [dict(r) for r in rows]


def count_rows(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]


def sample_videos_with_tags(conn: sqlite3.Connection, n: int = 100) -> List[Dict[str, Any]]:
    """
    Aggregate tags directly from video_tags.tag (no separate tags table exists).
    """
    sql = """
    WITH vt AS (
        SELECT video_id, GROUP_CONCAT(tag, ' ') AS tags
        FROM video_tags
        GROUP BY video_id
    )
    SELECT v.video_id, v.title, v.duration, v.views, v.rating, v.ratings, v.publish_date,
           v.category_source, v.is_active, vt.tags
    FROM videos v
    LEFT JOIN vt ON vt.video_id = v.video_id
    ORDER BY v.video_id
    LIMIT ?;
    """
    rows = conn.execute(sql, (n,)).fetchall()
    return [dict(r) for r in rows]


def to_json_serialisable(profile: Dict[str, TableProfile]) -> Dict[str, Any]:
    out = {}
    for t, p in profile.items():
        out[t] = {
            "row_count": p.row_count,
            "columns": [asdict(c) for c in p.columns],
            "indices": [asdict(i) for i in p.indices],
            "foreign_keys": p.foreign_keys,
        }
    return out


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile SQLite DB for equiTAG-RT.")
    parser.add_argument("--db", type=str, default=None, help="Optional path override to SQLite DB.")
    parser.add_argument("--sample_n", type=int, default=100, help="Rows to sample for CSV.")
    args = parser.parse_args(argv)

    cfg = load_config(CONFIG_FILE)
    db_path = Path(args.db) if args.db else PROJECT_ROOT / cfg["paths"]["database"]
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[info] Using DB: {db_path}")

    try:
        conn = connect_sqlite(db_path)
    except FileNotFoundError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 2

    # 1) Tables present
    tables = list_tables(conn)
    print(f"[info] Found tables: {', '.join(tables)}")

    expected = {"videos", "video_tags", "video_categories", "category_status", "collection_state", "audit_terms"}
    missing = sorted(list(expected - set(tables)))
    extras = sorted(list(set(tables) - expected))
    schema_diffs: Dict[str, Any] = {"missing_tables": missing, "extra_tables": extras}

    # 2) Profile each table
    profile: Dict[str, TableProfile] = {}
    for t in tables:
        cols = pragma_table_info(conn, t)
        idxs = pragma_index_list(conn, t)
        fks = pragma_foreign_keys(conn, t)
        rc = count_rows(conn, t)
        profile[t] = TableProfile(row_count=rc, columns=cols, indices=idxs, foreign_keys=fks)
        print(f"[ok] {t:<18} rows={rc:>9}  cols={len(cols):>2}  idx={len(idxs):>2}  fks={len(fks):>2}")

    # 3) Sample CSV (videos + aggregated tags)
    sample_rows = sample_videos_with_tags(conn, n=args.sample_n)
    csv_out = METRICS_DIR / "v0_sample_videos.csv"
    # Write with csv module to avoid pandas dependency
    import csv
    if sample_rows:
        with csv_out.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(sample_rows[0].keys()))
            writer.writeheader()
            writer.writerows(sample_rows)
        print(f"[ok] Wrote sample CSV → {csv_out} (rows={len(sample_rows)})")
    else:
        print("[warn] No sample rows produced (empty videos table?).")

    # 4) JSON profile
    json_out = METRICS_DIR / "v0_db_profile.json"
    out_payload = {
        "database": str(db_path),
        "tables": to_json_serialisable(profile),
        "schema_diffs": schema_diffs,
    }
    with json_out.open("w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"[ok] Wrote DB profile JSON → {json_out}")

    # 5) Targeted checks we care about for the dissertation narrative
    #    (a) are indices on videos(publish_date) and videos(is_active) present?
    wanted_idx = {"idx_videos_publish_date", "idx_videos_is_active"}
    have_idx = {i.name for i in profile.get("videos", TableProfile(0, [], [], [])).indices}
    missing_idx = sorted(list(wanted_idx - have_idx))
    if missing_idx:
        print(f"[warn] Missing recommended indices on videos: {missing_idx}")
    else:
        print("[ok] Recommended video indices present.")

    #    (b) foreign key from video_tags.video_id -> videos.video_id?
    fks_tags = profile.get("video_tags")
    if fks_tags and fks_tags.foreign_keys:
        print("[ok] video_tags has foreign key references configured.")
    else:
        print("[warn] No foreign key references found on video_tags (not critical for reads).")

    print("[done] Database verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
