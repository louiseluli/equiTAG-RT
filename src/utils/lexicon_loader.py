# path: src/utils/lexicon_loader.py
"""
Protected lexicon loader & validator for fairness auditing.

Purpose
-------
- Load a hierarchical JSON lexicon of protected attributes and stereotype markers.
- Validate structure, normalise terms, and compile boundary-safe regex patterns.
- Provide a simple matcher API for titles/tags and a CLI to emit an audit JSON.

Key features
------------
- Word-boundary guarding: avoids substring false positives (e.g., "asian" != "caucasian").
- Multi-word phrases supported (spaces -> \s+).
- Wildcards supported: '*' -> '.*' (greedy, use sparingly).
- Case-insensitive, Unicode-safe.
- Duplicate and cross-namespace overlap detection (informational).

Inputs
------
- JSON file (default: config/protected_terms.json) with a structure like:
  {
    "race_ethnicity": {"black": ["ebony", "afro", "black", "bbc"], ...},
    "nationality": {"brazilian": ["brazil*", "brasileir*"], ...},
    "gender": {...},
    "sexuality": {...},
    "age": {...},
    "hair_color": {...},
    "stereotype_terms": {...}
  }

Outputs (via CLI)
-----------------
- reports/metrics/v0_lexicon_audit.json   # counts, duplicates, overlaps

Assumptions
-----------
- The lexicon is curated for the adult content domain and reviewed for harms.
- We keep "genre/flag" terms (e.g., "hentai") but they can be flagged upstream.

Failure modes
-------------
- Missing or malformed JSON -> raises FileNotFoundError / ValueError.
- Empty namespaces or subgroups -> recorded in audit (not fatal).

Complexity
----------
- O(T) to compile T terms; matching is O(T) per text (typically small constants).

Test notes
----------
- Run: python -m src.utils.lexicon_loader --audit
- Verify JSON audit is created and console prints sane counts.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Pattern, Tuple, Iterable, Any, Optional, DefaultDict
from collections import defaultdict

from src.utils.config_loader import (
    load_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)


# ----------------------------- Helpers & types -----------------------------

Namespace = str       # e.g., "race_ethnicity"
Subgroup = str        # e.g., "black"
Term = str

@dataclass(frozen=True)
class CompiledTerm:
    raw: Term
    pattern: Pattern[str]


@dataclass
class ProtectedLexicon:
    terms: Dict[Namespace, Dict[Subgroup, List[Term]]]
    patterns: Dict[Namespace, Dict[Subgroup, List[CompiledTerm]]]

    @classmethod
    def from_json(cls, path: Path) -> "ProtectedLexicon":
        if not path.exists():
            raise FileNotFoundError(f"Lexicon file not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("Top-level lexicon JSON must be an object/dict.")

        # Ensure nesting is dict -> dict -> list[str]
        for ns, groups in raw.items():
            if not isinstance(groups, dict):
                raise ValueError(f"Namespace '{ns}' must map to an object of subgroups.")
            for sg, terms in groups.items():
                if not isinstance(terms, list) or not all(isinstance(t, str) for t in terms):
                    raise ValueError(f"Subgroup '{ns}.{sg}' must be a list of strings.")
        return cls(terms=raw, patterns=defaultdict(dict))  # type: ignore[assignment]

    def compile(self, boundary: str = "word") -> "ProtectedLexicon":
        """
        Compile regex patterns for each term with boundary guards.

        boundary: "word" -> \\b guards
                  "edge" -> (?<!\\w)...(?!\\w) guards (safer on some unicode cases)
        """
        compiled: Dict[Namespace, Dict[Subgroup, List[CompiledTerm]]] = {}
        for ns, groups in self.terms.items():
            compiled[ns] = {}
            for sg, term_list in groups.items():
                uniq_terms = _dedupe_preserve(term_list)
                compiled[ns][sg] = [CompiledTerm(raw=t, pattern=_compile_term(t, boundary)) for t in uniq_terms]
        self.patterns = compiled
        return self

    def match_text(self, text: str) -> Dict[Tuple[Namespace, Subgroup], List[str]]:
        """
        Return a mapping {(namespace, subgroup): [matched_terms...]} for the given text.
        Duplicates removed per (ns, sg).
        """
        hits: Dict[Tuple[Namespace, Subgroup], List[str]] = {}
        if not text:
            return hits
        for ns, groups in self.patterns.items():
            for sg, plist in groups.items():
                matched: List[str] = []
                for ct in plist:
                    if ct.pattern.search(text):
                        matched.append(ct.raw)
                if matched:
                    # dedupe to keep stable output
                    hits[(ns, sg)] = _dedupe_preserve(matched)
        return hits

    def audit(self) -> Dict[str, Any]:
        """
        Basic counts + duplicates across namespaces/subgroups (by exact normalised term).
        """
        total_ns = len(self.terms)
        total_sg = sum(len(g) for g in self.terms.values())
        total_terms = 0

        # Collect term -> list[(ns, sg)]
        index: DefaultDict[str, List[Tuple[str, str]]] = defaultdict(list)
        empty_groups: List[Tuple[str, str]] = []
        for ns, groups in self.terms.items():
            for sg, terms in groups.items():
                if not terms:
                    empty_groups.append((ns, sg))
                for t in terms:
                    norm = _normalise_term(t)
                    index[norm].append((ns, sg))
                    total_terms += 1

        # Duplicates across multiple (ns, sg)
        overlaps = {
            term: pairs for term, pairs in index.items() if len(pairs) > 1
        }

        return {
            "namespaces": total_ns,
            "subgroups": total_sg,
            "terms": total_terms,
            "empty_groups": empty_groups,
            "overlap_terms_count": len(overlaps),
            "overlap_examples": dict(list(overlaps.items())[:50]),  # cap for readability
        }


# ----------------------------- Compilation utils -----------------------------

_WORD_EDGE_LEFT = r"(?<!\w)"
_WORD_EDGE_RIGHT = r"(?!\w)"

def _normalise_term(t: str) -> str:
    return t.strip().lower()

def _escape_wildcards(term: str) -> str:
    """
    Escape regex special chars except '*' which we convert to '.*'
    """
    # First escape everything, then re-enable '*' wildcard
    esc = re.escape(term)
    esc = esc.replace(r"\*", ".*")
    return esc

def _compile_term(term: str, boundary: str = "word") -> Pattern[str]:
    """
    Build a robust regex:
    - spaces -> \\s+ (handles multiple spaces or separators)
    - '*' -> '.*' wildcard
    - boundaries -> \\b or (?<!\\w) ... (?!\\w)
    """
    raw = _normalise_term(term)
    # Replace spaces with \s+ (tolerant phrase matching)
    raw = re.sub(r"\s+", r" ", raw)
    esc = _escape_wildcards(raw)
    esc = esc.replace(" ", r"\s+")
    core = f"(?:{esc})"
    if boundary == "edge":
        pat = f"{_WORD_EDGE_LEFT}{core}{_WORD_EDGE_RIGHT}"
    else:
        # default 'word' boundary; may underperform with some unicode scripts
        pat = rf"\b{core}\b"
    return re.compile(pat, flags=re.IGNORECASE | re.UNICODE)


def _dedupe_preserve(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ----------------------------- CLI & I/O -----------------------------

def _load_or_fail(lex_path: Optional[Path]) -> ProtectedLexicon:
    cfg = load_config()
    default_path = Path(lex_path) if lex_path else cfg.paths.config_dir / "protected_terms.json"
    lex = ProtectedLexicon.from_json(default_path).compile(boundary="edge")
    return lex

def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def _cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Protected lexicon loader & audit")
    parser.add_argument("--lexicon", type=str, default=None, help="Path to protected_terms.json (optional).")
    parser.add_argument("--audit", action="store_true", help="Emit audit JSON to reports/metrics.")
    parser.add_argument("--sample", type=str, default=None, help="Optional sample text to test matching.")
    args = parser.parse_args(argv)

    cfg = load_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    device_info = pick_device()
    print_run_header(cfg, device_info, note="lexicon loader")

    lex = _load_or_fail(Path(args.lexicon) if args.lexicon else None)

    # Sample test
    if args.sample is not None:
        hits = lex.match_text(args.sample)
        print(f"[demo] sample text: {args.sample}")
        for (ns, sg), terms in hits.items():
            print(f"       hit: {ns}.{sg} <- {terms}")

    if args.audit:
        audit = lex.audit()
        out = cfg.paths.metrics / "v0_lexicon_audit.json"
        _write_json(out, audit)
        print(f"[ok] Wrote lexicon audit JSON → {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
