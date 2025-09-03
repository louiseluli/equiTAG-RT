r"""
src/utils/lexicon_loader.py

Purpose
-------
Load, validate, and compile a protected-terms lexicon for fairness auditing.
- Ignores top-level metadata keys (e.g., "_source_notes").
- Validates that each subgroup is a list of strings (coercing a single string to [string]).
- Supports "*" wildcard in terms (expanded to r"[\w\-]*").
- Compiles boundary-aware regex patterns with Unicode + case-insensitive flags.
- Provides an audit CLI to summarise coverage and write a JSON report.

Inputs
------
- config/protected_terms.json  (default)
- config/config.yaml           (for paths + reproducibility header)

Outputs
-------
- When run with --audit:
  reports/metrics/v0_lexicon_audit.json    (summary counts, sample patterns)

Assumptions
-----------
- Namespaces are dictionary keys grouping subgroups, e.g. "race_ethnicity": {"black": [...], ...}
- Any top-level key starting with "_" is considered metadata and ignored.

Failure Modes
-------------
- Missing or malformed JSON -> ValueError with a clear message.
- Non-list subgroup values -> coerced if string; otherwise skipped with a warning.

Complexity
----------
- O(N) in number of terms; compilation is linear in the number of patterns.

Test Notes
----------
- `python -m src.utils.lexicon_loader --audit` should print a header and write the audit JSON.
"""

from __future__ import annotations
import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from src.utils.config_loader import (
    load_config as load_project_config,
    ensure_directories,
    set_global_seed,
    pick_device,
    print_run_header,
)

META_PREFIXES = ("_",)  # ignore top-level keys that start with these
DEFAULT_LEXICON_REL = "config/protected_terms.json"

# Compile flags: case-insensitive + Unicode + DOTALL off (default)
REGEX_FLAGS = re.IGNORECASE


def _warn(msg: str) -> None:
    print(f"[warn] {msg}")


def _is_meta_key(key: str) -> bool:
    return any(key.startswith(p) for p in META_PREFIXES)


def _term_to_regex(term: str) -> str:
    r"""
    Turn a lexicon term into a safe regex fragment.
    - Escape all regex metacharacters, then re-enable "*" wildcard:
      "japan*" -> r"japan[\w\-]*"
    """
    # Escape first
    esc = re.escape(term)
    # Re-enable '*' as an alnum/hyphen word extension (Unicode word chars via \w)
    esc = esc.replace(r"\*", r"[\w\-]*")
    return esc


def _wrap_boundary(pattern: str, boundary: str) -> str:
    r"""
    boundary in {"word", "edge", "none"}:
      - "word": wrap with \b..\b  (Unicode-aware word boundaries in Python)
      - "edge": similar to "word" but tolerant of punctuation edges (here same as "word")
      - "none": no wrapping
    """
    if boundary == "none":
        return pattern
    if boundary in {"word", "edge"}:
        return rf"\b(?:{pattern})\b"
    _warn(f"Unknown boundary '{boundary}', defaulting to 'word'")
    return rf"\b(?:{pattern})\b"


@dataclass
class CompiledGroup:
    subgroup: str
    terms: List[str] = field(default_factory=list)
    patterns: List[re.Pattern] = field(default_factory=list)


@dataclass
class CompiledNamespace:
    namespace: str
    groups: Dict[str, CompiledGroup] = field(default_factory=dict)


@dataclass
class ProtectedLexicon:
    """Structured and (optionally) compiled lexicon."""
    raw: Dict[str, Dict[str, List[str]]]
    compiled: Dict[str, CompiledNamespace] = field(default_factory=dict)

    # ---------- factory & validators ----------

    @classmethod
    def from_json(cls, path: Path) -> "ProtectedLexicon":
        if not path.exists():
            raise FileNotFoundError(f"Lexicon JSON not found: {path}")
        with path.open("r", encoding="utf-8") as f:
            raw_any = json.load(f)
        if not isinstance(raw_any, dict):
            raise ValueError("Lexicon JSON must be an object mapping namespaces to subgroup lists.")

        parsed: Dict[str, Dict[str, List[str]]] = {}
        for ns, groups in raw_any.items():
            if _is_meta_key(ns):
                # skip metadata blocks like "_source_notes"
                continue
            if not isinstance(groups, dict):
                _warn(f"Namespace '{ns}' should be an object; skipping.")
                continue
            bucket: Dict[str, List[str]] = {}
            for sg, terms in groups.items():
                # allow string -> [string]; skip non-list/dict
                if isinstance(terms, str):
                    bucket[sg] = [terms]
                elif isinstance(terms, list):
                    # ensure they are strings
                    bad = [t for t in terms if not isinstance(t, str)]
                    if bad:
                        _warn(f"Namespace '{ns}.{sg}' contains non-string terms; filtering them out.")
                    bucket[sg] = [str(t) for t in terms if isinstance(t, str)]
                else:
                    _warn(f"Subgroup '{ns}.{sg}' is not a list/string; skipping.")
                    continue

                # normalise terms (strip/unique, keep order)
                seen = set()
                normed: List[str] = []
                for t in bucket[sg]:
                    tt = t.strip()
                    if not tt or tt.lower() in seen:
                        continue
                    seen.add(tt.lower())
                    normed.append(tt)
                bucket[sg] = normed
            if bucket:
                parsed[ns] = bucket

        return cls(raw=parsed)

    # ---------- compilation ----------

    def compile(self, boundary: str = "word") -> "ProtectedLexicon":
        """
        Compile all terms into regex patterns according to boundary strategy.
        boundary: "word" (default), "edge", or "none".
        """
        compiled: Dict[str, CompiledNamespace] = {}
        for ns, groups in self.raw.items():
            cns = CompiledNamespace(namespace=ns, groups={})
            for sg, terms in groups.items():
                pats: List[re.Pattern] = []
                for t in terms:
                    frag = _term_to_regex(t)
                    patt = _wrap_boundary(frag, boundary=boundary)
                    try:
                        pats.append(re.compile(patt, REGEX_FLAGS))
                    except re.error as e:
                        _warn(f"Regex compile error in {ns}.{sg} for term '{t}': {e}. Skipping term.")
                cns.groups[sg] = CompiledGroup(subgroup=sg, terms=terms, patterns=pats)
            compiled[ns] = cns
        self.compiled = compiled
        return self

    # ---------- utilities ----------

    def audit_summary(self, sample_n: int = 3) -> Dict[str, Any]:
        """
        Produce a JSON-serialisable audit summary.
        """
        out: Dict[str, Any] = {"namespaces": {}, "totals": {"namespaces": 0, "subgroups": 0, "terms": 0}}
        n_ns = n_sg = n_terms = 0
        for ns, cns in self.compiled.items():
            ns_terms = 0
            groups_summary = {}
            for sg, cg in cns.groups.items():
                ns_terms += len(cg.terms)
                groups_summary[sg] = {
                    "terms_count": len(cg.terms),
                    "sample_terms": cg.terms[:sample_n],
                    "compiled_patterns": [p.pattern for p in cg.patterns[:sample_n]],
                }
            out["namespaces"][ns] = {
                "subgroups": groups_summary,
                "subgroup_count": len(cns.groups),
                "terms_count": ns_terms,
            }
            n_ns += 1
            n_sg += len(cns.groups)
            n_terms += ns_terms
        out["totals"]["namespaces"] = n_ns
        out["totals"]["subgroups"] = n_sg
        out["totals"]["terms"] = n_terms
        return out


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def _cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Protected lexicon loader & auditor.")
    parser.add_argument("--lexicon", type=str, default=None, help="Path to protected_terms.json")
    parser.add_argument("--boundary", type=str, default="word", choices=["word", "edge", "none"],
                        help="Regex boundary strategy.")
    parser.add_argument("--audit", action="store_true", help="Print summary and write audit JSON.")
    args = parser.parse_args(argv)

    cfg = load_project_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    dev = pick_device()
    print_run_header(cfg, dev, note="lexicon loader")

    default_path = cfg.paths.root / DEFAULT_LEXICON_REL
    path = Path(args.lexicon) if args.lexicon else default_path
    if not path.exists():
        raise FileNotFoundError(f"Lexicon file not found at {path}. Place it at config/protected_terms.json or pass --lexicon.")

    # Load & compile
    lex = ProtectedLexicon.from_json(path).compile(boundary=args.boundary)

    if args.audit:
        audit = lex.audit_summary(sample_n=5)
        metrics_dir = cfg.paths.metrics
        metrics_dir.mkdir(parents=True, exist_ok=True)
        out_json = metrics_dir / "v0_lexicon_audit.json"
        with out_json.open("w", encoding="utf-8") as f:
            json.dump(audit, f, indent=2, ensure_ascii=False)
        print(f"[ok] Wrote lexicon audit → {out_json}")
        # brief console summary
        t = audit["totals"]
        print(f"[ok] Namespaces={t['namespaces']}  Subgroups={t['subgroups']}  Terms={t['terms']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
