"""
Step 3 - Tag reviews with a free LLM.

Reads:  discovery/data/gold_reviews.csv (preferred)
        discovery/data/reviews.csv (fallback)
Writes: discovery/data/gold_tagged_reviews.json (preferred)
        discovery/data/tagged_reviews.json (fallback)

Run from project root:
  python discovery/tagger.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd

from shared import config
from shared.llm_client import call_llm, extract_json, model_name

SYSTEM_PROMPT = (
    "You are analyzing user feedback about online fashion shopping (Myntra). "
    "Return ONLY valid JSON. No markdown fences, no preamble."
)

USER_PROMPT_TEMPLATE = """You are analyzing user feedback about online fashion shopping (Myntra).
For each review below, extract four fields.

REASON vs BLOCKER (hard rule):
- reason_for_wishlisting = why they SAVED the item (intent to keep it for later).
- purchase_blocker = why they have NOT BOUGHT yet.
- Never copy a blocker label into reason. Never copy reason into blocker.
- Do NOT use price_change or quality_doubt as a reason.
- Use price_wait ONLY if they saved in order to wait for a sale / price drop.
  Cheap-looking fabric is quality_doubt (blocker), not price_wait.

reason_for_wishlisting — use one of:
  liked_look, occasion_save, compare_later, need_uncertainty,
  style_confirmation, price_wait, budget_wait, just_browsing
  (null if they did not describe why they saved)

purchase_blocker — use one of:
  fit_uncertainty, price_change, found_alternative, forgot,
  quality_doubt, occasion_mismatch, no_urgency
  (null if not mentioned)

comparison_behavior: true/false/null — do they compare items or apps before deciding?

info_sought_outside_app — use one of:
  instagram, youtube, google, friend_family, other_apps, physical_store, influencer
  (null if they did not mention leaving the app)
  Mentions of reel, haul video, asked sister, Ajio, Amazon, or a physical store count.
  Do NOT label a row as youtube just because the comment was posted on YouTube.

Return ONLY a JSON array. One object per review with keys:
id, reason_for_wishlisting, purchase_blocker, comparison_behavior, info_sought_outside_app
Use null when not mentioned. Keep labels short snake_case from the lists above.

Reviews:
{reviews_block}
"""


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def parse_tagged_payload(data) -> tuple[int | None, list[dict]]:
    """Unwrap {tag_schema_version, reviews} or a legacy bare list."""
    if isinstance(data, dict):
        version = data.get("tag_schema_version")
        try:
            version = int(version) if version is not None else None
        except (TypeError, ValueError):
            version = None
        rows = data.get("reviews") or data.get("rows") or []
        return version, list(rows) if isinstance(rows, list) else []
    if isinstance(data, list):
        return None, data
    return None, []


def parse_tagged_file(path: Path) -> tuple[int | None, list[dict]]:
    return parse_tagged_payload(json.loads(path.read_text(encoding="utf-8")))


def _normalize_tags(parsed, batch_ids: list[int]) -> list[dict]:
    if isinstance(parsed, dict):
        for key in ("reviews", "results", "items", "data"):
            if isinstance(parsed.get(key), list):
                parsed = parsed[key]
                break
        else:
            parsed = [parsed]

    by_id = {}
    for i, item in enumerate(parsed):
        if not isinstance(item, dict):
            continue
        rid = item.get("id", batch_ids[i] if i < len(batch_ids) else None)
        try:
            rid = int(rid)
        except (TypeError, ValueError):
            rid = batch_ids[i] if i < len(batch_ids) else i
        by_id[rid] = {
            "reason_for_wishlisting": item.get("reason_for_wishlisting"),
            "purchase_blocker": item.get("purchase_blocker"),
            "comparison_behavior": item.get("comparison_behavior"),
            "info_sought_outside_app": item.get("info_sought_outside_app"),
        }

    out = []
    for rid in batch_ids:
        tags = by_id.get(
            rid,
            {
                "reason_for_wishlisting": None,
                "purchase_blocker": None,
                "comparison_behavior": None,
                "info_sought_outside_app": None,
            },
        )
        out.append({"id": rid, **tags})
    return out


# ---------------------------------------------------------------------------
# Label canon + heuristic fill
# ---------------------------------------------------------------------------

def _nonempty(value) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    return text not in ("", "null", "none", "nan")


def _snake(value) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _canon_reason(value) -> str | None:
    if not _nonempty(value):
        return None
    raw = _snake(value)
    if raw in config.BLOCKER_LABELS and raw not in config.REASON_LABELS:
        return None
    mapped = config.REASON_ALIASES.get(raw, raw)
    return mapped if mapped in config.REASON_LABELS else None


def _canon_external(value) -> str | None:
    if not _nonempty(value):
        return None
    raw = _snake(value)
    mapped = config.EXTERNAL_ALIASES.get(raw, raw)
    return mapped if mapped in config.EXTERNAL_LABELS else None


def _canon_blocker(value) -> str | None:
    if not _nonempty(value):
        return None
    raw = _snake(value)
    aliases = {
        "fit": "fit_uncertainty",
        "sizing": "fit_uncertainty",
        "quality": "quality_doubt",
        "fabric": "quality_doubt",
        "price": "price_change",
        "expensive": "price_change",
        "alternative": "found_alternative",
        "occasion": "occasion_mismatch",
        "no urgency": "no_urgency",
    }
    mapped = aliases.get(raw, raw)
    return mapped if mapped in config.BLOCKER_LABELS else None


_REASON_RULES: list[tuple[str, list[str]]] = [
    (
        "price_wait",
        [
            "wait for sale",
            "waiting for sale",
            "until sale",
            "price drop",
            "when it goes on sale",
            "wait for discount",
            "waiting for a better price",
            "wait for the price",
            "waiting for the price",
        ],
    ),
    (
        "budget_wait",
        [
            "salary",
            "payday",
            "saving up",
            "savings to grow",
            "over my budget",
            "can't afford",
            "cannot afford",
            "too costly for me",
        ],
    ),
    (
        "occasion_save",
        [
            "wedding",
            "sangeet",
            "rakhi",
            "raksha",
            "occasion",
            "party wear",
            "festive",
            "function",
            "diwali",
        ],
    ),
    (
        "compare_later",
        [
            "compare",
            "comparing",
            " vs ",
            "alternative",
            "other options",
            "ajio",
            "flipkart",
            "meesho",
        ],
    ),
    (
        "need_uncertainty",
        [
            "not sure i need",
            "don't need",
            "do i need",
            "wasn't sure if i needed",
            "wasnt sure if i needed",
            "not sure if i need",
        ],
    ),
    (
        "style_confirmation",
        ["suit me", "my style", "will it look", "styling", "suits the occasion"],
    ),
    (
        "liked_look",
        [
            "liked how",
            "looks good",
            "looks nice",
            "looked nice",
            "pretty",
            "beautiful",
            "cute",
            "loved the look",
        ],
    ),
    ("just_browsing", ["just browsing", "window shop", "maybe later", "for later"]),
]

_EXTERNAL_RULES: list[tuple[str, list[str]]] = [
    ("instagram", ["instagram", " insta ", "reel"]),
    ("youtube", ["youtube", "watched your", "your video", "review video"]),
    ("google", ["google", "googled", "searched online"]),
    (
        "friend_family",
        [
            "asked friend",
            "asked sister",
            "my mom",
            "my sister",
            "family told",
            "friend told",
            "asked my",
        ],
    ),
    (
        "physical_store",
        ["physical store", "in store", "in-store", "local store", "tried in shop", "offline"],
    ),
    ("influencer", ["influencer", "blogger"]),
    ("other_apps", ["ajio", "amazon", "flipkart", "meesho", "nykaa"]),
]


def _heuristic_reason(low: str) -> str | None:
    for label, phrases in _REASON_RULES:
        if any(p in low for p in phrases):
            return label
    return None


def _heuristic_external(low: str) -> str | None:
    for label, phrases in _EXTERNAL_RULES:
        if any(p in low for p in phrases):
            return label
    return None


def heuristic_fill(text: str, tags: dict) -> dict:
    """Fill null reason/external from keyword families; never copy blockers into reason."""
    low = (text or "").lower()
    out = dict(tags)

    out["reason_for_wishlisting"] = _canon_reason(out.get("reason_for_wishlisting"))
    if out["reason_for_wishlisting"] is None:
        out["reason_for_wishlisting"] = _heuristic_reason(low)

    out["info_sought_outside_app"] = _canon_external(out.get("info_sought_outside_app"))
    if out["info_sought_outside_app"] is None:
        out["info_sought_outside_app"] = _heuristic_external(low)

    blocker_raw = out.get("purchase_blocker")
    out["purchase_blocker"] = _canon_blocker(blocker_raw)
    if out["purchase_blocker"] is None and _nonempty(blocker_raw):
        raw = _snake(blocker_raw)
        if raw not in config.REASON_LABELS:
            out["purchase_blocker"] = raw

    cmp = out.get("comparison_behavior")
    if cmp in (True, "true", "True", 1, "1", "yes", "Yes"):
        out["comparison_behavior"] = True
    elif cmp in (False, "false", "False", 0, "0", "no", "No"):
        out["comparison_behavior"] = False
    else:
        out["comparison_behavior"] = None
        if any(w in low for w in ("compare", "ajio", "flipkart", "meesho", " vs ")):
            out["comparison_behavior"] = True

    return out


def _normalize_text(text: str) -> str:
    return " ".join(str(text or "").lower().split())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _json_safe(value):
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass
    return value


def _save(path: Path, tagged: list[dict]) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "tag_schema_version": config.TAG_SCHEMA_VERSION,
        "reviews": _json_safe(tagged),
    }
    tmp = path.with_suffix(".tmp.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def _log(msg: str) -> None:
    print(msg, flush=True)


def _row_record(row: dict, tag: dict) -> dict:
    filled = heuristic_fill(str(row.get("text") or ""), tag)
    if filled["purchase_blocker"] is None:
        sig = str(row.get("primary_signal") or "").strip()
        signal_to_blocker = {
            "fit_uncertainty": "fit_uncertainty",
            "quality_doubt": "quality_doubt",
            "price_hesitation": "price_change",
            "comparison_behavior": "found_alternative",
            "occasion_styling_mismatch": "occasion_mismatch",
            "wishlist_delay": "no_urgency",
        }
        filled["purchase_blocker"] = signal_to_blocker.get(sig)
    if filled["reason_for_wishlisting"] is None:
        sig = str(row.get("primary_signal") or "").strip()
        signal_to_reason = {
            "liked_look": "liked_look",
            "occasion_styling_mismatch": "occasion_save",
            "comparison_behavior": "compare_later",
            "price_hesitation": "price_wait",
            "wishlist_delay": "just_browsing",
        }
        # price_hesitation → price_wait only when sale-wait language is present
        if sig == "price_hesitation":
            low = str(row.get("text") or "").lower()
            if any(
                p in low
                for p in (
                    "wait for sale",
                    "waiting for sale",
                    "price drop",
                    "until sale",
                    "wait for discount",
                )
            ):
                filled["reason_for_wishlisting"] = "price_wait"
        elif sig in signal_to_reason:
            filled["reason_for_wishlisting"] = signal_to_reason[sig]
    return {
        "id": int(row["id"]),
        "source": row.get("source", ""),
        "date": "" if pd.isna(row.get("date")) else str(row.get("date")),
        "text": row.get("text", ""),
        "keep_for_gold": row.get("keep_for_gold"),
        "relevance_score": row.get("relevance_score"),
        "primary_signal": row.get("primary_signal"),
        "rationale": row.get("rationale") or row.get("curation_rationale"),
        "noise_category": row.get("noise_category"),
        "reason_for_wishlisting": filled["reason_for_wishlisting"],
        "purchase_blocker": filled["purchase_blocker"],
        "comparison_behavior": filled["comparison_behavior"],
        "info_sought_outside_app": filled["info_sought_outside_app"],
    }


def _empty_tags(rid: int) -> dict:
    return {
        "id": rid,
        "reason_for_wishlisting": None,
        "purchase_blocker": None,
        "comparison_behavior": None,
        "info_sought_outside_app": None,
    }


def tag_reviews(resume: bool = True) -> Path:
    csv_path = config.preferred_review_csv()
    if not csv_path.exists():
        _log(f"Missing {csv_path}. Run scraper.py first.")
        sys.exit(1)

    provider = config.LLM["provider"]
    model = model_name()
    batch_size = config.LLM["batch_size"]
    out = (
        config.GOLD_TAGGED_JSON
        if csv_path == config.GOLD_CSV
        else config.TAGGED_JSON
    )

    _log(f"Provider: {provider}")
    _log(f"Model:    {model}")
    _log(f"Batch:    {batch_size}")
    _log(f"Tag schema version: {config.TAG_SCHEMA_VERSION}")

    df = pd.read_csv(csv_path)
    df = df.reset_index(drop=True)
    if "id" in df.columns:
        df = df.drop(columns=["id"])
    df.insert(0, "id", df.index + 1)

    tagged: list[dict] = []
    done_texts: set[str] = set()
    if resume and out.exists():
        try:
            file_version, existing_rows = parse_tagged_file(out)
            if file_version == config.TAG_SCHEMA_VERSION and existing_rows:
                by_text: dict[str, dict] = {}
                for item in existing_rows:
                    key = _normalize_text(item.get("text"))
                    if key:
                        by_text[key] = item
                for row in df.to_dict("records"):
                    key = _normalize_text(row.get("text"))
                    if key and key in by_text:
                        old = by_text[key]
                        tagged.append(
                            _row_record(
                                row,
                                {
                                    "reason_for_wishlisting": old.get("reason_for_wishlisting"),
                                    "purchase_blocker": old.get("purchase_blocker"),
                                    "comparison_behavior": old.get("comparison_behavior"),
                                    "info_sought_outside_app": old.get(
                                        "info_sought_outside_app"
                                    ),
                                },
                            )
                        )
                        done_texts.add(key)
                _log(
                    f"Resuming by normalized text: {len(done_texts)} already tagged "
                    f"(schema v{file_version})"
                )
            else:
                _log(
                    f"Tagged file schema {file_version!r} != {config.TAG_SCHEMA_VERSION}; "
                    "retagging all gold rows once"
                )
        except Exception as exc:
            _log(f"Could not resume tagged file ({exc}); tagging from scratch")
            tagged = []
            done_texts = set()

    pending = df[~df["text"].map(_normalize_text).isin(done_texts)].copy()
    total = len(df)
    todo = len(pending)
    _log(f"Total reviews: {total} | remaining: {todo}")

    if todo == 0:
        tagged.sort(key=lambda x: x["id"])
        _save(out, tagged)
        _log(f"Nothing left to tag. File: {out}")
        return out

    n_batches = (todo + batch_size - 1) // batch_size
    rows = pending.to_dict("records")
    heuristic_only = False

    for b in range(n_batches):
        start = b * batch_size
        end = min(start + batch_size, todo)
        batch = rows[start:end]
        batch_ids = [int(r["id"]) for r in batch]

        lines = []
        for row in batch:
            text = str(row["text"]).replace("\n", " ").strip()
            if len(text) > 500:
                text = text[:500] + "..."
            lines.append(f"[{row['id']}] {text}")
        reviews_block = "\n".join(lines)

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(reviews_block=reviews_block),
            },
        ]

        _log(f"[batch {b + 1}/{n_batches}] tagging ids {batch_ids[0]}-{batch_ids[-1]}...")
        tags = None
        if not heuristic_only:
            try:
                raw = call_llm(messages)
                parsed = extract_json(raw)
                tags = _normalize_tags(parsed, batch_ids)
            except Exception as exc:
                err = str(exc)
                _log(f"  LLM tagging failed ({exc}) — heuristic fill for this batch")
                if "402" in err or "depleted" in err.lower() or "credits" in err.lower():
                    _log("  switching remaining batches to heuristic-only tagging")
                    heuristic_only = True
        if tags is None:
            tags = [_empty_tags(rid) for rid in batch_ids]

        for row, tag in zip(batch, tags):
            tagged.append(_row_record(row, tag))

        tagged.sort(key=lambda x: x["id"])
        _save(out, tagged)
        _log(f"  saved {len(tagged)}/{total}")
        if not heuristic_only:
            time.sleep(1)

    blockers = [t["purchase_blocker"] for t in tagged if t.get("purchase_blocker")]
    reasons = [t["reason_for_wishlisting"] for t in tagged if t.get("reason_for_wishlisting")]
    externals = [
        t["info_sought_outside_app"] for t in tagged if t.get("info_sought_outside_app")
    ]
    _log("\n=== Done ===")
    _log(f"Tagged: {len(tagged)}")
    _log(f"With purchase_blocker: {len(blockers)}")
    _log(f"With wishlisting reason: {len(reasons)}")
    _log(f"With outside-app info: {len(externals)}")
    _log(f"Saved to: {out}")
    return out


if __name__ == "__main__":
    tag_reviews(resume=True)
