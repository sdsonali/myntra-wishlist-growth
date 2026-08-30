"""
All scrape/tag/query settings live here. Secrets live in .env locally,
or Streamlit Cloud Secrets when deployed.

Edit counts / toggles / queries / LLM provider here.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

# shared/config.py → project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env(name: str) -> str:
    val = (os.getenv(name) or "").strip()
    if val:
        return val
    try:
        import streamlit as st

        secret = st.secrets.get(name)
        if secret is not None:
            return str(secret).strip()
    except Exception:
        pass
    return ""


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DISCOVERY_DATA = BASE_DIR / "discovery" / "data"
MVP_DATA = BASE_DIR / "mvp" / "data"

OUTPUT_CSV = DISCOVERY_DATA / "reviews.csv"
TAGGED_JSON = DISCOVERY_DATA / "tagged_reviews.json"
OPPORTUNITY_JSON = DISCOVERY_DATA / "opportunity_table.json"
OPPORTUNITY_CSV = DISCOVERY_DATA / "opportunity_table.csv"
GOLD_PROGRESS_JSON = DISCOVERY_DATA / "gold_curation_progress.json"
GOLD_JSON = DISCOVERY_DATA / "gold_reviews.json"
GOLD_CSV = DISCOVERY_DATA / "gold_reviews.csv"
GOLD_TAGGED_JSON = DISCOVERY_DATA / "gold_tagged_reviews.json"

MVP_CATALOG = MVP_DATA / "mvp_catalog.json"
MVP_IMAGES = MVP_DATA / "mvp_images"

SURVEY_CSV = BASE_DIR / "survey" / "responses" / "Wishlist shopping decisions.csv"

# Back-compat aliases used by older call sites
DATA_DIR = DISCOVERY_DATA

# ---------------------------------------------------------------------------
# Which sources to run (toggle True/False to test individually)
# ---------------------------------------------------------------------------
ENABLE_PLAY_STORE = True
ENABLE_APP_STORE = True
ENABLE_YOUTUBE = True

# Discovery corpus targets
TARGET_TOTAL = 1000
GOLD_TARGET_TOTAL = 600  # this-run keep cap before merge
GOLD_MAX_TOTAL = 1000  # rolling gold hard cap after merge/dedupe

SOURCE_LABELS = {
    "play_store": "Google Play",
    "app_store": "App Store",
    "youtube": "YouTube",
}

# ---------------------------------------------------------------------------
# Google Play Store  (free, no auth)
# ---------------------------------------------------------------------------
PLAY_STORE = {
    "app_id": "com.myntra.android",
    "lang": "en",
    "country": "in",
    "count": 450,
    "sort": "newest",  # newest | rating | most_relevant
}

# ---------------------------------------------------------------------------
# Apple App Store  (free iTunes RSS, no auth)
# India RSS is often empty; keep extra storefronts so the source is not 0.
# ---------------------------------------------------------------------------
APP_STORE = {
    "app_id": 907394059,
    "country": "in",
    "countries": ["in", "us", "gb", "ae", "sg"],
    "count": 300,
}

# ---------------------------------------------------------------------------
# YouTube Data API v3 — key from .env (YOUTUBE_API_KEY)
# ---------------------------------------------------------------------------
YOUTUBE = {
    "api_key": _env("YOUTUBE_API_KEY"),
    "search_queries": [
        "myntra haul review",
        "myntra unboxing",
        "myntra shopping review india",
        "myntra",
    ],
    "max_videos_per_query": 15,
    "max_comments_per_video": 50,
    "order": "relevance",  # relevance | date | viewCount
}

# ---------------------------------------------------------------------------
# LLM tagging / answers — swap provider here; keys in .env
# ---------------------------------------------------------------------------
LLM = {
    "provider": "huggingface",  # huggingface | groq | gemini
    "batch_size": 10,
    "max_retries": 3,
    "retry_sleep_sec": 8,
    "temperature": .3,
    "max_tokens": 2500,
    "models": {
        "huggingface": "meta-llama/Llama-3.1-8B-Instruct",
        "groq": "llama-3.1-8b-instant",
        "gemini": "gemini-1.5-flash",
    },
    "gemini_api_key": _env("GEMINI_API_KEY"),
    "groq_api_key": _env("GROQ_API_KEY"),
    "huggingface_api_key": _env("HUGGINGFACE_API_KEY"),
}

# Bump when reason/external taxonomies or the tagger prompt change.
# tagger.py retags the whole gold corpus once, then resumes by normalized text.
TAG_SCHEMA_VERSION = 2

REASON_LABELS = [
    "liked_look",
    "occasion_save",
    "compare_later",
    "need_uncertainty",
    "style_confirmation",
    "price_wait",
    "budget_wait",
    "just_browsing",
]

EXTERNAL_LABELS = [
    "instagram",
    "youtube",
    "google",
    "friend_family",
    "other_apps",
    "physical_store",
    "influencer",
]

BLOCKER_LABELS = [
    "fit_uncertainty",
    "price_change",
    "found_alternative",
    "forgot",
    "quality_doubt",
    "occasion_mismatch",
    "no_urgency",
]

# LLM sometimes emits close synonyms / the old schema.
REASON_ALIASES = {
    "gift_idea": "liked_look",
    "wait_for_sale": "price_wait",
    "sale_wait": "price_wait",
    "waiting_for_sale": "price_wait",
    "salary_wait": "budget_wait",
    "wait_for_salary": "budget_wait",
    "saving_up": "budget_wait",
    "liked_how_it_looked": "liked_look",
    "looks_good": "liked_look",
    "occasion": "occasion_save",
    "saving_for_occasion": "occasion_save",
    "comparing": "compare_later",
    "comparison": "compare_later",
    "not_sure_i_need_it": "need_uncertainty",
    "unsure_need": "need_uncertainty",
    "style_check": "style_confirmation",
    "browsing": "just_browsing",
}

EXTERNAL_ALIASES = {
    "google_search": "google",
    "google_reviews": "google",
    "review_video": "youtube",
    "yt": "youtube",
    "insta": "instagram",
    "ig": "instagram",
    "friend": "friend_family",
    "family": "friend_family",
    "sister": "friend_family",
    "asked_friend": "friend_family",
    "asked_sister": "friend_family",
    "ajio": "other_apps",
    "amazon": "other_apps",
    "flipkart": "other_apps",
    "meesho": "other_apps",
    "nykaa": "other_apps",
    "store": "physical_store",
    "offline_store": "physical_store",
    "blogger": "influencer",
}

# ---------------------------------------------------------------------------
# Gold corpus curation
# ---------------------------------------------------------------------------
CURATION = {
    "mode": "auto",  # auto | llm | heuristic  (auto falls back if LLM credits fail)
    "batch_size": 8,
    "max_review_chars": 450,
    "max_tokens": 2200,
    "min_text_chars": 20,
    "keep_labels": [
        "fit_uncertainty",
        "quality_doubt",
        "price_hesitation",
        "comparison_behavior",
        "occasion_styling_mismatch",
        "liked_look",
        "wishlist_delay",
        "external_research",
    ],
    "drop_labels": [
        "generic_app_praise",
        "generic_service_issue",
        "spam_or_noise",
        "off_topic",
        "unclear_signal",
    ],
}

# ---------------------------------------------------------------------------
# Survey overlay (interview/form layer — not merged into corpus %)
# ---------------------------------------------------------------------------
SURVEY_OVERLAY = {
    "csv_path": SURVEY_CSV,
    "external_column": (
        "Before deciding on an item like this, do you do anything outside the app? "
        "(Select all that apply)"
    ),
    "none_values": ("", "none", "no", "n/a", "na", "nothing", "nil"),
    "fallback_n": 10,
    "fallback_pct_external": 100.0,
}

# ---------------------------------------------------------------------------
# Discovery query UI (Streamlit Tab 1)
# ---------------------------------------------------------------------------
QUERY = {
    "max_excerpts": 12,
    "max_excerpt_chars": 280,
    "answer_max_tokens": 700,
    # Questions are routed to tag labels by the LLM (see app.route_corpus_question)
    # and ranked by how many of those labels a row carries, so there are no
    # keyword lists or match weights to tune here.
    "starter_questions": [
        {
            "label": "Fit",
            "question": "Why does fit or sizing stop shoppers from buying wishlisted items?",
        },
        {
            "label": "Quality",
            "question": "What quality or fabric doubts keep wishlisted items unbought?",
        },
        {
            "label": "Price",
            "question": "How do price, sales, and budget affect wishlist conversion?",
        },
        {
            "label": "Occasion",
            "question": "How do occasion and styling mismatch delay wishlist purchases?",
        },
        {
            "label": "Comparison",
            "question": "How do shoppers compare alternatives before buying from wishlist?",
        },
        {
            "label": "Left the app",
            "question": "Where do shoppers go outside the app before buying a wishlisted item?",
        },
    ],
}


def preferred_review_csv() -> Path:
    if GOLD_CSV.exists():
        return GOLD_CSV
    return OUTPUT_CSV


def preferred_tagged_json() -> Path:
    if GOLD_TAGGED_JSON.exists():
        return GOLD_TAGGED_JSON
    return TAGGED_JSON
