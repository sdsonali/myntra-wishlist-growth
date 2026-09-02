"""
Discovery Engine + MVP (Streamlit).

Tab 1 = AI Discovery Engine
Tab 2 = Fit & Confidence Assistant

Run from project root:
  streamlit run app.py
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

from shared import config
from discovery.aggregate import aggregate, save_opportunity
from shared.llm_client import call_llm, extract_json
from mvp import (
    analyze,
    badge_label,
    compare_table,
    llm_compare_products,
    load_catalog,
    resolve_question,
    size_in_hub,
    sku_express_ready,
)
from mvp.express import extract_pincodes, hub_for_pin, load_express_hubs, stock_caption

st.set_page_config(
    page_title="Myntra Wishlist — Discovery + Confidence Assistant",
    page_icon="🛍️",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_tagged() -> list[dict]:
    path = config.preferred_tagged_json()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data.get("reviews") or data.get("rows") or []
    return data if isinstance(data, list) else []


@st.cache_data(show_spinner=False)
def load_opportunity() -> dict:
    path = config.OPPORTUNITY_JSON
    preferred_corpus = (
        "gold" if config.preferred_tagged_json() == config.GOLD_TAGGED_JSON else "raw"
    )
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("source_corpus") == preferred_corpus and data.get("survey_overlay"):
            return data
    # Build on the fly if aggregate.py hasn't been run yet
    if config.preferred_tagged_json().exists():
        result = aggregate()
        save_opportunity(result)
        return result
    return {}


def _nonempty(value) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    return text not in ("", "null", "none", "nan", "—", "-")


def _is_true(value) -> bool:
    return value in (True, "true", "True", 1, "yes", "Yes")


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", (text or "").lower()))


@st.cache_data(show_spinner=False)
def token_idf(corpus_key: str, _rows: list[dict]) -> dict[str, float]:
    """How much each word narrows the corpus, learned from the corpus itself.

    A stopword list can't do this job here: "quality" appears in 21% of reviews
    and "myntra" in 18%, yet the first is the signal and the second is noise, so
    no frequency cutoff separates them. Inverse document frequency ranks them
    without anyone maintaining a word list.
    """
    if not _rows:
        return {}
    doc_freq: Counter = Counter()
    for row in _rows:
        doc_freq.update({t for t in _tokens(row.get("text")) if len(t) >= 3})
    n = len(_rows)
    return {tok: math.log(n / (1 + df)) for tok, df in doc_freq.items()}


ROUTER_SYSTEM = (
    "You route a product manager's question to the tagged review labels that answer "
    "it. The corpus is public Myntra reviews, each tagged with at most one label per "
    "field.\n"
    'Return ONLY JSON: {"intent": "...", "blockers": [], "reasons": [], '
    '"comparison": false, "external": false}\n'
    "intent: three or four words naming what the question is really asking.\n"
    "blockers: labels from the purchase_blocker vocabulary that bear on the question.\n"
    "reasons: labels from the reason_for_wishlisting vocabulary that bear on it.\n"
    "comparison: true if the question is about comparing items, apps or alternatives.\n"
    "external: true if it is about leaving the app to research.\n"
    "Pick only what the question actually asks about, with one exception: a broad "
    "question about hesitation, delay or why people do not buy is asking about "
    "blockers in general, so return every blocker label that could plausibly apply "
    "rather than narrowing to a guess. Returning an empty list for such a question is "
    "wrong."
)


def route_corpus_question(question: str) -> dict:
    """Ask the model which tagged labels answer this question."""
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM},
        {
            "role": "user",
            "content": (
                f"purchase_blocker vocabulary: {', '.join(config.BLOCKER_LABELS)}\n"
                f"reason_for_wishlisting vocabulary: {', '.join(config.REASON_LABELS)}\n\n"
                f"Question: {question}"
            ),
        },
    ]
    raw = call_llm(messages, max_tokens=300, force_json=True)
    data = extract_json(raw)

    def _known(values, vocabulary: list[str]) -> list[str]:
        if not isinstance(values, list):
            return []
        picked = []
        for v in values:
            label = str(v).strip()
            if label in vocabulary and label not in picked:
                picked.append(label)
        return picked

    return {
        "intent": str(data.get("intent") or "").strip(),
        "blockers": _known(data.get("blockers"), config.BLOCKER_LABELS),
        "reasons": _known(data.get("reasons"), config.REASON_LABELS),
        "comparison": bool(data.get("comparison")),
        "external": bool(data.get("external")),
    }


def _label_score(row: dict, plan: dict) -> int:
    """How many of the routed signals this row carries."""
    score = 0
    if str(row.get("purchase_blocker") or "").strip() in plan["blockers"]:
        score += 1
    if str(row.get("reason_for_wishlisting") or "").strip() in plan["reasons"]:
        score += 1
    if plan["comparison"] and _is_true(row.get("comparison_behavior")):
        score += 1
    if plan["external"] and _nonempty(row.get("info_sought_outside_app")):
        score += 1
    return score


def _text_score(row: dict, q_tokens: set[str], idf: dict[str, float]) -> float:
    blob = str(row.get("text") or "").lower()
    return round(
        sum(idf.get(tok, 0.0) for tok in q_tokens if len(tok) >= 3 and tok in blob),
        3,
    )


def _diversify(scored: list[tuple, dict], limit: int) -> list[dict]:
    """Spread the picks across review sources so one platform can't own an answer."""
    if not scored:
        return []
    by_source: dict[str, list[tuple]] = {}
    for item in scored:
        src = str(item[1].get("source") or "unknown")
        by_source.setdefault(src, []).append(item)
    n_src = max(1, len(by_source))
    quota = max(1, limit // n_src)
    picked: list[tuple] = []
    leftovers: list[tuple] = []
    for items in by_source.values():
        picked.extend(items[:quota])
        leftovers.extend(items[quota:])
    picked.sort(key=lambda x: x[0], reverse=True)
    leftovers.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in (picked + leftovers)[:limit]]


def filter_reviews(
    question: str,
    rows: list[dict],
    limit: int,
    plan: dict,
    idf: dict[str, float] | None = None,
) -> list[dict]:
    """Retrieve rows carrying the routed labels; wording only breaks ties.

    Ranking on a tuple rather than a weighted sum means no magic number decides
    how many keyword hits outrank a real tag match.
    """
    q_tokens = _tokens(question)
    idf = idf or {}

    scored: list[tuple[tuple[int, float], dict]] = []
    for row in rows:
        labels = _label_score(row, plan)
        text = _text_score(row, q_tokens, idf)
        if labels or text:
            scored.append(((labels, text), row))

    scored.sort(key=lambda x: x[0], reverse=True)
    return _diversify(scored, limit)


ANSWER_SYSTEM = (
    "You brief a product manager from tagged public reviews about Myntra wishlist "
    "hesitation. Use ONLY the excerpts and the COUNTS block given.\n"
    'Return ONLY JSON: {"points": ["...", "..."], "validate": "..."}\n'
    "points: 4 to 6 findings, one sentence each. The first must name the largest "
    "purchase blocker with its count. Open with the finding itself — never 'Here are', "
    "never 'The data shows'. Do not number them yourself, and never refer to an "
    "excerpt by its number; the reader cannot see them.\n"
    "Ignore excerpts that are only about delivery, packaging, refunds or support. "
    "Those are operations complaints, not wishlist decision signal.\n"
    "validate: one question to ask a shopper about their own behaviour at the moment "
    "they hesitated. Not a question about what Myntra should build, and not a leading "
    "question that assumes the answer.\n"
    "NUMBERS ARE NOT YOURS TO INVENT. Before writing any figure, find it in the COUNTS "
    "block; if it is not there, write the sentence without a figure. Never add, divide "
    "or estimate one, and never combine two counts — nothing tells you how many "
    "reviews in one count also belong to another. Points citing a figure that is not "
    "in the COUNTS block are discarded before the reader sees them.\n"
    "Percentages in the COUNTS block are shares of the matched reviews, not of all "
    "shoppers — phrase them that way.\n"
    "Researching outside the app and comparing options are behaviours, not purchase "
    "blockers. Only the labels under 'Purchase blockers tagged' are blockers.\n"
    "Rules: comparing items and leaving the app are decision behaviour, not lifestyle "
    "preference. Never recommend fixing catalogue quality, logistics or support — "
    "those are not this team's levers. If price appears, report it and mark it out of "
    "scope because there is no discount lever here. If the matched set is thin, say so "
    "in the last point instead of overstating it."
)


def _verify_counts(points: list[str], c: dict) -> list[str]:
    """Drop any finding citing a number that is not in the aggregate.

    The writer is told to copy its figures from the counts block. This makes that
    an enforced property instead of a hope, so a fabricated "1 of 12" never
    reaches a PM who might quote it in a deck.
    """
    n = c["n"]
    allowed = (
        set(c["blocker_counts"].values())
        | set(c["reason_counts"].values())
        | {c["comparison_n"], c["external_n"], n}
    )
    allowed_pct = {c["pct_comparison"], c["pct_external"]}

    kept = []
    for point in points:
        fractions = re.findall(r"(\d+)\s+(?:out\s+)?of\s+(\d+)", point)
        if any(int(total) != n or int(part) not in allowed for part, total in fractions):
            continue
        percents = [float(p) for p in re.findall(r"(\d+(?:\.\d+)?)\s*%", point)]
        if any(round(p, 1) not in allowed_pct for p in percents):
            continue
        kept.append(point)
    return kept


def answer_question(question: str, excerpts: list[dict]) -> dict:
    max_chars = config.QUERY.get("max_excerpt_chars", 280)
    lines = []
    for i, row in enumerate(excerpts, 1):
        text = str(row.get("text") or "").replace("\n", " ").strip()
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        tags = []
        if row.get("purchase_blocker"):
            tags.append(f"blocker={row['purchase_blocker']}")
        if row.get("reason_for_wishlisting"):
            tags.append(f"reason={row['reason_for_wishlisting']}")
        if row.get("comparison_behavior") in (True, "true", "True"):
            tags.append("comparison=true")
        if row.get("info_sought_outside_app"):
            tags.append(f"outside={row['info_sought_outside_app']}")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(f"{i}. ({row.get('source')}){tag_str} {text}")

    evidence = "\n".join(lines) if lines else "(no matching excerpts)"
    c = consensus_from_excerpts(excerpts)
    n = c["n"]

    def _breakdown(counts: dict[str, int]) -> str:
        if not counts:
            return "none tagged"
        return "; ".join(
            f"{label.replace('_', ' ')} {value} of {n}"
            for label, value in sorted(counts.items(), key=lambda kv: -kv[1])
        )

    counts = "\n".join(
        [
            f"Matched reviews: {n}",
            f"Sources: {', '.join(c['sources_used']) or 'none'}",
            f"Purchase blockers tagged: {_breakdown(c['blocker_counts'])}",
            f"Wishlisting reasons tagged: {_breakdown(c['reason_counts'])}",
            f"Compared items or apps: {c['comparison_n']} of {n} "
            f"({c['pct_comparison']}% of matched reviews)",
            f"Researched outside the app: {c['external_n']} of {n} "
            f"({c['pct_external']}% of matched reviews)",
        ]
    )

    messages = [
        {"role": "system", "content": ANSWER_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"COUNTS:\n{counts}\n\n"
                f"Excerpts:\n{evidence}"
            ),
        },
    ]
    raw = call_llm(
        messages,
        max_tokens=config.QUERY.get("answer_max_tokens", 700),
        force_json=True,
    )
    data = extract_json(raw)
    points = []
    for point in data.get("points") or []:
        # The UI numbers the list, so drop any numbering the model added itself.
        text = re.sub(r"^\s*\d+[.)]\s*", "", str(point)).strip()
        if text:
            points.append(text)
    if not points:
        raise ValueError("Model returned no findings")
    verified = _verify_counts(points, c)
    if not verified:
        raise ValueError("Every finding cited a number the corpus does not support")
    return {
        "points": verified[:6],
        "validate": str(data.get("validate") or "").strip(),
    }


def consensus_from_excerpts(excerpts: list[dict]) -> dict:
    """Aggregate matched rows into theme/source consensus — no raw quotes."""
    n = len(excerpts)
    blockers = Counter()
    reasons = Counter()
    sources = Counter()
    compare_n = 0
    external_n = 0

    for row in excerpts:
        sources[str(row.get("source") or "unknown")] += 1
        if _nonempty(row.get("purchase_blocker")):
            blockers[str(row["purchase_blocker"]).strip()] += 1
        if _nonempty(row.get("reason_for_wishlisting")):
            reasons[str(row["reason_for_wishlisting"]).strip()] += 1
        if _is_true(row.get("comparison_behavior")):
            compare_n += 1
        if _nonempty(row.get("info_sought_outside_app")):
            external_n += 1

    def _top(counter: Counter, limit: int = 5) -> pd.DataFrame:
        if not counter:
            return pd.DataFrame({"theme": [], "count": []})
        rows = [{"theme": k, "count": v} for k, v in counter.most_common(limit)]
        return pd.DataFrame(rows).set_index("theme")

    source_labels = getattr(config, "SOURCE_LABELS", None) or {
        "play_store": "Google Play",
        "app_store": "App Store",
        "youtube": "YouTube",
    }
    source_mix = [
        {"source": source_labels.get(k, k), "reviews": v}
        for k, v in sources.most_common()
    ]

    return {
        "n": n,
        "blocker_df": _top(blockers),
        "reason_df": _top(reasons),
        "blocker_counts": dict(blockers),
        "reason_counts": dict(reasons),
        "source_df": pd.DataFrame(source_mix).set_index("source")
        if source_mix
        else pd.DataFrame({"source": [], "reviews": []}),
        "comparison_n": compare_n,
        "external_n": external_n,
        "pct_comparison": round(100.0 * compare_n / n, 1) if n else 0.0,
        "pct_external": round(100.0 * external_n / n, 1) if n else 0.0,
        "blocker_mentions": sum(blockers.values()),
        "reason_mentions": sum(reasons.values()),
        "top_blocker": blockers.most_common(1)[0][0] if blockers else None,
        "sources_used": [source_labels.get(k, k) for k, _ in sources.most_common()],
    }


def render_routing_note(plan: dict) -> None:
    """Show what the router matched on — this tab is a PM console, so routing is fair game."""
    if not plan:
        return
    picked = list(plan.get("blockers") or []) + list(plan.get("reasons") or [])
    if plan.get("comparison"):
        picked.append("comparison behaviour")
    if plan.get("external"):
        picked.append("research outside the app")
    if not picked:
        return
    labels = ", ".join(p.replace("_", " ") for p in picked)
    intent = plan.get("intent") or "this question"
    st.caption(f"Routed *{intent}* to tagged signals: {labels}.")


def render_evidence_consensus(excerpts: list[dict]) -> None:
    """Show charts + consensus instead of raw review quotes."""
    c = consensus_from_excerpts(excerpts)
    if c["n"] == 0:
        st.warning("No matching signals for this question in the tagged corpus.")
        return

    st.markdown("### What the matching signals say")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Signals matched", c["n"])
    m2.metric("With a purchase blocker", c["blocker_mentions"])
    m3.metric("Comparison behavior", f"{c['pct_comparison']}%")
    m4.metric("Looked outside the app", f"{c['pct_external']}%")

    if c["top_blocker"]:
        st.success(
            f"**Consensus:** among matched reviews, the strongest purchase-blocker theme is "
            f"`{c['top_blocker'].replace('_', ' ')}`."
        )

    g1, g2 = st.columns(2)
    with g1:
        st.caption("Themes in this answer (purchase blockers)")
        if not c["blocker_df"].empty:
            st.bar_chart(c["blocker_df"])
        else:
            st.caption("No blocker tags in this match set.")
    with g2:
        st.caption("Where these signals came from")
        if not c["source_df"].empty:
            st.bar_chart(c["source_df"])
        else:
            st.caption("No source mix available.")

    if not c["reason_df"].empty:
        st.caption("Wishlisting reasons in this match set")
        st.bar_chart(c["reason_df"])

    sources = ", ".join(c["sources_used"]) if c["sources_used"] else "public review corpus"
    st.caption(
        f"**Source of truth:** {c['n']} theme-routed rows from the tagged discovery corpus "
        f"({sources}). Themes are LLM-tagged labels aggregated for this question — "
        f"individual review text is kept in the backend dataset, not shown here."
    )


# Friendly wait copy (never expose provider / model names)
WAIT_MESSAGES = [
    "Scanning wishlist hesitation patterns…",
    "Comparing blockers across shopper feedback…",
    "Building a grounded consensus for your question…",
    "Connecting themes to conversion opportunities…",
]


def blockers_chart_df(opp: dict) -> pd.DataFrame:
    rows = opp.get("top_purchase_blockers") or []
    if not rows:
        return pd.DataFrame({"label": [], "pct_of_mentions": []})
    df = pd.DataFrame(rows)
    return df.set_index("label")[["pct_of_mentions"]]


def reasons_chart_df(opp: dict) -> pd.DataFrame:
    rows = opp.get("top_reasons_for_wishlisting") or []
    if not rows:
        return pd.DataFrame({"label": [], "pct_of_mentions": []})
    df = pd.DataFrame(rows)
    return df.set_index("label")[["pct_of_mentions"]]


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("Myntra Wishlist Conversion")
tab1, tab2 = st.tabs(["Discovery Engine", "Fit & Confidence Assistant (MVP)"])

with tab1:
    tagged = load_tagged()
    opp = load_opportunity()
    source_corpus = opp.get("source_corpus") or (
        "gold" if config.preferred_tagged_json() == config.GOLD_TAGGED_JSON else "raw"
    )

    if "disc_answer" not in st.session_state:
        st.session_state.disc_answer = None
        st.session_state.disc_excerpts = None
        st.session_state.disc_plan = None
        st.session_state.disc_starter = None

    if not tagged:
        st.error("No discovery data yet. Run the pipeline locally, then restart the app:")
        st.code("python discovery/run_pipeline.py", language="bash")
    else:
        if not opp:
            st.warning("Opportunity table missing — click rebuild below.")

        col_a, col_b = st.columns([1.2, 1])

        with col_a:
            st.subheader("Ask the discovery corpus")
            st.caption(
                "PM discovery console — grounded in tagged public reviews. "
                "Shopper-facing fit help is on the Fit & Confidence tab."
            )

            starters = config.QUERY.get("starter_questions") or []
            st.markdown("**Theme shortcuts**")
            st.caption(
                "One-click PM questions — the router still decides which tagged "
                "reviews answer them."
            )
            starter_row1 = st.columns(3)
            starter_row2 = st.columns(3)
            for i, starter in enumerate(starters):
                col = starter_row1[i] if i < 3 else starter_row2[i - 3]
                with col:
                    if st.button(
                        starter["label"],
                        key=f"disc_starter_{i}",
                        use_container_width=True,
                    ):
                        st.session_state.disc_starter = starter["question"]
                        st.rerun()

            question = st.text_area(
                "Ask a question about why users don't convert wishlisted items",
                placeholder="e.g. Why do users hesitate after adding items to wishlist?",
                height=100,
            )
            ask = st.button("Get grounded answer", type="primary")

            run_question = None
            if st.session_state.disc_starter:
                run_question = st.session_state.disc_starter
                st.session_state.disc_starter = None
            elif ask and question.strip():
                run_question = question.strip()

            if run_question:
                wait_msg = WAIT_MESSAGES[hash(run_question) % len(WAIT_MESSAGES)]
                with st.spinner(wait_msg):
                    try:
                        plan = route_corpus_question(run_question)
                        excerpts = filter_reviews(
                            run_question,
                            tagged,
                            config.QUERY.get("max_excerpts", 12),
                            plan,
                            idf=token_idf(f"{source_corpus}:{len(tagged)}", tagged),
                        )
                        st.session_state.disc_answer = answer_question(
                            run_question, excerpts
                        )
                        st.session_state.disc_excerpts = excerpts
                        st.session_state.disc_plan = plan
                    except Exception as exc:
                        st.session_state.disc_answer = None
                        st.session_state.disc_excerpts = None
                        st.session_state.disc_plan = None
                        st.error(
                            "Couldn't generate an answer right now. "
                            "Try again in a moment."
                        )
                        st.caption(f"Details: {exc}")
            elif ask:
                st.warning("Enter a question first, or pick a theme shortcut.")

            answer = st.session_state.disc_answer
            if answer:
                st.markdown("### Answer")
                for i, point in enumerate(answer["points"], 1):
                    st.markdown(f"{i}. {point}")
                if answer.get("validate"):
                    st.markdown(f"**Validate in interviews:** {answer['validate']}")
                render_routing_note(st.session_state.disc_plan or {})
                render_evidence_consensus(st.session_state.disc_excerpts or [])

        with col_b:
            st.subheader("Opportunity comparison")
            if opp.get("headline"):
                st.info(opp["headline"])

            m1, m2, m3 = st.columns(3)
            m1.metric("Reviews tagged", opp.get("total_reviews", len(tagged)))
            m2.metric("Comparison behavior", f"{opp.get('pct_comparison_behavior', 0)}%")
            m3.metric(
                "External research (corpus)",
                f"{opp.get('pct_external_research', 0)}%",
            )
            overlay = opp.get("survey_overlay") or {}
            if overlay.get("caption"):
                st.caption(overlay["caption"])
            st.caption(f"Using the `{source_corpus}` discovery corpus as source of truth.")

            by_source = opp.get("by_source") or {}
            if by_source:
                labels = getattr(config, "SOURCE_LABELS", {}) or {}
                mix_rows = [
                    {
                        "source": labels.get(k, k),
                        "reviews": (v or {}).get("total", 0),
                    }
                    for k, v in by_source.items()
                ]
                mix_df = pd.DataFrame(mix_rows).set_index("source")
                st.caption("Source mix (incl. App Store when present)")
                st.bar_chart(mix_df)

            st.caption("Top purchase blockers (% of blocker mentions)")
            st.bar_chart(blockers_chart_df(opp))

            st.caption("Top wishlisting reasons (% of reason mentions)")
            st.bar_chart(reasons_chart_df(opp))

            if st.button("Rebuild opportunity table"):
                load_opportunity.clear()
                result = aggregate()
                save_opportunity(result)
                st.success("Rebuilt opportunity_table.json")
                st.rerun()

        st.divider()
        st.markdown("### How this works")
        st.caption(
            "Scrape public reviews (Play Store / App Store / YouTube) -> "
            "curate a gold corpus with the LLM -> "
            "tag wishlist reasons, purchase blockers, comparison, and outside research -> "
            "aggregate into an opportunity table → "
            "ask questions live. Answers are theme-consensus for PMs, not a shopper assistant. "
            "the UI shows consensus charts and source mix, not raw review dumps."
        )

with tab2:
    IMG_DIR = config.MVP_IMAGES
    st.markdown(
        """
        <style>
        .mvp-card {
          border: 1px solid #eaeaec; border-radius: 10px; padding: 10px;
          background: #fff; margin-bottom: 10px; min-height: 100%;
        }
        .mvp-card.selected {
          border: 2px solid #FF3F6C; background: #fff8fa;
        }
        .mvp-meta { color:#535766; font-size: 0.85rem; margin: 0.15rem 0 0.35rem; }
        .mvp-price { font-weight: 700; color:#282c3f; margin: 0 0 0.4rem; }
        .mvp-badge {
          display:inline-block; background:#282c3f; color:#fff;
          font-size:11px; font-weight:700; padding:3px 8px; border-radius:4px;
          margin: 0.25rem 0 0.5rem;
        }
        .mvp-badge.warn { background:#FF3F6C; }
        .mvp-badge.ok { background:#3e4152; }
        .mvp-answer-block {
          margin: 0.75rem 0 0.25rem;
          padding: 0.65rem 0.75rem;
          border-radius: 8px;
          background: #f4f7f9;
          border-left: 3px solid #ff3f6c;
        }
        .mvp-answer-label {
          font-size: 0.72rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: #535766;
          margin-bottom: 0.25rem;
        }
        .mvp-selected {
          display:inline-block; background:#FF3F6C; color:#fff;
          font-size:11px; font-weight:700; padding:2px 8px; border-radius:10px;
          margin-left:6px; vertical-align: middle;
        }
        .express-panel {
          border: 2px solid #FF3F6C;
          background: #fff5f8;
          border-radius: 12px;
          padding: 14px 14px 6px;
          margin: 0.75rem 0 0.25rem;
          box-shadow: 0 6px 20px rgba(255, 63, 108, 0.28);
        }
        .express-kicker {
          color: #FF3F6C;
          font-size: 0.72rem;
          font-weight: 800;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          margin: 0 0 0.2rem;
        }
        .express-title {
          color: #282c3f;
          font-size: 1.05rem;
          font-weight: 800;
          line-height: 1.3;
          margin: 0 0 0.25rem;
        }
        .express-sub {
          color: #535766;
          font-size: 0.88rem;
          font-weight: 600;
          line-height: 1.35;
          margin: 0 0 0.65rem;
        }
        .express-avail {
          background: #FF3F6C;
          color: #fff;
          font-weight: 700;
          font-size: 0.82rem;
          line-height: 1.35;
          padding: 8px 10px;
          border-radius: 8px;
          margin: 0.45rem 0 0.2rem;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.express-kicker) {
          border: 2px solid #FF3F6C !important;
          background: #fff5f8 !important;
          box-shadow: 0 6px 20px rgba(255, 63, 108, 0.28) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    catalog = load_catalog()
    stats_by_id = {p["id"]: analyze(p) for p in catalog}
    if "bag" not in st.session_state:
        st.session_state.bag = []
    if "focus_id" not in st.session_state:
        st.session_state.focus_id = catalog[0]["id"]
    if "wl_filter" not in st.session_state:
        st.session_state.wl_filter = "All"
    if "mvp_compare_answer" not in st.session_state:
        st.session_state.mvp_compare_answer = None
    if "bag_express" not in st.session_state:
        st.session_state.bag_express = []

    express_hubs = load_express_hubs()

    def _render_shopper_answer(answer: dict, product_id: str) -> None:
        body = (answer.get("answer") or answer.get("bottom_line") or "").strip()
        verdict = (answer.get("verdict") or "").strip()
        if not body:
            st.warning("This answer is stale — click **Get answer** again.")
            return

        label = verdict or "Recommendation"
        vlow = label.lower()
        offline = answer.get("source") == "offline"
        if offline:
            st.warning(f"**{label}**")
        elif vlow.startswith("go"):
            st.success(f"**{label}**")
        elif vlow.startswith("skip"):
            st.error(f"**{label}**")
        elif "size up" in vlow:
            st.warning(f"**{label}**")
        else:
            st.info(f"**{label}**")
        st.markdown(body)
        bullets = answer.get("proof_bullets") or []
        if bullets:
            st.markdown(
                "**Closest reviews**" if offline else "**Why reviewers say this**"
            )
            for bullet in bullets:
                st.markdown(f"- {bullet}")

        b1, b2 = st.columns(2)
        with b1:
            if st.button("Add to bag", key=f"ans_bag_{product_id}", use_container_width=True):
                if product_id not in st.session_state.bag:
                    st.session_state.bag.append(product_id)
                st.toast("Added to bag")
        with b2:
            if st.button(
                "Still not sure",
                key=f"ans_unsure_{product_id}",
                use_container_width=True,
            ):
                st.toast("Saved for later — that's OK.")

    def _apply_wishlist_filter(items: list[dict], choice: str) -> list[dict]:
        if choice == "Ethnic Wear":
            return [p for p in items if p.get("category") == "ethnic_occasion"]
        if choice == "In stock":
            return [p for p in items if p.get("in_stock", True)]
        return list(items)

    wl_col, fit_col = st.columns([1.15, 1], gap="large")

    with wl_col:
        st.subheader("Wishlist")
        pin_raw = st.session_state.get("pincode") or ""
        pins = extract_pincodes(pin_raw)
        hub = hub_for_pin(pin_raw, express_hubs)
        last_pin = st.session_state.get("_express_pin_checked", "")
        if pin_raw != last_pin:
            st.session_state["_express_pin_checked"] = pin_raw
            for key in list(st.session_state.keys()):
                if str(key).startswith("express_prompt_"):
                    del st.session_state[key]

        filter_choice = st.pills(
            "Filter",
            options=["All", "Ethnic Wear", "In stock"],
            default=st.session_state.wl_filter,
            key="wl_filter_pills",
        )
        if filter_choice:
            st.session_state.wl_filter = filter_choice

        visible = _apply_wishlist_filter(catalog, st.session_state.wl_filter)
        st.caption(f"Showing {len(visible)} of {len(catalog)} saved items")

        visible_ids = {p["id"] for p in visible}
        if visible and st.session_state.focus_id not in visible_ids:
            st.session_state.focus_id = visible[0]["id"]

        if not visible:
            st.info("No items match this filter.")
        else:
            rows = [visible[i : i + 2] for i in range(0, len(visible), 2)]
            for row in rows:
                cols = st.columns(2, gap="medium")
                for col, p in zip(cols, row):
                    s = stats_by_id[p["id"]]
                    img = IMG_DIR / p.get("image", "")
                    selected = p["id"] == st.session_state.focus_id
                    card_cls = "mvp-card selected" if selected else "mvp-card"
                    in_stock = p.get("in_stock", True)
                    if not in_stock:
                        badge = '<span class="mvp-badge warn">Out of stock</span>'
                    else:
                        bl, warn = badge_label(s)
                        cls = "mvp-badge warn" if warn else "mvp-badge ok"
                        badge = f'<span class="{cls}">Reviews: {bl}</span>'
                    sel = (
                        '<span class="mvp-selected">Selected</span>' if selected else ""
                    )
                    with col:
                        st.markdown(f'<div class="{card_cls}">', unsafe_allow_html=True)
                        if img.exists():
                            st.image(str(img), use_container_width=True)
                        st.markdown(
                            f"**{p['brand']}**{sel}<br>"
                            f"<span class='mvp-meta'>{p.get('short_name') or p['name']}</span><br>"
                            f"<div class='mvp-price'>{p['price']}</div>"
                            f"{badge}",
                            unsafe_allow_html=True,
                        )
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button(
                                "Select",
                                key=f"sel_{p['id']}",
                                type="primary" if selected else "secondary",
                                use_container_width=True,
                            ):
                                st.session_state.focus_id = p["id"]
                                st.rerun()
                        with b2:
                            if st.button(
                                "Bag",
                                key=f"bag_{p['id']}",
                                use_container_width=True,
                                disabled=not in_stock,
                            ):
                                if p["id"] not in st.session_state.bag:
                                    st.session_state.bag.append(p["id"])
                                st.toast(f"Added: {p.get('short_name')}")
                        prompt_key = f"express_prompt_{p['id']}"
                        pin_serves = bool(hub and sku_express_ready(p))
                        show_express = bool(
                            pin_serves
                            and st.session_state.get(prompt_key) != "dismissed"
                        )
                        if pin_serves:
                            st.markdown(
                                "<div class='express-avail'>"
                                "Try it in 30. Swap it today — 30-min delivery "
                                "+ same-day exchange in your area</div>",
                                unsafe_allow_html=True,
                            )
                            st.caption(stock_caption(p))
                        if show_express:
                            if p["id"] in st.session_state.bag_express:
                                st.caption("In bag as Express — try in 30, swap today.")
                            elif st.session_state.get(prompt_key) == "open":
                                usual_focus = st.session_state.get(f"sz_{p['id']}") or ""
                                size_opts = ["", "S", "M", "L", "XL", "UK 6"]
                                sz_key = f"express_sz_{p['id']}"
                                if sz_key not in st.session_state:
                                    st.session_state[sz_key] = (
                                        usual_focus if usual_focus in size_opts else ""
                                    )
                                pick = st.selectbox(
                                    "Size for 30-min hub",
                                    size_opts,
                                    key=sz_key,
                                )
                                if pick:
                                    st.caption(stock_caption(p, pick))
                                if st.button(
                                    "Get it in 30 — swap today if needed",
                                    key=f"express_go_{p['id']}",
                                    use_container_width=True,
                                    disabled=not in_stock,
                                ):
                                    if not pick:
                                        st.warning("Pick a size first.")
                                    elif not size_in_hub(p, pick):
                                        st.warning(
                                            "30-min is on for this pin, but your size "
                                            "isn’t in the hub — standard delivery "
                                            "still applies."
                                        )
                                    else:
                                        if p["id"] not in st.session_state.bag:
                                            st.session_state.bag.append(p["id"])
                                        if p["id"] not in st.session_state.bag_express:
                                            st.session_state.bag_express.append(p["id"])
                                        st.session_state[prompt_key] = "open"
                                        st.toast(
                                            f"Try it in 30, swap today: "
                                            f"{p.get('short_name')} ({pick}) "
                                            f"from {hub.get('hub')}"
                                        )
                                        st.rerun()
                            else:
                                y, n = st.columns(2)
                                with y:
                                    if st.button(
                                        "Yes",
                                        key=f"express_yes_{p['id']}",
                                        use_container_width=True,
                                    ):
                                        st.session_state[prompt_key] = "open"
                                        st.rerun()
                                with n:
                                    if st.button(
                                        "Not now",
                                        key=f"express_no_{p['id']}",
                                        use_container_width=True,
                                    ):
                                        st.session_state[prompt_key] = "dismissed"
                                        st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

    with fit_col:
        focus = next(
            (p for p in catalog if p["id"] == st.session_state.focus_id), catalog[0]
        )
        fs = stats_by_id[focus["id"]]

        st.subheader("Still deciding?")
        st.caption("Answers from this item's reviews — not a guarantee.")
        st.markdown(f"**{focus['brand']}** · {focus.get('short_name')}")
        st.caption(f"Saved {focus['saved_ago']} · intent {focus['intent']}")

        bl, warn = badge_label(fs)
        if warn:
            st.warning(f"Reviews: {bl}")
        else:
            st.info(f"Reviews: {bl}")

        usual = st.selectbox(
            "Your usual size",
            ["", "S", "M", "L", "XL", "UK 6"],
            key=f"sz_{focus['id']}",
        )
        occasion = st.text_input(
            "Occasion",
            placeholder="daytime Rakhi / wedding guest",
            key=f"occ_{focus['id']}",
        )
        question = st.text_area(
            "Ask about this item",
            value="Will the work look cheap in person? Should I size up?",
            height=80,
            key=f"ask_{focus['id']}",
        )
        answer_key = f"mvp_answer_v2_{focus['id']}"
        if st.button("Get answer", type="primary", use_container_width=True):
            q = question.strip()
            with st.spinner("Reading this item's reviews…"):
                st.session_state[answer_key] = resolve_question(
                    focus,
                    q,
                    usual,
                    fs,
                    occasion=occasion.strip(),
                )
                st.session_state.mvp_compare_answer = None

        if st.session_state.get(answer_key):
            _render_shopper_answer(st.session_state[answer_key], focus["id"])

        with st.expander("Reviews used"):
            for r in focus["reviews"]:
                st.write(f"- {r}")

        st.markdown("##### Compare (pick 2–3)")
        cmp_ids = [
            p["id"]
            for p in catalog
            if st.checkbox(p.get("short_name") or p["name"], key=f"cmp_{p['id']}")
        ]
        if st.button("Compare selected", use_container_width=True):
            picked = [p for p in catalog if p["id"] in cmp_ids][:3]
            if len(picked) < 2:
                st.error("Pick at least 2 items.")
            else:
                with st.spinner("Comparing saved items…"):
                    st.session_state.mvp_compare_answer = llm_compare_products(
                        picked,
                        occasion=occasion.strip(),
                        question=question.strip()
                        or "Which of these should I buy?",
                    )
                    st.session_state[answer_key] = None

        if st.session_state.get("mvp_compare_answer"):
            cmp_ans = st.session_state.mvp_compare_answer
            st.markdown("##### Compare")
            _render_shopper_answer(cmp_ans, focus["id"])
            rows = cmp_ans.get("table_rows") or compare_table(
                [p for p in catalog if p["id"] in cmp_ids][:3]
            )
            if rows:
                st.dataframe(rows, hide_index=True, use_container_width=True)

        if st.session_state.bag:
            names = []
            for pid in st.session_state.bag:
                tag = (
                    " · Express: try in 30, swap today"
                    if pid in st.session_state.bag_express
                    else ""
                )
                names.append(f"{pid}{tag}")
            st.caption("Bag: " + ", ".join(names))

        with st.container(border=True):
            st.markdown("<p class='express-kicker'>Express</p>", unsafe_allow_html=True)
            st.markdown("### Try it in 30. Swap it today.")
            st.caption(
                "Doorstep in 30 mins. If the size isn’t right, exchange it the same day."
            )
            with st.form("express_pin_form", border=False):
                pin_col, check_col = st.columns([3.2, 1])
                with pin_col:
                    pin_raw = st.text_input(
                        "Let us know your pincode",
                        placeholder="e.g. 560001",
                        help="Enter a 6-digit pincode, then tap Check.",
                        key="pincode",
                    )
                with check_col:
                    st.markdown(
                        "<div style='height:1.85rem'></div>", unsafe_allow_html=True
                    )
                    st.form_submit_button(
                        "Check", type="primary", use_container_width=True
                    )
            pins = extract_pincodes(pin_raw)
            hub = hub_for_pin(pin_raw, express_hubs)
            if not (pin_raw or "").strip():
                st.caption("Enter your pincode and tap Check.")
            elif not pins:
                st.caption("Enter a full 6-digit pincode (you can add more than one).")
            elif not hub:
                st.caption("30-min isn’t in this area yet — try another pin.")
            else:
                st.markdown(
                    "<div class='express-avail'>"
                    "30-min delivery + same-day exchange is on in your area"
                    "</div>",
                    unsafe_allow_html=True,
                )


