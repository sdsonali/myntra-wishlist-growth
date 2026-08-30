"""Fit & Confidence Assistant — an LLM agent that decides from one item's reviews.

Agent flow per question:
    route   -> the model names what the shopper is stuck on and picks the review
               lines that actually speak to it
    select  -> those lines (and only those) become the writer's evidence
    write   -> the model returns a verdict + a recommendation

Two things are deliberately not model-driven:

* ``analyze`` / ``badge_label`` feed the wishlist card badges, which render for
  every saved item on page load. Calling the model once per card would make the
  page slow and burn quota on a hint, not an answer.
* ``evidence_fallback`` is what the UI shows when the API is unreachable. It
  surfaces the closest reviews and says the model is down; it never invents a
  verdict, because a wrong recommendation is worse than no recommendation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from shared import config
from shared.llm_client import call_llm, extract_json

CATALOG_PATH = config.MVP_CATALOG

VERDICTS = (
    "Go for it",
    "Size up, then buy",
    "Hesitate",
    "Skip",
    "Need more info",
)

# Badge-only signals. See module docstring for why these stay regex.
_FIT_TRUE = re.compile(r"true to size|usual size|size chart match|usual m fit|m fit", re.I)
_FIT_SMALL = re.compile(r"runs?\s+(slightly\s+)?small|size up|snug|tight", re.I)
_FIT_LARGE = re.compile(r"runs?\s+(slightly\s+)?large|too loose|roomy", re.I)
_QUALITY_POS = re.compile(
    r"not cheap|looks expensive|neat|premium|honest for|held after|richer in person", re.I
)
_QUALITY_NEG = re.compile(
    r"cheap|sparse|shed|photo exaggeration|photo vs real|synthetic|average|dull", re.I
)

ROUTER_SYSTEM = (
    "You triage a shopper's question about one saved fashion item.\n"
    "Reviews are numbered. Decide what the shopper is stuck on, then pick the review "
    "numbers that genuinely help answer THAT question — ignore reviews about other "
    "topics even if they are interesting.\n"
    "Pick 3 to 6 reviews when that many are relevant, and include reviews on BOTH "
    "sides where opinion splits. Never hand back only the flattering ones.\n"
    'Return ONLY JSON: {"intent": "...", "need": "...", "evidence": [1, 4, 7]}\n'
    "intent: two or three words naming the doubt (e.g. fabric quality, sizing, "
    "occasion fit, return risk, choosing between items).\n"
    "need: one clause restating what they want to know.\n"
    "evidence: review numbers, most useful first. Empty list if none apply."
)

WRITER_SYSTEM = (
    "You help a shopper decide whether to buy one saved fashion item.\n"
    "Answer ONLY the question asked, using ONLY the reviews given to you. Never "
    "bring up size, fit, or occasion unless the question raises them.\n"
    "Address the shopper as 'you'. Never write in the first person — you are "
    "advising them, not narrating your own purchase.\n"
    "Read every review you are given before deciding. Where reviewers disagree, say "
    "so and lean cautious; do not ignore a warning because other reviews are "
    "positive. Quote a reviewer's advice in the direction they actually meant it.\n"
    'Return ONLY JSON: {"verdict": "...", "answer": "...", "proof": ["...", "..."]}\n'
    f"verdict: exactly one of {', '.join(VERDICTS)}.\n"
    'Sizing direction matters. Use "Size up, then buy" ONLY when reviewers say the '
    "item runs small, snug or tight. If reviewers say it runs large, roomy or loose, "
    "sizing up is wrong — tell them to take their usual size or go down, and use "
    '"Go for it" or "Hesitate". If reviewers say their usual size fit, that is '
    '"Go for it".\n'
    "answer: 2-3 sentences. The opening must agree with your verdict — "
    '"Go for it" opens "You can buy this"; "Hesitate" opens "Hold off"; "Skip" opens '
    '"Skip this one"; "Size up, then buy" opens "Order one size up"; "Need more info" '
    'opens "There is not enough here". Then say what to do and why, in plain shopper '
    "language. Reason from what reviewers describe — do not list or recap reviews. "
    "Write with commitment: no 'consider', no 'you might want to', no 'you may wish'.\n"
    "proof: 2 short lines from the reviews that back your call.\n"
    "If the reviews do not answer the question, the verdict must be "
    '"Need more info" — say what is missing instead of guessing.'
)

# The router occasionally returns a single line; one misread review should not
# decide a purchase, so top up to this many before the writer sees the evidence.
MIN_EVIDENCE = 4


def load_catalog() -> list[dict]:
    raw = json.loads(Path(CATALOG_PATH).read_text(encoding="utf-8"))
    return raw["products"]


def analyze(product: dict) -> dict:
    """Cheap review signals for the wishlist card badge (no API call)."""
    reviews = product.get("reviews") or []
    return {
        "n": len(reviews),
        "true_n": sum(1 for r in reviews if _FIT_TRUE.search(r)),
        "small_n": sum(1 for r in reviews if _FIT_SMALL.search(r)),
        "large_n": sum(1 for r in reviews if _FIT_LARGE.search(r)),
        "qpos": sum(1 for r in reviews if _QUALITY_POS.search(r)),
        "qneg": sum(1 for r in reviews if _QUALITY_NEG.search(r)),
    }


def badge_label(stats: dict) -> tuple[str, bool]:
    """Short card hint. Returns (text, is_warning)."""
    if stats["n"] < 6:
        return "Too few reviews", True
    if stats["small_n"] >= 2 and stats["small_n"] > stats["true_n"]:
        return "Several say size up", False
    if stats["small_n"] and stats["large_n"]:
        return "Mixed on fit", False
    if stats["qneg"] >= 2 and stats["qneg"] > stats["qpos"]:
        return "Some quality cautions", False
    if stats["true_n"] >= 2:
        return "Mostly true to size", False
    if stats["qpos"] >= 2 and not stats["qneg"]:
        return "Quality reads well", False
    return "Reviews are mixed", False


def _extract_json(raw: str) -> dict[str, Any]:
    data = extract_json(raw)
    if not isinstance(data, dict):
        raise ValueError("model returned JSON but not an object")
    return data


def _numbered(reviews: list[str]) -> str:
    return "\n".join(f"{i}. {r}" for i, r in enumerate(reviews, 1))


def _closest_reviews(question: str, reviews: list[str], limit: int = 3) -> list[str]:
    """Word-overlap retrieval. Used only when the model is unreachable."""
    words = {w for w in re.findall(r"[a-z]{4,}", (question or "").lower())}
    if not words:
        return reviews[:limit]
    ranked = sorted(
        reviews,
        key=lambda r: -sum(1 for w in words if w in r.lower()),
    )
    return ranked[:limit]


def _shorten(line: str, cap: int = 130) -> str:
    line = line.strip()
    return line if len(line) <= cap else line[: cap - 3] + "..."


def _use_json_mode() -> bool:
    return config.LLM["provider"] in ("groq", "huggingface")


def route_question(question: str, reviews: list[str]) -> dict[str, Any]:
    """Agent step 1 — the model names the doubt and picks its own evidence."""
    messages = [
        {"role": "system", "content": ROUTER_SYSTEM},
        {
            "role": "user",
            "content": f"Question: {question}\n\nReviews:\n{_numbered(reviews)}",
        },
    ]
    data = _extract_json(call_llm(messages, max_tokens=300, force_json=_use_json_mode()))

    picked: list[int] = []
    for value in data.get("evidence") or []:
        try:
            idx = int(value)
        except (TypeError, ValueError):
            continue
        if 1 <= idx <= len(reviews) and idx not in picked:
            picked.append(idx)

    return {
        "intent": str(data.get("intent") or "").strip() or "their question",
        "need": str(data.get("need") or "").strip(),
        "evidence": picked[:6],
    }


def write_answer(
    product: dict,
    question: str,
    evidence: list[str],
    *,
    intent: str = "",
    need: str = "",
    usual_size: str = "",
    occasion: str = "",
    total_reviews: int | None = None,
) -> dict[str, Any]:
    """Agent step 3 — verdict plus recommendation from the selected evidence."""
    context = [f"Question: {question}"]
    if intent:
        context.append(f"Doubt identified: {intent}")
    if need:
        context.append(f"What they want to know: {need}")
    if usual_size:
        context.append(f"Their usual size (mention only if the question is about fit): {usual_size}")
    if occasion.strip():
        context.append(
            f"Their occasion (mention only if the question is about the occasion): {occasion.strip()}"
        )
    shown = len(evidence)
    total = total_reviews if total_reviews is not None else shown
    context.append(
        f"You are seeing {shown} of this item's {total} reviews. If you cite a count, "
        f"count only the {shown} shown and say so — never invent a total."
    )

    messages = [
        {"role": "system", "content": WRITER_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Item: {product['name']} ({product['brand']}, {product['price']})\n"
                + "\n".join(context)
                + "\n\nReviews:\n"
                + (_numbered(evidence) or "(none relevant)")
            ),
        },
    ]
    data = _extract_json(call_llm(messages, max_tokens=600, force_json=_use_json_mode()))

    answer = str(data.get("answer") or "").strip()
    if not answer:
        raise ValueError("model returned no recommendation")

    verdict = str(data.get("verdict") or "").strip()
    if verdict not in VERDICTS:
        opening = answer.lower()[:48]
        verdict = next(
            (v for v in VERDICTS if v.lower() in verdict.lower() or v.lower() in opening),
            "Need more info",
        )

    proof = data.get("proof") or data.get("proof_bullets") or []
    if not isinstance(proof, list):
        proof = [proof]
    bullets = [_shorten(str(p)) for p in proof if str(p).strip()][:3]
    if not bullets:
        bullets = [_shorten(r) for r in evidence[:2]]

    return {
        "verdict": verdict,
        "answer": answer,
        "proof_bullets": bullets,
        "intent": intent,
        "source": "llm",
    }


def evidence_fallback(
    product: dict,
    question: str,
    reason: str = "",
) -> dict[str, Any]:
    """Model unreachable — show the closest reviews, do not fake a verdict."""
    closest = _closest_reviews(question, product.get("reviews") or [])
    return {
        "verdict": "Couldn't reach the assistant",
        "answer": (
            "The assistant is unavailable right now, so this is not a recommendation. "
            "These are the reviews closest to your question — retry in a moment for a verdict."
        ),
        "proof_bullets": [_shorten(r) for r in closest],
        "intent": "",
        "source": "offline",
        "error": reason,
    }


def resolve_question(
    product: dict,
    question: str,
    usual_size: str,
    stats: dict | None = None,
    occasion: str = "",
) -> dict[str, Any]:
    """Run the agent: route, select evidence, write the recommendation.

    ``stats`` is accepted for call-site compatibility; the model reasons from the
    reviews themselves rather than from precomputed counts.
    """
    reviews = product.get("reviews") or []
    if not reviews:
        return evidence_fallback(product, question, "item has no reviews")

    steps: list[str] = []
    plan: dict[str, Any] = {"intent": "", "need": "", "evidence": []}
    try:
        plan = route_question(question, reviews)
        steps.append(
            f"Router read the question as “{plan['intent']}” and picked "
            f"{len(plan['evidence'])} of {len(reviews)} reviews."
        )
    except Exception as exc:
        steps.append(f"Router unavailable ({type(exc).__name__}); writer saw all reviews.")

    evidence = [reviews[i - 1] for i in plan["evidence"]] or list(reviews)
    if len(evidence) < MIN_EVIDENCE:
        for extra in _closest_reviews(question, reviews, limit=MIN_EVIDENCE):
            if extra not in evidence:
                evidence.append(extra)
            if len(evidence) >= MIN_EVIDENCE:
                break
        steps.append(
            f"Router returned too little to judge on, so the writer saw "
            f"{len(evidence)} reviews."
        )

    try:
        answer = write_answer(
            product,
            question,
            evidence,
            intent=plan["intent"],
            need=plan["need"],
            usual_size=usual_size,
            occasion=occasion,
            total_reviews=len(reviews),
        )
        steps.append(f"Writer returned “{answer['verdict']}”.")
        answer["steps"] = steps
        answer["evidence_used"] = len(evidence)
        return answer
    except Exception as exc:
        steps.append(f"Writer unavailable ({type(exc).__name__}).")
        answer = evidence_fallback(product, question, str(exc))
        answer["steps"] = steps
        answer["evidence_used"] = len(evidence)
        return answer


def llm_compare_products(
    products: list[dict],
    occasion: str,
    question: str = "",
) -> dict[str, Any]:
    """Compare 2-3 saved items and name one to buy."""
    picked = products[:3]
    if len(picked) < 2:
        raise ValueError("Need at least 2 products to compare")

    blocks = []
    for p in picked:
        blocks.append(
            f"{p.get('short_name') or p['name']} — {p['brand']}, {p['price']}\n"
            + _numbered(p.get("reviews") or [])
        )

    ask = question.strip() or "Which of these should I buy?"
    if occasion.strip():
        ask += f" Occasion: {occasion.strip()}"

    messages = [
        {
            "role": "system",
            "content": (
                "You compare saved wishlist items for a shopper and name ONE to buy.\n"
                'Return ONLY JSON: {"verdict": "...", "answer": "...", "proof": ["...", "..."]}\n'
                "verdict: the name of the item you recommend, or "
                '"Need more info" if the reviews cannot separate them.\n'
                "answer: 2-3 sentences saying which to buy and the trade-off you are "
                "making. Be direct; no hedging.\n"
                "proof: 2 short review lines that justify the pick."
            ),
        },
        {"role": "user", "content": f"Question: {ask}\n\n" + "\n\n".join(blocks)},
    ]

    table_rows = compare_table(picked)
    try:
        data = _extract_json(call_llm(messages, max_tokens=650, force_json=_use_json_mode()))
        answer = str(data.get("answer") or "").strip()
        if not answer:
            raise ValueError("model returned no comparison")
        proof = data.get("proof") or []
        if not isinstance(proof, list):
            proof = [proof]
        result = {
            "verdict": str(data.get("verdict") or "Recommendation").strip(),
            "answer": answer,
            "proof_bullets": [_shorten(str(p)) for p in proof if str(p).strip()][:3],
            "source": "llm",
        }
    except Exception as exc:
        result = {
            "verdict": "Couldn't reach the assistant",
            "answer": (
                "The assistant is unavailable, so this is not a recommendation. "
                "Compare the review summaries below and retry in a moment."
            ),
            "proof_bullets": [],
            "source": "offline",
            "error": str(exc),
        }

    result["table_rows"] = table_rows
    return result


def compare_table(products: list[dict]) -> list[dict]:
    """Deterministic side-by-side summary shown under the recommendation."""
    rows = []
    for p in products[:3]:
        s = analyze(p)
        rows.append(
            {
                "Item": p.get("short_name") or p["name"],
                "Price": p["price"],
                "Reviews": s["n"],
                "Reviews say": badge_label(s)[0],
            }
        )
    return rows
