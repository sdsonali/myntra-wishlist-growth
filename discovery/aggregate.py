"""
Step 4 - Aggregate tagged reviews into an opportunity table.

Reads:  discovery/data/gold_tagged_reviews.json (preferred)
        discovery/data/tagged_reviews.json (fallback)
Writes: discovery/data/opportunity_table.json
        discovery/data/opportunity_table.csv

Run from project root:
  python discovery/aggregate.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd

from shared import config
from discovery.tagger import parse_tagged_payload


def _is_true(value) -> bool:
    return value in (True, "true", "True", 1, "yes", "Yes")


def _nonempty(value) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and pd.isna(value):
        return False
    text = str(value).strip().lower()
    return text not in ("", "null", "none", "nan")


def _top_n(counter: Counter, n: int = 5) -> list[dict]:
    total = sum(counter.values()) or 1
    rows = []
    for label, count in counter.most_common(n):
        rows.append(
            {
                "label": label,
                "count": count,
                "pct_of_mentions": round(100.0 * count / total, 1),
            }
        )
    return rows


def _headline(blockers: list[dict]) -> str:
    if not blockers:
        return "Not enough purchase-blocker mentions to rank opportunities yet."
    top = blockers[0]
    if len(blockers) >= 3:
        return (
            f"{top['label'].replace('_', ' ').title()} appears in "
            f"{top['pct_of_mentions']}% of purchase-blocker mentions, more than "
            f"{blockers[1]['label'].replace('_', ' ')} ({blockers[1]['pct_of_mentions']}%) "
            f"or {blockers[2]['label'].replace('_', ' ')} ({blockers[2]['pct_of_mentions']}%) "
            f"- making it the single largest addressable blocker in this corpus."
        )
    if len(blockers) == 2:
        return (
            f"{top['label'].replace('_', ' ').title()} appears in "
            f"{top['pct_of_mentions']}% of purchase-blocker mentions, ahead of "
            f"{blockers[1]['label'].replace('_', ' ')} ({blockers[1]['pct_of_mentions']}%)."
        )
    return (
        f"{top['label'].replace('_', ' ').title()} is the top purchase blocker "
        f"({top['pct_of_mentions']}% of blocker mentions)."
    )


def _survey_overlay(corpus_pct: float) -> dict:
    """Second evidence layer from the survey CSV — not mixed into corpus %."""
    cfg = config.SURVEY_OVERLAY
    path = Path(cfg["csv_path"])
    n = int(cfg["fallback_n"])
    pct = float(cfg["fallback_pct_external"])

    if path.exists():
        try:
            df = pd.read_csv(path)
            col = cfg["external_column"]
            if col in df.columns:
                series = df[col].fillna("").astype(str)
                n = len(series)
                none_vals = {str(v).strip().lower() for v in cfg["none_values"]}
                did_external = 0
                for val in series:
                    low = val.strip().lower()
                    if low and low not in none_vals:
                        did_external += 1
                pct = round(100.0 * did_external / n, 1) if n else 0.0
        except Exception as exc:
            print(f"Survey overlay fallback ({exc})")

    if pct >= 80:
        survey_bit = f"survey respondents (n={n}) almost all did."
    else:
        survey_bit = f"survey respondents (n={n}) {pct:.0f}% did."
    caption = (
        f"Public reviews mention leaving the app in {corpus_pct}%; {survey_bit} "
        "These are two evidence layers, not one combined rate."
    )
    return {
        "n": n,
        "pct_external_research": pct,
        "corpus_pct_external_research": corpus_pct,
        "caption": caption,
    }


def aggregate(tagged_path: Path | None = None) -> dict:
    path = tagged_path or config.preferred_tagged_json()
    if not path.exists():
        print(f"Missing {path}. Run tagger.py first.")
        sys.exit(1)

    version, rows = parse_tagged_payload(json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(rows, list) or not rows:
        print("tagged_reviews.json is empty.")
        sys.exit(1)

    n = len(rows)
    reason_c = Counter()
    blocker_c = Counter()
    external_c = Counter()
    compare_n = 0
    external_n = 0

    for row in rows:
        reason = row.get("reason_for_wishlisting")
        blocker = row.get("purchase_blocker")
        external = row.get("info_sought_outside_app")
        if _nonempty(reason):
            reason_c[str(reason).strip()] += 1
        if _nonempty(blocker):
            blocker_c[str(blocker).strip()] += 1
        if _is_true(row.get("comparison_behavior")):
            compare_n += 1
        if _nonempty(external):
            external_n += 1
            external_c[str(external).strip()] += 1

    top_reasons = _top_n(reason_c, 5)
    top_blockers = _top_n(blocker_c, 5)
    top_external = _top_n(external_c, 5)
    corpus_pct_external = round(100.0 * external_n / n, 1) if n else 0.0

    result = {
        "total_reviews": n,
        "source_corpus": "gold" if path == config.GOLD_TAGGED_JSON else "raw",
        "tag_schema_version": version,
        "top_reasons_for_wishlisting": top_reasons,
        "top_purchase_blockers": top_blockers,
        "top_info_sought_outside_app": top_external,
        "pct_comparison_behavior": round(100.0 * compare_n / n, 1),
        "pct_external_research": corpus_pct_external,
        "counts": {
            "reason_mentions": sum(reason_c.values()),
            "blocker_mentions": sum(blocker_c.values()),
            "comparison_true": compare_n,
            "external_research": external_n,
        },
        "headline": _headline(top_blockers),
        "survey_overlay": _survey_overlay(corpus_pct_external),
        "by_source": {},
    }

    # light per-source null / signal snapshot (useful for scrape priority)
    by_source: dict[str, list] = {}
    for row in rows:
        by_source.setdefault(row.get("source", "unknown"), []).append(row)

    for source, items in by_source.items():
        sn = len(items)
        fully_null = 0
        for r in items:
            if (
                not _nonempty(r.get("reason_for_wishlisting"))
                and not _nonempty(r.get("purchase_blocker"))
                and not _is_true(r.get("comparison_behavior"))
                and not _nonempty(r.get("info_sought_outside_app"))
            ):
                fully_null += 1
        result["by_source"][source] = {
            "total": sn,
            "fully_null": fully_null,
            "fully_null_pct": round(100.0 * fully_null / sn, 1) if sn else 0.0,
        }

    return result


def save_opportunity(result: dict) -> tuple[Path, Path]:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path = config.OPPORTUNITY_JSON
    csv_path = config.OPPORTUNITY_CSV

    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    chart_rows = []
    for item in result["top_purchase_blockers"]:
        chart_rows.append(
            {
                "category": "purchase_blocker",
                "label": item["label"],
                "count": item["count"],
                "pct_of_mentions": item["pct_of_mentions"],
            }
        )
    for item in result["top_reasons_for_wishlisting"]:
        chart_rows.append(
            {
                "category": "reason_for_wishlisting",
                "label": item["label"],
                "count": item["count"],
                "pct_of_mentions": item["pct_of_mentions"],
            }
        )
    for item in result.get("top_info_sought_outside_app") or []:
        chart_rows.append(
            {
                "category": "info_sought_outside_app",
                "label": item["label"],
                "count": item["count"],
                "pct_of_mentions": item["pct_of_mentions"],
            }
        )
    pd.DataFrame(chart_rows).to_csv(csv_path, index=False, encoding="utf-8")
    return json_path, csv_path


def main() -> None:
    result = aggregate()
    json_path, csv_path = save_opportunity(result)

    print("=== Opportunity table ===")
    print(f"Total reviews: {result['total_reviews']}")
    print(f"Comparison behavior: {result['pct_comparison_behavior']}%")
    print(f"External research (corpus): {result['pct_external_research']}%")
    overlay = result.get("survey_overlay") or {}
    if overlay.get("caption"):
        print(f"Survey overlay: {overlay['caption']}")
    print("\nTop purchase blockers (% of blocker mentions):")
    for row in result["top_purchase_blockers"]:
        print(f"  {row['label']}: {row['count']} ({row['pct_of_mentions']}%)")
    print("\nTop wishlisting reasons (% of reason mentions):")
    for row in result["top_reasons_for_wishlisting"]:
        print(f"  {row['label']}: {row['count']} ({row['pct_of_mentions']}%)")
    print(f"\nHeadline:\n  {result['headline']}")
    print(f"\nSaved: {json_path}")
    print(f"Saved: {csv_path}")


if __name__ == "__main__":
    main()
