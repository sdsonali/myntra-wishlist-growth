"""
Shared free-LLM chat client. Provider/model/keys from config.py / .env.
"""

from __future__ import annotations

import json
import re
import time

import requests

from shared import config


def model_name() -> str:
    return config.LLM["models"][config.LLM["provider"]]


def extract_json(text: str):
    """Parse a model reply that should be JSON but may carry fences or prose."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\[.*\]|\{.*\})", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON found in model response")
    return json.loads(match.group(1))


def call_huggingface(
    messages: list[dict],
    max_tokens: int | None = None,
    force_json: bool = False,
) -> str:
    key = config._env("HUGGINGFACE_API_KEY")
    if not key:
        raise RuntimeError(
            "HUGGINGFACE_API_KEY missing. Add it in Streamlit Cloud → Settings → Secrets, or in local .env"
        )

    payload = {
        "model": model_name(),
        "messages": messages,
        "temperature": config.LLM["temperature"],
        "max_tokens": max_tokens or config.LLM["max_tokens"],
    }
    if force_json:
        payload["response_format"] = {"type": "json_object"}
    resp = requests.post(
        "https://router.huggingface.co/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"HF {resp.status_code}: {resp.text[:400]}")
    return resp.json()["choices"][0]["message"]["content"]


def call_groq(
    messages: list[dict],
    max_tokens: int | None = None,
    force_json: bool = False,
) -> str:
    key = config._env("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY missing. Add it in Streamlit Cloud → Settings → Secrets, or in local .env"
        )

    payload = {
        "model": model_name(),
        "messages": messages,
        "temperature": config.LLM["temperature"],
        "max_tokens": max_tokens or config.LLM["max_tokens"],
    }
    if force_json:
        payload["response_format"] = {"type": "json_object"}

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Groq {resp.status_code}: {resp.text[:400]}")
    return resp.json()["choices"][0]["message"]["content"]


def call_gemini(
    messages: list[dict],
    max_tokens: int | None = None,
    force_json: bool = False,
) -> str:
    key = config._env("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY missing. Add it in Streamlit Cloud → Settings → Secrets, or in local .env"
        )

    parts = [f"{m['role'].upper()}: {m['content']}" for m in messages]
    prompt = "\n\n".join(parts)
    model = model_name()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={key}"
    )
    generation = {
        "temperature": config.LLM["temperature"],
        "maxOutputTokens": max_tokens or config.LLM["max_tokens"],
    }
    if force_json:
        generation["responseMimeType"] = "application/json"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": generation,
    }
    resp = requests.post(url, json=payload, timeout=120)
    if resp.status_code >= 400:
        raise RuntimeError(f"Gemini {resp.status_code}: {resp.text[:400]}")
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


PROVIDERS = {
    "huggingface": call_huggingface,
    "groq": call_groq,
    "gemini": call_gemini,
}


def call_llm(
    messages: list[dict],
    max_tokens: int | None = None,
    force_json: bool = False,
) -> str:
    provider = config.LLM["provider"]
    fn = PROVIDERS.get(provider)
    if fn is None:
        raise RuntimeError(f"Unknown provider {provider!r}. Use: {list(PROVIDERS)}")

    last_err = None
    for attempt in range(1, config.LLM["max_retries"] + 1):
        try:
            return fn(messages, max_tokens=max_tokens, force_json=force_json)
        except Exception as exc:
            last_err = exc
            wait = config.LLM["retry_sleep_sec"] * attempt
            print(f"  [llm retry {attempt}] {exc} - sleeping {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"LLM failed after retries: {last_err}")
