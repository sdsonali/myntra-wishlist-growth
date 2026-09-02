"""Demo lookup for the optional 30-min wishlist prompt. Not live logistics."""

from __future__ import annotations

import json
import re
from pathlib import Path

from shared import config

_PIN = re.compile(r"\d{6}")


def load_express_hubs() -> list[dict]:
    raw = json.loads(Path(config.MVP_CATALOG).read_text(encoding="utf-8"))
    hubs = raw.get("express_hubs") or []
    if isinstance(hubs, dict):
        return [
            {"city": v.get("city", ""), "hub": v.get("hub", ""), "prefixes": [str(k)[:3]]}
            for k, v in hubs.items()
        ]
    return list(hubs)


def extract_pincodes(value: str | None) -> list[str]:
    seen: list[str] = []
    for pin in _PIN.findall(value or ""):
        if pin not in seen:
            seen.append(pin)
    return seen


def normalize_pincode(value: str | None) -> str:
    pins = extract_pincodes(value)
    if pins:
        return pins[0]
    return re.sub(r"\D", "", value or "")[:6]


def hub_for_pin(pincode: str, hubs: list[dict] | dict) -> dict | None:
    """Return the first hub that serves any 6-digit pin in the input."""
    if isinstance(hubs, dict):
        hubs = [
            {"city": v.get("city", ""), "hub": v.get("hub", ""), "prefixes": [str(k)[:3]]}
            for k, v in hubs.items()
        ]
    pins = extract_pincodes(pincode)
    if not pins:
        one = normalize_pincode(pincode)
        if re.fullmatch(r"\d{6}", one):
            pins = [one]
    for pin in pins:
        for hub in hubs:
            prefixes = [str(p) for p in (hub.get("prefixes") or [])]
            exact = {str(p) for p in (hub.get("pins") or [])}
            if pin in exact or any(pin.startswith(pref) for pref in prefixes if pref):
                return hub
    return None


def sku_express_ready(product: dict) -> bool:
    return bool(product.get("express_eligible") and product.get("in_stock", True))


def size_in_hub(product: dict, size: str) -> bool:
    allowed = product.get("express_sizes") or []
    return bool(size) and size in allowed


def remaining_stock(product: dict, size: str | None = None) -> int:
    stock = product.get("express_stock") or {}
    if not isinstance(stock, dict):
        return int(stock or 0)
    if size:
        return int(stock.get(size, 0) or 0)
    return sum(int(v or 0) for v in stock.values())


def stock_caption(product: dict, size: str | None = None) -> str:
    if size:
        n = remaining_stock(product, size)
        if n <= 0:
            return f"Size {size} is out at the 30-min hub."
        if n == 1:
            return "Only 1 left in your size."
        return f"Only {n} left in size {size}."
    n = remaining_stock(product)
    if n <= 0:
        return "30-min stock just sold out."
    if n == 1:
        return "Only 1 left for 30-min delivery."
    return f"Only {n} left for 30-min delivery."
