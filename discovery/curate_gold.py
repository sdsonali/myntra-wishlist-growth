"""
Step 2 - Curate a gold discovery corpus with an LLM.

Reads:  discovery/data/reviews.csv
Writes: discovery/data/gold_curation_progress.json
        discovery/data/gold_reviews.json
        discovery/data/gold_reviews.csv

Run from project root:
  python discovery/curate_gold.py
"""

from __future__ import annotations

import json
import re
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
    "You are curating a gold corpus of Myntra shopper feedback for wishlist-to-purchase "
    "discovery. Keep only reviews with real purchase-decision signal. Return ONLY valid JSON."
)

USER_PROMPT_TEMPLATE = """Decide which reviews belong in a gold corpus for understanding why shoppers
save items but do not confidently buy yet.

Prioritize reviews with real signal about:
- fit uncertainty
- quality doubt
- price hesitation
- comparison behavior or alternatives (Ajio, Amazon, Flipkart, Meesho, other options)
- occasion or styling mismatch (wedding, Rakhi, party, office, festive)
- liked how it looked / saving a look they liked
- wishlist hesitation, delayed purchase, no urgency, waiting to decide
- external research before buying (Instagram, YouTube, Google, friend/family, physical store)

Drop reviews that are mainly:
- generic app praise
- generic delivery, refund, service, or logistics complaints with no purchase-decision signal
- spam, abuse, nonsense, or off-topic chatter

Return ONLY a JSON array. One object per review with keys:
- id
- keep_for_gold (true/false)
- relevance_score (0-100 integer)
- primary_signal (short snake_case label)
- rationale (short sentence)
- noise_category (short snake_case label or null)

Use keep_for_gold=true only when the review clearly helps identify purchase blockers or hesitation.
When uncertain, be selective.

Reviews:
{reviews_block}
"""


# Signal / noise patterns for heuristic curation (used when LLM credits are exhausted)
_SIGNAL_RULES: list[tuple[str, list[str], int]] = [
    ("fit_uncertainty", ["fit", "size", "sizing", "tight", "loose", "size chart", "runs small", "runs large", "size up", "ordered m", "ordered l"], 18),
    ("quality_doubt", ["quality", "fabric", "material", "cheap look", "thread", "see through", "transparent", "color fade", "looks cheap"], 16),
    ("price_hesitation", ["price", "sale", "discount", "expensive", "costly", "too costly", "wait for sale", "price drop"], 14),
    ("comparison_behavior", ["compare", "vs", "ajio", "amazon", "flipkart", "meesho", "nykaa", "alternative", "better than", "other options", "wishlist"], 16),
    ("occasion_styling_mismatch", ["occasion", "wedding", "sangeet", "rakhi", "raksha", "party", "office", "function", "styling", "festive", "diwali", "event"], 16),
    ("liked_look", ["liked how", "looks good", "looks nice", "looked nice", "pretty", "beautiful", "cute", "loved the look", "loved this look"], 14),
    ("wishlist_delay", ["wishlist", "wish list", "later", "still deciding", "hesitat", "not sure", "thinking"], 16),
    ("external_research", ["youtube", "instagram", "google", "review video", "asked friend", "asked sister", "influencer", "reel", "haul", "physical store", "in store", "local store"], 14),
]

_NOISE_RULES: list[tuple[str, list[str]]] = [
    ("generic_app_praise", ["nice app", "good app", "best app", "love this app", "amazing app", "great app", "superb app"]),
    ("generic_service_issue", ["delivery boy", "courier", "customer care", "customer support", "otp", "login", "account blocked", "account deactivated", "refund not", "pickup failed"]),
    ("spam_or_noise", ["purchase link", "subscribe", "first comment", "nice video", "😍😍", "🔥🔥"]),
]


def _heuristic_decision(text: str) -> dict:
    """Local gold filter when LLM is unavailable — prefers purchase-decision signal."""
    low = (text or "").lower()
    signal_hits: list[tuple[str, int]] = []
    for label, words, weight in _SIGNAL_RULES:
        hits = sum(1 for w in words if w in low)
        if hits:
            signal_hits.append((label, hits * weight))

    noise_label = None
    for label, words in _NOISE_RULES:
        if any(w in low for w in words):
            noise_label = label
            break

    best_signal = None
    score = 0
    if signal_hits:
        best_signal, score = max(signal_hits, key=lambda x: x[1])
        score = min(100, 12 + score)  # base boost so single strong hit clears keep bar

    # Pure noise / praise with no real signal → drop
    if noise_label and score < 14:
        return {
            "keep_for_gold": False,
            "relevance_score": max(0, score // 2),
            "primary_signal": None,
            "rationale": f"heuristic_drop:{noise_label}",
            "noise_category": noise_label,
        }

    # Keep anything with a clear purchase-decision theme
    keep = best_signal is not None and score >= 14
    return {
        "keep_for_gold": keep,
        "relevance_score": score if keep else max(0, score // 2),
        "primary_signal": best_signal if keep else None,
        "rationale": "heuristic_keep" if keep else "heuristic_drop:weak_or_no_signal",
        "noise_category": None if keep else (noise_label or "unclear_signal"),
    }


def _normalize_decisions(parsed, batch_ids: list[int]) -> list[dict]:
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

        score = item.get("relevance_score", 0)
        try:
            score = max(0, min(100, int(score)))
        except (TypeError, ValueError):
            score = 0

        keep = item.get("keep_for_gold")
        keep = keep in (True, "true", "True", 1, "1", "yes", "Yes")

        by_id[rid] = {
            "keep_for_gold": keep,
            "relevance_score": score,
            "primary_signal": item.get("primary_signal"),
            "rationale": item.get("rationale"),
            "noise_category": item.get("noise_category"),
        }

    out = []
    for rid in batch_ids:
        out.append(
            {
                "id": rid,
                **by_id.get(
                    rid,
                    {
                        "keep_for_gold": False,
                        "relevance_score": 0,
                        "primary_signal": None,
                        "rationale": "missing_llm_output",
                        "noise_category": "unclear_signal",
                    },
                ),
            }
        )
    return out


def _save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    # Direct write is more reliable on Windows when the target is briefly locked
    for attempt in range(5):
        try:
            path.write_text(text, encoding="utf-8")
            return
        except PermissionError:
            time.sleep(0.4 * (attempt + 1))
    path.write_text(text, encoding="utf-8")


def _save_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    for attempt in range(5):
        try:
            df.to_csv(path, index=False, encoding="utf-8")
            return
        except PermissionError:
            time.sleep(0.4 * (attempt + 1))
    df.to_csv(path, index=False, encoding="utf-8")


def _normalize_text(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def _native(value):
    if value is None:
        return None
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


def _clean_gold_row(row: dict) -> dict:
    keep = row.get("keep_for_gold")
    return {
        "id": _native(row.get("id")),
        "source": str(row.get("source") or ""),
        "date": "" if _native(row.get("date")) is None else str(_native(row.get("date"))),
        "text": row.get("text") or "",
        "keep_for_gold": keep in (True, "true", "True", 1, "1", "yes", "Yes"),
        "relevance_score": int(_native(row.get("relevance_score")) or 0),
        "primary_signal": _native(row.get("primary_signal")),
        "rationale": _native(row.get("rationale")),
        "noise_category": _native(row.get("noise_category")),
    }


def snapshot_existing_gold() -> list[dict]:
    """Load current gold CSV as the rolling-corpus seed. Empty if none yet."""
    path = config.GOLD_CSV
    if not path.exists():
        return []
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        print(f"Could not snapshot existing gold ({exc}); starting from empty.", flush=True)
        return []
    if df.empty or "text" not in df.columns:
        return []
    return [_clean_gold_row(row) for row in df.to_dict("records")]


def _build_gold_rows(judged: list[dict]) -> list[dict]:
    kept = [row for row in judged if row.get("keep_for_gold")]
    kept.sort(
        key=lambda row: (
            int(row.get("relevance_score") or 0),
            len(str(row.get("text") or "")),
        ),
        reverse=True,
    )
    return kept[: config.GOLD_TARGET_TOTAL]


def merge_gold(existing: list[dict], this_run: list[dict]) -> list[dict]:
    """Dedupe by normalized text, cap at GOLD_MAX_TOTAL by dropping oldest.

    Clash: higher relevance_score wins; tie keeps the existing row.
    Missing dates leave first (treated as oldest).
    """
    by_text: dict[str, dict] = {}
    for row in existing:
        key = _normalize_text(row.get("text"))
        if not key:
            continue
        by_text[key] = _clean_gold_row(row)

    for row in this_run:
        key = _normalize_text(row.get("text"))
        if not key:
            continue
        cleaned = _clean_gold_row(row)
        if key in by_text:
            old_score = int(by_text[key].get("relevance_score") or 0)
            new_score = int(cleaned.get("relevance_score") or 0)
            if new_score > old_score:
                by_text[key] = cleaned
        else:
            by_text[key] = cleaned

    merged = list(by_text.values())
    max_total = int(getattr(config, "GOLD_MAX_TOTAL", 1000))
    if len(merged) > max_total:
        merged.sort(
            key=lambda row: (
                str(row.get("date") or "").strip() or "0000-00-00",
                int(row.get("relevance_score") or 0),
            )
        )
        drop_n = len(merged) - max_total
        merged = merged[drop_n:]

    merged.sort(
        key=lambda row: (
            int(row.get("relevance_score") or 0),
            str(row.get("date") or ""),
        ),
        reverse=True,
    )
    for i, row in enumerate(merged, 1):
        row["id"] = i
        row["keep_for_gold"] = True
    return merged


def _persist_outputs(judged: list[dict], existing_gold: list[dict]) -> tuple[int, int, int]:
    judged.sort(key=lambda row: row["id"])
    this_run = _build_gold_rows(judged)
    gold_rows = merge_gold(existing_gold, this_run)
    _save_json(config.GOLD_PROGRESS_JSON, judged)
    _save_json(config.GOLD_JSON, gold_rows)
    _save_csv(config.GOLD_CSV, gold_rows)
    return len(judged), len(this_run), len(gold_rows)


def curate_gold(resume: bool = True) -> Path:
    csv_path = config.OUTPUT_CSV
    if not csv_path.exists():
        print(f"Missing {csv_path}. Run scraper.py first.", flush=True)
        sys.exit(1)

    existing_gold = snapshot_existing_gold()
    print(
        f"Rolling gold seed: {len(existing_gold)} existing rows "
        f"(cap {getattr(config, 'GOLD_MAX_TOTAL', 1000)})",
        flush=True,
    )

    df = pd.read_csv(csv_path)
    df = df.reset_index(drop=True)
    df.insert(0, "id", df.index + 1)
    if "text" not in df.columns:
        print("Expected a 'text' column in reviews.csv", flush=True)
        sys.exit(1)

    min_chars = config.CURATION["min_text_chars"]
    df = df[df["text"].fillna("").astype(str).str.len() >= min_chars].copy()
    df = df.reset_index(drop=True)
    df["id"] = range(1, len(df) + 1)

    judged: list[dict] = []
    done_ids: set[int] = set()
    if resume and config.GOLD_PROGRESS_JSON.exists():
        try:
            existing = json.loads(config.GOLD_PROGRESS_JSON.read_text(encoding="utf-8"))
            if isinstance(existing, list) and existing and "id" in existing[0]:
                judged = existing
                done_ids = {int(item["id"]) for item in judged}
                print(f"Resuming with {len(done_ids)} already judged", flush=True)
        except Exception:
            judged = []
            done_ids = set()

    pending = df[~df["id"].isin(done_ids)].copy()
    batch_size = config.CURATION["batch_size"]
    provider = config.LLM["provider"]

    print(f"Provider: {provider}", flush=True)
    print(f"Model:    {model_name()}", flush=True)
    print(f"Batch:    {batch_size}", flush=True)
    print(f"Raw rows: {len(df)} | remaining: {len(pending)}", flush=True)

    if pending.empty:
        _, this_n, gold_n = _persist_outputs(judged, existing_gold)
        print(
            f"Nothing left to curate. This-run keep {this_n} | merged gold {gold_n}",
            flush=True,
        )
        return config.GOLD_CSV

    rows = pending.to_dict("records")
    total_batches = (len(rows) + batch_size - 1) // batch_size
    max_chars = config.CURATION["max_review_chars"]

    for batch_index in range(total_batches):
        start = batch_index * batch_size
        end = min(start + batch_size, len(rows))
        batch = rows[start:end]
        batch_ids = [int(row["id"]) for row in batch]

        lines = []
        for row in batch:
            text = str(row.get("text") or "").replace("\n", " ").strip()
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            lines.append(
                f"[{row['id']}] source={row.get('source', 'unknown')} "
                f"date={row.get('date', '')} text={text}"
            )

        print(
            f"[batch {batch_index + 1}/{total_batches}] judging ids {batch_ids[0]}-{batch_ids[-1]}...",
            flush=True,
        )
        mode = (config.CURATION.get("mode") or "auto").lower()
        use_heuristic = mode == "heuristic"

        if not use_heuristic:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(
                        reviews_block="\n".join(lines)
                    ),
                },
            ]
            try:
                raw = call_llm(
                    messages,
                    max_tokens=config.CURATION["max_tokens"],
                    force_json=True,
                )
                parsed = extract_json(raw)
                decisions = _normalize_decisions(parsed, batch_ids)
            except Exception as exc:
                err = str(exc)
                if mode == "llm":
                    raise
                print(f"  LLM batch failed ({exc}) — using heuristic for this batch", flush=True)
                use_heuristic = True
                if "402" in err or "depleted" in err.lower() or "credits" in err.lower():
                    print(
                        "  LLM credits unavailable — switching remaining batches to heuristic mode",
                        flush=True,
                    )
                    config.CURATION["mode"] = "heuristic"

        if use_heuristic:
            decisions = [
                {"id": int(row["id"]), **_heuristic_decision(str(row.get("text") or ""))}
                for row in batch
            ]

        for row, decision in zip(batch, decisions):
            judged.append(
                {
                    "id": int(row["id"]),
                    "source": row.get("source", ""),
                    "date": "" if pd.isna(row.get("date")) else str(row.get("date")),
                    "text": row.get("text", ""),
                    "keep_for_gold": decision["keep_for_gold"],
                    "relevance_score": decision["relevance_score"],
                    "primary_signal": decision["primary_signal"],
                    "rationale": decision["rationale"],
                    "noise_category": decision["noise_category"],
                }
            )

        judged_n, this_n, gold_n = _persist_outputs(judged, existing_gold)
        print(
            f"  saved judgments {judged_n}/{len(df)} | this-run keep {this_n} | merged gold {gold_n}",
            flush=True,
        )
        if not use_heuristic:
            time.sleep(1)

    judged_n, this_n, gold_n = _persist_outputs(judged, existing_gold)
    kept_n = sum(1 for row in judged if row.get("keep_for_gold"))
    print("\n=== Done ===", flush=True)
    print(f"Judged rows: {judged_n}", flush=True)
    print(f"This-run keep_for_gold: {kept_n} (capped to {this_n})", flush=True)
    print(f"Merged gold rows saved: {gold_n}", flush=True)
    print(f"Saved progress: {config.GOLD_PROGRESS_JSON}", flush=True)
    print(f"Saved gold JSON: {config.GOLD_JSON}", flush=True)
    print(f"Saved gold CSV:  {config.GOLD_CSV}", flush=True)
    return config.GOLD_CSV


if __name__ == "__main__":
    progress = config.GOLD_PROGRESS_JSON
    if progress.exists():
        try:
            old = json.loads(progress.read_text(encoding="utf-8"))
            csv_df = pd.read_csv(config.OUTPUT_CSV)
            csv_n = len(csv_df)
            ids = sorted(int(x["id"]) for x in old) if isinstance(old, list) else []
            old_texts = {
                _normalize_text(x.get("text"))
                for x in old
                if isinstance(x, dict)
            } - {""}
            csv_texts = {
                _normalize_text(t) for t in csv_df.get("text", pd.Series(dtype=str)).fillna("")
            } - {""}
            overlap = (len(old_texts & csv_texts) / len(old_texts)) if old_texts else 0.0
            if not ids or ids[0] != 1 or max(ids) > csv_n or overlap < 0.5:
                progress.unlink()
                print(
                    f"Cleared incompatible gold_curation_progress.json (text overlap {overlap:.0%})",
                    flush=True,
                )
        except Exception:
            progress.unlink(missing_ok=True)
    curate_gold(resume=True)
