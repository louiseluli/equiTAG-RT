"""
src/utils/config_loader.py

Purpose
-------
Centralised configuration, paths resolution, and reproducibility controls.
- Loads YAML config (project name, paths, seed).
- Resolves project-relative paths robustly (works from any CWD).
- Enforces seed policy (75 by default) and prints a standard run header.
- Picks a safe torch device (MPS > CUDA > CPU) and applies recommended settings:
  * torch.set_float32_matmul_precision('medium')
  * Avoid fp16 on MPS; no pin_memory on MPS
  * Deterministic/cuDNN flags when available

This module is imported by scripts (e.g., setup tasks, EDA, modeling) to keep
replicability and logging consistent across the project.

Inputs
------
- config/config.yaml (required): contains project_name, random_seed, and paths.*

Outputs
-------
- None directly; provides functions/classes used elsewhere.

Assumptions
-----------
- YAML config exists at <project_root>/config/config.yaml.
- Torch may or may not be installed; functions degrade gracefully.

Failure Modes
-------------
- Missing YAML -> raises FileNotFoundError.
- Malformed YAML -> raises yaml.YAMLError.

Complexity
----------
- O(1); negligible overhead relative to modeling/EDA.

Test Notes
----------
- Run as a module to print an example header:
    python -m src.utils.config_loader --print
"""

from __future__ import annotations
import argparse
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import yaml  # type: ignore
except ImportError as e:
    print("Please install pyyaml: pip install pyyaml", file=sys.stderr)
    raise

# Optional deps
try:  # numpy is optional but recommended
    import numpy as np  # type: ignore
except Exception:
    np = None  # type: ignore

try:
    import torch  # type: ignore
except Exception:
    torch = None  # type: ignore


# --------------------------------------------------------------------------------------
# Project root & config path resolution
# --------------------------------------------------------------------------------------

# This file lives at: <root>/src/utils/config_loader.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_FILE = PROJECT_ROOT / "config" / "config.yaml"


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    data: Path
    reports: Path
    figures: Path
    metrics: Path
    database: Path
    config_dir: Path
    config_file: Path


@dataclass(frozen=True)
class ProjectConfig:
    project_name: str
    random_seed: int
    paths: ProjectPaths


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r") as f:
        return yaml.safe_load(f)


def load_config(config_path: Optional[Path] = None) -> ProjectConfig:
    """
    Load YAML config and return a typed ProjectConfig.

    Parameters
    ----------
    config_path : Optional[Path]
        Override path to YAML; defaults to <root>/config/config.yaml

    Returns
    -------
    ProjectConfig
    """
    cfg_path = config_path or DEFAULT_CONFIG_FILE
    raw = _read_yaml(cfg_path)

    # Mandatory fields with defaults
    project_name = str(raw.get("project_name", "equiTAG-RT"))
    seed = int(raw.get("random_seed", 75))
    paths_raw = raw.get("paths", {})
    # Resolve relative to project root
    def _p(key: str, default: str) -> Path:
        return (PROJECT_ROOT / Path(paths_raw.get(key, default))).resolve()

    data = _p("data_dir", "data")  # “data_dir” optional; we still read DB path below
    reports = _p("reports", "reports")
    figures = _p("figures", "reports/figures")
    metrics = _p("metrics", "reports/metrics")
    database = _p("database", "data/redtube_videos.db")
    config_dir = DEFAULT_CONFIG_FILE.parent

    paths = ProjectPaths(
        root=PROJECT_ROOT,
        data=data,
        reports=reports,
        figures=figures,
        metrics=metrics,
        database=database,
        config_dir=config_dir,
        config_file=cfg_path,
    )
    return ProjectConfig(project_name=project_name, random_seed=seed, paths=paths)


def ensure_directories(paths: ProjectPaths) -> None:
    """
    Create important directories if missing. Safe to call multiple times.
    """
    for p in (paths.data, paths.reports, paths.figures, paths.metrics):
        p.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------------------
# Reproducibility: seed & device setup
# --------------------------------------------------------------------------------------

def set_global_seed(seed: int = 75, deterministic: bool = True) -> None:
    """
    Set random seeds across Python, NumPy (if present), and Torch (if present).

    Notes
    -----
    - We avoid setting fp16 on MPS.
    - For Torch, we set deterministic/cuDNN flags when available.
    """
    # Guard against string env: ensure stable hashing
    os.environ["PYTHONHASHSEED"] = str(seed)

    random.seed(seed)
    if np is not None:
        try:
            np.random.seed(seed)  # type: ignore[attr-defined]
        except Exception:
            pass

    if torch is not None:
        try:
            torch.manual_seed(seed)  # type: ignore[attr-defined]
            if torch.cuda.is_available():  # type: ignore[attr-defined]
                torch.cuda.manual_seed_all(seed)  # type: ignore[attr-defined]
            if deterministic:
                # cuDNN determinism when available
                if hasattr(torch, "use_deterministic_algorithms"):
                    torch.use_deterministic_algorithms(True)  # type: ignore[attr-defined]
                if hasattr(torch.backends, "cudnn"):
                    torch.backends.cudnn.deterministic = True  # type: ignore[attr-defined]
                    torch.backends.cudnn.benchmark = False     # type: ignore[attr-defined]
            # Precision policy (safe default)
            if hasattr(torch, "set_float32_matmul_precision"):
                torch.set_float32_matmul_precision("medium")  # type: ignore[attr-defined]
        except Exception:
            pass  # If torch not properly configured, continue gracefully


def pick_device(prefer_mps: bool = True, prefer_cuda: bool = True) -> Tuple[str, str]:
    """
    Pick an appropriate compute device.

    Returns
    -------
    (device_repr, device_type) where device_type in {'mps','cuda','cpu','none'}

    Notes
    -----
    - We prefer MPS on Apple Silicon, then CUDA, else CPU.
    - Avoid fp16 on MPS; do not use pin_memory with MPS dataloaders.
    """
    if torch is None:
        return ("no-torch", "none")

    try:
        if prefer_mps and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():  # type: ignore
            return ("mps", "mps")
        if prefer_cuda and torch.cuda.is_available():  # type: ignore[attr-defined]
            idx = torch.cuda.current_device()  # type: ignore[attr-defined]
            name = torch.cuda.get_device_name(idx)  # type: ignore[attr-defined]
            return (f"cuda:{idx} ({name})", "cuda")
        return ("cpu", "cpu")
    except Exception:
        return ("cpu", "cpu")


def print_run_header(cfg: ProjectConfig,
                     device_info: Tuple[str, str],
                     note: str = "") -> None:
    """
    Standard header for every runnable script to ensure logs are consistent.
    """
    dev_str, dev_type = device_info
    print("=" * 78)
    print(f"{cfg.project_name} :: Reproducible run")
    print(f"- Root:    {cfg.paths.root}")
    print(f"- Config:  {cfg.paths.config_file}")
    print(f"- DB:      {cfg.paths.database}")
    print(f"- Reports: {cfg.paths.reports}")
    print(f"- Seed:    {cfg.random_seed}")
    print(f"- Device:  {dev_str} [{dev_type}]")
    if note:
        print(f"- Note:    {note}")
    print("=" * 78)


# --------------------------------------------------------------------------------------
# CLI (optional) for quick smoke test
# --------------------------------------------------------------------------------------

def _cli(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Config loader smoke test.")
    parser.add_argument("--print", action="store_true", help="Print resolved config and run header.")
    args = parser.parse_args(argv)

    cfg = load_config()
    ensure_directories(cfg.paths)
    set_global_seed(cfg.random_seed, deterministic=True)
    device_info = pick_device()
    if args.print:
        print_run_header(cfg, device_info, note="config_loader smoke test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
