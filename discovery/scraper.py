"""
Discovery Engine scraper — collect reviews into one CSV:
  source | text | date

All knobs: shared/config.py
Run from project root:
  python discovery/scraper.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd

from shared import config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_date(value) -> str:
    """Normalize many date shapes to YYYY-MM-DD or empty string."""
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, (int, float)):
        # unix seconds or ms
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        try:
            return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
        except (OSError, OverflowError, ValueError):
            return ""
    text = str(value).strip()
    if not text:
        return ""
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text[:10]


def _clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(str(text).split())


def _row(source: str, text: str, date="") -> dict | None:
    text = _clean_text(text)
    if len(text) < 15:
        return None
    return {"source": source, "text": text, "date": _to_date(date)}


# ---------------------------------------------------------------------------
# 1) Google Play Store
# ---------------------------------------------------------------------------

def scrape_play_store() -> list[dict]:
    from google_play_scraper import Sort, reviews

    sort_map = {
        "newest": Sort.NEWEST,
        "rating": Sort.RATING,
        "most_relevant": Sort.MOST_RELEVANT,
    }
    cfg = config.PLAY_STORE
    sort = sort_map.get(cfg.get("sort", "newest"), Sort.NEWEST)
    target = cfg["count"]

    print(f"[play_store] fetching up to {target} reviews...")
    result = []
    token = None
    while len(result) < target:
        batch, token = reviews(
            cfg["app_id"],
            lang=cfg.get("lang", "en"),
            country=cfg.get("country", "in"),
            sort=sort,
            count=min(200, target - len(result)),
            continuation_token=token,
        )
        if not batch:
            break
        result.extend(batch)
        if not token:
            break

    rows = []
    for item in result:
        r = _row("play_store", item.get("content", ""), item.get("at"))
        if r:
            rows.append(r)
    print(f"[play_store] kept {len(rows)} reviews")
    return rows


# ---------------------------------------------------------------------------
# 2) Apple App Store
# ---------------------------------------------------------------------------

def _atom_label(item: dict, key: str) -> str:
    val = item.get(key)
    if isinstance(val, dict):
        return str(val.get("label") or "")
    if val is None:
        return ""
    return str(val)


def _rss_entries(payload: dict, page: int) -> list[dict]:
    """Normalize Apple RSS `entry` to a list of review dicts.

    Page 1 sometimes starts with app metadata (`im:name`, no `im:rating`).
    Real reviews also have `im:name` (author), so only strip metadata.
    A single review arrives as a dict, not a list.
    """
    entries = payload.get("feed", {}).get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]
    if not isinstance(entries, list):
        return []
    if page == 1 and entries:
        first = entries[0] if isinstance(entries[0], dict) else {}
        has_name = "im:name" in first
        has_rating = "im:rating" in first
        if has_name and not has_rating:
            entries = entries[1:]
    return [item for item in entries if isinstance(item, dict)]


def scrape_app_store() -> list[dict]:
    """Apple public RSS feed - no auth, no fragile scraper package."""
    import requests

    cfg = config.APP_STORE
    countries = cfg.get("countries") or [cfg.get("country", "in")]
    app_id = cfg["app_id"]
    target = cfg.get("count", 150)
    print(f"[app_store] fetching up to {target} reviews via iTunes RSS...")
    print(f"[app_store] countries: {', '.join(countries)}")

    rows: list[dict] = []
    seen: set[str] = set()

    for country in countries:
        if len(rows) >= target:
            break
        country_before = len(rows)
        # RSS returns ~50 per page; pages are 1..10
        for page in range(1, 11):
            if len(rows) >= target:
                break
            url = (
                f"https://itunes.apple.com/{country}/rss/customerreviews/"
                f"page={page}/id={app_id}/sortBy=mostRecent/json"
            )
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                payload = resp.json()
            except Exception as exc:
                print(f"[app_store] {country} page {page} failed: {exc}")
                break

            entries = _rss_entries(payload, page)
            if not entries:
                if page == 1:
                    print(f"[app_store] {country} empty (no review entries) — skipping")
                break

            before = len(rows)
            for item in entries:
                review_id = _atom_label(item, "id") or f"{country}-{page}-{len(seen)}"
                if review_id in seen:
                    continue
                seen.add(review_id)
                title = _atom_label(item, "title")
                body = _atom_label(item, "content")
                text = f"{title}. {body}".strip() if title else body
                r = _row("app_store", text, _atom_label(item, "updated"))
                if r:
                    rows.append(r)
                if len(rows) >= target:
                    break
            if len(rows) == before:
                break

        added = len(rows) - country_before
        if added:
            print(f"[app_store] {country}: +{added} (running total {len(rows)})")

    if not rows:
        raise RuntimeError(
            "[app_store] 0 reviews after scanning countries "
            f"{countries}. Check RSS feeds / countries list — refusing to drop this source silently."
        )

    print(f"[app_store] kept {len(rows)} reviews")
    return rows


# ---------------------------------------------------------------------------
# 3) YouTube comments
# ---------------------------------------------------------------------------

def scrape_youtube() -> list[dict]:
    cfg = config.YOUTUBE
    if not cfg.get("api_key"):
        print("[youtube] skipped - set api_key in config.py")
        return []

    from googleapiclient.discovery import build

    youtube = build("youtube", "v3", developerKey=cfg["api_key"])
    rows: list[dict] = []
    video_ids: list[str] = []

    for query in cfg.get("search_queries", []):
        print(f"[youtube] search: {query!r}")
        try:
            resp = (
                youtube.search()
                .list(
                    q=query,
                    part="id",
                    type="video",
                    maxResults=cfg.get("max_videos_per_query", 5),
                    order=cfg.get("order", "relevance"),
                    regionCode="IN",
                )
                .execute()
            )
        except Exception as exc:
            print(f"[youtube] search failed: {exc}")
            continue

        for item in resp.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if vid and vid not in video_ids:
                video_ids.append(vid)

    for vid in video_ids:
        print(f"[youtube] comments for video {vid}")
        try:
            resp = (
                youtube.commentThreads()
                .list(
                    part="snippet",
                    videoId=vid,
                    maxResults=min(cfg.get("max_comments_per_video", 40), 100),
                    textFormat="plainText",
                    order="relevance",
                )
                .execute()
            )
        except Exception as exc:
            print(f"[youtube] comments failed for {vid}: {exc}")
            continue

        for item in resp.get("items", []):
            snippet = item["snippet"]["topLevelComment"]["snippet"]
            r = _row("youtube", snippet.get("textDisplay", ""), snippet.get("publishedAt"))
            if r:
                rows.append(r)

    print(f"[youtube] kept {len(rows)} comments")
    return rows


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def source_balanced_cap(df: pd.DataFrame, target: int) -> pd.DataFrame:
    """Keep up to `target` rows with a per-source quota, then fill leftovers.

    Stops YouTube (scraped last, high volume) from wiping Play / App Store
    when applying TARGET_TOTAL.
    """
    if len(df) <= target:
        return df.reset_index(drop=True)

    sources = [s for s in df["source"].drop_duplicates().tolist() if s]
    n_sources = max(1, len(sources))
    quota = target // n_sources

    taken: list[pd.DataFrame] = []
    extras: list[pd.DataFrame] = []
    for source in sources:
        subset = df[df["source"] == source]
        take_n = min(len(subset), quota)
        taken.append(subset.iloc[:take_n])
        if len(subset) > take_n:
            extras.append(subset.iloc[take_n:])

    result = pd.concat(taken, ignore_index=True) if taken else df.iloc[0:0]
    remaining = target - len(result)
    if remaining > 0 and extras:
        extra_df = pd.concat(extras, ignore_index=True)
        result = pd.concat([result, extra_df.iloc[:remaining]], ignore_index=True)
    return result.reset_index(drop=True)


def run_scraper() -> Path:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []

    if config.ENABLE_PLAY_STORE:
        try:
            all_rows.extend(scrape_play_store())
        except Exception as exc:
            print(f"[play_store] ERROR: {exc}")

    if config.ENABLE_APP_STORE:
        # Fail loud on 0 rows — do not swallow; App Store must not vanish silently.
        all_rows.extend(scrape_app_store())

    if config.ENABLE_YOUTUBE:
        try:
            all_rows.extend(scrape_youtube())
        except Exception as exc:
            print(f"[youtube] ERROR: {exc}")

    if not all_rows:
        print("No data collected. Enable a source or add API keys in config.py.")
        sys.exit(1)

    df = pd.DataFrame(all_rows, columns=["source", "text", "date"])
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)

    if len(df) > config.TARGET_TOTAL:
        df = source_balanced_cap(df, config.TARGET_TOTAL)

    out = config.OUTPUT_CSV
    df.to_csv(out, index=False, encoding="utf-8")

    print("\n=== Done ===")
    print(df["source"].value_counts().to_string())
    print(f"\nTotal rows: {len(df)}")
    print(f"Saved to: {out}")
    return out


if __name__ == "__main__":
    run_scraper()
