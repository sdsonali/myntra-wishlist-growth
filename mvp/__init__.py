"""MVP Fit & Confidence Assistant."""

from mvp.assistant import (
    analyze,
    badge_label,
    compare_table,
    evidence_fallback,
    llm_compare_products,
    load_catalog,
    resolve_question,
    route_question,
    write_answer,
)
from mvp.express import (
    hub_for_pin,
    load_express_hubs,
    normalize_pincode,
    remaining_stock,
    size_in_hub,
    sku_express_ready,
    stock_caption,
)

__all__ = [
    "analyze",
    "badge_label",
    "compare_table",
    "evidence_fallback",
    "hub_for_pin",
    "llm_compare_products",
    "load_catalog",
    "load_express_hubs",
    "normalize_pincode",
    "remaining_stock",
    "stock_caption",
    "resolve_question",
    "route_question",
    "size_in_hub",
    "sku_express_ready",
    "write_answer",
]
