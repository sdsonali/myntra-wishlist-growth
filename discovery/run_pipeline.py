"""
Run the full discovery pipeline in one go:

  scrape → curate gold (rolling merge) → tag → aggregate

From project root:
  python discovery/run_pipeline.py

Skip steps when reusing existing outputs:
  python discovery/run_pipeline.py --skip-scrape
  python discovery/run_pipeline.py --skip-scrape --skip-curate
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

STEPS = (
    ("scrape", "discovery/scraper.py"),
    ("curate", "discovery/curate_gold.py"),
    ("tag", "discovery/tagger.py"),
    ("aggregate", "discovery/aggregate.py"),
)

LogFn = Callable[[str], None]


def _default_log(msg: str) -> None:
    print(msg, flush=True)


def _run_step(name: str, script: str, on_log: LogFn) -> bool:
    path = _ROOT / script
    on_log(f"=== {name}: {script} ===")
    proc = subprocess.Popen(
        [sys.executable, str(path)],
        cwd=_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if proc.stdout:
        for line in proc.stdout:
            on_log(line.rstrip())
    proc.wait()
    if proc.returncode != 0:
        on_log(f"Step {name} failed (exit {proc.returncode})")
        return False
    return True


def run_pipeline(
    *,
    skip_scrape: bool = False,
    skip_curate: bool = False,
    skip_tag: bool = False,
    skip_aggregate: bool = False,
    on_log: LogFn | None = None,
) -> bool:
    """Run pipeline steps. Returns True on success."""
    log = on_log or _default_log
    skip = {
        "scrape": skip_scrape,
        "curate": skip_curate,
        "tag": skip_tag,
        "aggregate": skip_aggregate,
    }

    log("Discovery pipeline")
    for name, script in STEPS:
        if skip.get(name):
            log(f"  skip {name}")
            continue
        if not _run_step(name, script, log):
            return False

    log("=== Pipeline complete ===")
    log("Outputs: gold_tagged_reviews.json, opportunity_table.json")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the discovery pipeline end-to-end.")
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Reuse discovery/data/reviews.csv",
    )
    parser.add_argument(
        "--skip-curate",
        action="store_true",
        help="Reuse discovery/data/gold_reviews.csv",
    )
    parser.add_argument(
        "--skip-tag",
        action="store_true",
        help="Reuse discovery/data/gold_tagged_reviews.json",
    )
    parser.add_argument(
        "--skip-aggregate",
        action="store_true",
        help="Skip opportunity table rebuild",
    )
    args = parser.parse_args()

    ok = run_pipeline(
        skip_scrape=args.skip_scrape,
        skip_curate=args.skip_curate,
        skip_tag=args.skip_tag,
        skip_aggregate=args.skip_aggregate,
    )
    if ok:
        _default_log("Run: streamlit run app.py")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
