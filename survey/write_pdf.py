"""Stdlib-only landscape PDF (14pt Helvetica). No extra packages."""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "deck" / "Myntra_Wishlist_Confidence_Gap.pdf"

W, H = 842, 595  # landscape A4 points
LEFT, TOP, SIZE, LEAD = 36, 40, 14, 18
MAX_CHARS = 108


def esc(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u00d7", "x")
        .replace("\u2265", ">=")
        .replace("\u2192", "->")
    )


def wrap(text: str) -> list[str]:
    lines = []
    for para in text.split("\n"):
        para = para.strip()
        if not para:
            lines.append("")
            continue
        words = para.split()
        cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if len(t) <= MAX_CHARS:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines


def page_stream(title: str, body: str, n: int, cover: bool = False) -> str:
    cmds = ["q"]
    if cover:
        cmds += ["0.12 0.23 0.37 rg", f"0 0 {W} {H} re f"]
        cmds += ["0.72 0.36 0.22 rg", f"0 0 {W} 110 re f"]
        cmds += ["1 1 1 rg", "BT", f"/F2 {SIZE} Tf", f"1 0 0 1 {LEFT} {H - 180} Tm", f"({esc(title)}) Tj", "ET"]
        y = H - 220
        cmds += ["1 1 1 rg", "BT", f"/F1 {SIZE} Tf"]
        for line in wrap(body):
            cmds += [f"1 0 0 1 {LEFT} {y} Tm", f"({esc(line)}) Tj"]
            y -= LEAD
        cmds += ["ET", "Q"]
        return "\n".join(cmds)

    cmds += ["0.96 0.96 0.94 rg", f"0 0 {W} {H} re f"]
    cmds += ["0.12 0.23 0.37 rg", f"0 0 10 {H} re f"]
    cmds += ["0.12 0.23 0.37 rg", "BT", f"/F2 {SIZE} Tf"]
    y = H - TOP
    for line in wrap(f"{n}/10  {title}"):
        cmds += [f"1 0 0 1 {LEFT} {y} Tm", f"({esc(line)}) Tj"]
        y -= LEAD
    cmds += ["ET"]
    y -= 8
    cmds += ["0.12 0.23 0.37 RG", "2 w", f"{LEFT} {y} m {W - 36} {y} l S"]
    y -= 22
    cmds += ["0.13 0.13 0.13 rg", "BT", f"/F1 {SIZE} Tf"]
    for line in wrap(body):
        if y < 36:
            break
        cmds += [f"1 0 0 1 {LEFT} {y} Tm", f"({esc(line)}) Tj"]
        y -= LEAD
    cmds += ["ET", "Q"]
    return "\n".join(cmds)


SLIDES = [
    (
        True,
        "Closing the Wishlist Confidence Gap",
        "Improving Wishlist-to-Purchase Conversion on Myntra - without discounts\n\nProduct Manager, Growth Team",
    ),
    (
        False,
        "Re-engagement is not the bottleneck - decision confidence is the lever that moves WPCR",
        "North star (WPCR): % of users who purchase >=1 wishlisted item within 30 days of adding it.\n\n"
        "1. Re-engagement: % of wishlisted items revisited in 30 days. NOT the bottleneck (segment already shops 2-4x/month).\n"
        "2. Decision confidence (PRIMARY LEVER): % of revisited items where fit / quality / comparison / occasion doubt is resolved.\n"
        "3. Cart conversion: % of resolved items added to cart.\n"
        "4. Checkout: % of those cart items purchased.\n\n"
        "Segmentation: bookmarkers vs genuine intenders; ethnic/occasion (higher AOV, high uncertainty) vs basics; "
        "price-waiters OUT OF SCOPE vs confidence-blocked IN SCOPE.\n\n"
        "Callout: wishlisted demand dies at stage 2. If doubt is not resolved in-app, cart and checkout never get a fair shot.",
    ),
    (
        False,
        "AI discovery: quality is the loudest complaint; fit is real; price exists but is out of scope",
        "Workflow: Play Store + App Store + YouTube (n=550 tagged reviews) -> LLM cluster -> tag -> mention share. "
        "Reviews under-index silent wishlist freeze; primary research fills that gap.\n\n"
        "Quality / authenticity (fabric, finish): 47.8% IN SCOPE\n"
        "Price change / deal-waiting: 13.9% OUT OF SCOPE\n"
        "Fit / size uncertainty: 13.0% IN SCOPE\n"
        "Found an alternative (comparison): 5.2% IN SCOPE\n"
        "Occasion mismatch: 2.6% IN SCOPE\n"
        "Also tagged: comparison 11.8%; external research 10.5% of corpus.\n\n"
        "Paste the public Discovery Engine URL into the deck LINKS before you submit.",
    ),
    (
        False,
        'Pilot (n=10): "Probably" buyers leave the app to decide - no in-app way to resolve doubt',
        "Google Form, one named item each. Designed segment: 24-30, Tier 1-2, 2-4x/month, 5+ wishlist, dormant 2+ weeks. "
        "Named items: 4/10 ethnic/occasion (Rakhi dress, wedding dress, kurta set, kurta).\n\n"
        "Main blocker: price/budget 3/10 (out of scope); comparison 2; quality 2; occasion/style 2; fit 1. "
        "Confidence cluster = 7/10. Intent: Probably 6/10 (target zone); Yes definitely 3; Not sure 1.\n\n"
        "Outside the app: 10/10 did at least one. Compare prices 6/10, store 6/10, Instagram 3, friends 3, YouTube/Google 3. "
        "7/10 wanted similar-buyer reviews/photos. Coping: order two and keep the fit; size-chart then exchange; leave until payday.\n\n"
        "Caveat: directional, not powered. Screener leaky (Q2/Q3 blank for 7/10); one Rarely shopper included. "
        "Pursue 7/10 confidence, not 3/10 price-waiters.",
    ),
    (
        False,
        "The gap is in-app confidence at reconsideration - not lack of desire to buy",
        "Segment: 24-30, Tier 1-2, 2-4x/month, impulsive savers, 5+ items sitting 2+ weeks, Probably intent, "
        "ethnic/occasion and fashion-forward (not basics).\n"
        "Product outcome: Decision Confidence Rate (funnel stage 2).\n\n"
        "Root cause: after impulsive save, no in-app way at revisit to resolve fit, quality/authenticity "
        "(fabric, threadwork vs photo), comparison, or occasion-fit. Users leave; most never complete the loop.\n\n"
        "Workarounds: extra sizes + returns; friends; stores; off-app reviews; infinite wishlist.\n"
        "User value: less anxiety, fewer returns, faster yes/no on high-stakes occasion buys.\n"
        "Business value: ethnic AOV > basics, so a modest lift moves GMV from demand already saved - no discount, no acquisition. "
        "Guardrail: false confidence must not raise returns.\n\n"
        "Thinking: WPCR -> stage-2 outcome -> AI discovery (quality+fit; price excluded) -> research "
        "(ethnic, Probably, leave-app) -> in-app confidence gap.",
    ),
    (
        False,
        "Ethnic-wear decision confidence is the lever that fits the data and the no-discount constraint",
        "Largest allowed blocker: pilot 7/10 confidence vs 3/10 price. Discovery: quality 47.8% + fit 13%. "
        "Ethnic/forward is less safe than basics (fit + threadwork/fabric vs photo).\n\n"
        "No margin giveaway. Instrumentable stage-2 metric. Data already exists (reviews, return reasons, size charts).\n\n"
        "Not basics (lower AOV, lower uncertainty). Not price (forbidden). Not bookmarking (no purchase intent).",
    ),
    (
        False,
        "MVP: an AI layer inside the wishlist that answers fit, quality, and comparison without leaving the app",
        "Fit & Confidence Assistant sits on the existing wishlist - not a new destination.\n\n"
        "1. Confidence score from reviews/return reasons, with provenance (never a fake absolute).\n"
        "2. Ask-a-question on the saved SKU: fit, fabric/threadwork vs photo, occasion.\n"
        "3. Personalized fit from past order/fit feedback when available.\n"
        "4. Comparison assist for at most 2-3 similar wishlisted items.\n\n"
        "Mock: saved kurta set, 3 weeks, intent Probably -> labelled confidence + occasion question grounded in reviews.\n"
        "Paste the public MVP URL into LINKS before submit.",
    ),
    (
        False,
        "WPCR is the north star; we watch whether doubt is resolved - and that we do not inflate returns",
        "North star: WPCR (30-day wishlist-to-purchase).\n"
        "Leading / adoption: % of in-scope wishlist visits that use the assistant.\n"
        "Leading / resolution: % of uses ending in add-to-cart or this-helped / explicit decide-not-to-buy.\n"
        "Guardrail: return rate must not increase.\n"
        "Guardrail: wishlist add rate must not drop.\n"
        "Guardrail: fit/quality support contacts expected to fall.",
    ),
    (
        False,
        "We de-risk cold start, hallucination, trust, hiding, and comparison overload before scale",
        "Cold start: brand size charts + community Q&A; say insufficient evidence; no invented score.\n"
        "Hallucination: ground in review/return text; provenance; caveats not absolute claims.\n"
        "Low trust: real reviews beside the summary, labelled as synthesis.\n"
        "Discoverability: embed in the wishlist row at hesitation, not a separate hub.\n"
        "Comparison fatigue: cap at top 2-3 similar saved items.",
    ),
    (
        False,
        "Resolve fit, quality, and comparison doubt at hesitation to lift ethnic-wear WPCR without touching price",
        "By resolving fit, quality (including online vs real fabric/threadwork), and comparison at hesitation on "
        "high-AOV ethnic/fashion-forward wishlist items - validated by discovery (quality+fit) and the n=10 pilot "
        "(7/10 confidence, 6/10 Probably, 10/10 leave-app) - we lift decision-confidence rate and thus WPCR, without touching price.\n\n"
        "Artefacts (must work logged out): Discovery Engine URL; Deployed MVP URL; Google Form viewform URL.\n\n"
        "Product Manager, Growth Team | no monetary incentives",
    ),
]


def build():
    n_slides = len(SLIDES)
    streams = [
        page_stream(title, body, i, cover=cover)
        for i, (cover, title, body) in enumerate(SLIDES, 1)
    ]

    # Object ids: 1 catalog, 2 page tree, then a (page, content) pair per slide
    # starting at 3, then the two fonts.
    page_id = lambda i: 3 + i * 2  # noqa: E731
    font_regular = 2 * n_slides + 3
    font_bold = font_regular + 1

    objs = ["<< /Type /Catalog /Pages 2 0 R >>"]
    kids = " ".join(f"{page_id(i)} 0 R" for i in range(n_slides))
    objs.append(f"<< /Type /Pages /Kids [{kids}] /Count {n_slides} >>")

    for i, stream in enumerate(streams):
        objs.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] "
            f"/Contents {page_id(i) + 1} 0 R /Resources << /Font << "
            f"/F1 {font_regular} 0 R /F2 {font_bold} 0 R >> >> >>"
        )
        data = stream.encode("latin-1", "replace")
        objs.append(f"<< /Length {len(data)} >>\nstream\n{stream}\nendstream")

    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1", "replace"))
    xref = len(out)
    out.extend(f"xref\n0 {len(objs)+1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode())
    out.extend(
        f"trailer << /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(bytes(out))
    print(f"Wrote {OUT} ({len(out)} bytes, {n_slides} slides)")


if __name__ == "__main__":
    build()
