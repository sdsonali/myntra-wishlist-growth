"""10-slide landscape PDF, 14pt, no fellow name."""
from pathlib import Path

from fpdf import FPDF

OUT = Path(__file__).resolve().parent.parent / "deck" / "Myntra_Wishlist_Confidence_Gap.pdf"

NAVY = (30, 58, 95)
INK = (34, 34, 34)
MUTED = (74, 74, 74)
AMBER = (184, 92, 56)
BG = (246, 244, 240)
WHITE = (255, 255, 255)


class Deck(FPDF):
    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(False)
        self.set_margins(12, 10, 12)

    def page_bg(self):
        self.set_fill_color(*BG)
        self.rect(0, 0, 297, 210, "F")
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 4, 210, "F")

    def title_bar(self, title, n):
        self.set_xy(12, 8)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*NAVY)
        self.multi_cell(255, 6.5, title)
        y = self.get_y()
        self.set_xy(268, 8)
        self.set_font("Helvetica", "", 14)
        self.set_text_color(*MUTED)
        self.cell(18, 6.5, f"{n}/10", align="R")
        self.set_draw_color(200, 196, 188)
        self.set_line_width(0.4)
        self.line(12, max(y, 22) + 1, 285, max(y, 22) + 1)
        self.set_y(max(y, 22) + 4)

    def body(self, text, bold=False, color=INK, h=6.2):
        self.set_x(12)
        self.set_font("Helvetica", "B" if bold else "", 14)
        self.set_text_color(*color)
        self.multi_cell(273, h, text)

    def gap(self, h=2):
        self.ln(h)


def ascii(s: str) -> str:
    return (
        s.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u00d7", "x")
        .replace("\u2265", ">=")
        .replace("\u2192", "->")
    )


def main():
    pdf = Deck()

    # 1
    pdf.add_page()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, 297, 210, "F")
    pdf.set_fill_color(*AMBER)
    pdf.rect(0, 155, 297, 55, "F")
    pdf.set_xy(18, 55)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*WHITE)
    pdf.multi_cell(260, 8, "Closing the Wishlist Confidence Gap")
    pdf.set_xy(18, 85)
    pdf.set_font("Helvetica", "", 14)
    pdf.multi_cell(260, 7, ascii("Improving Wishlist-to-Purchase Conversion on Myntra - without discounts"))
    pdf.set_xy(18, 170)
    pdf.set_font("Helvetica", "B", 14)
    pdf.multi_cell(260, 7, "Product Manager, Growth Team")

    # 2
    pdf.add_page()
    pdf.page_bg()
    pdf.title_bar(ascii("Re-engagement is not the bottleneck - decision confidence is the lever that moves WPCR"), 2)
    pdf.body(ascii("North star (WPCR): % of users who purchase >=1 wishlisted item within 30 days of adding it."), color=MUTED)
    pdf.gap(2)
    pdf.body("Funnel", bold=True, color=NAVY)
    pdf.body("1. Re-engagement: % of wishlisted items revisited in 30 days. NOT the bottleneck (segment already shops 2-4x/month).")
    pdf.body("2. Decision confidence (PRIMARY LEVER): % of revisited items where fit / quality / comparison / occasion doubt is resolved.")
    pdf.body('3. Cart conversion: % of "resolved" items added to cart.')
    pdf.body("4. Checkout completion: % of those cart items purchased.")
    pdf.gap(2)
    pdf.body("Segmentation lens", bold=True, color=NAVY)
    pdf.body("- Bookmarkers vs genuine intenders")
    pdf.body("- Ethnic/occasion wear (fit-sensitive, higher AOV) vs basics (lower uncertainty, lower AOV)")
    pdf.body("- Price-waiters (OUT OF SCOPE - no monetary levers) vs confidence-blocked (IN SCOPE)")
    pdf.gap(2)
    pdf.body(ascii("Callout: wishlisted demand dies at stage 2. If doubt is not resolved in-app, cart and checkout never get a fair shot."), bold=True)

    # 3
    pdf.add_page()
    pdf.page_bg()
    pdf.title_bar("AI discovery: quality is the loudest complaint; fit is real; price exists but is out of scope", 3)
    pdf.body(ascii("Workflow: Play Store + App Store + YouTube (n=550 tagged reviews) -> LLM cluster -> tag -> mention share. Reviews under-index silent wishlist freeze; primary research fills that gap."), color=MUTED)
    pdf.gap(1)
    pdf.body("Sources -> Cluster -> Tag -> Quantify", bold=True, color=NAVY)
    pdf.body("Quality / authenticity (fabric, finish): 47.8%  IN SCOPE")
    pdf.body("Price change / deal-waiting: 13.9%  OUT OF SCOPE")
    pdf.body("Fit / size uncertainty: 13.0%  IN SCOPE")
    pdf.body("Found an alternative (comparison): 5.2%  IN SCOPE")
    pdf.body("Occasion mismatch: 2.6%  IN SCOPE")
    pdf.body("Also tagged: comparison behaviour 11.8%; external research 10.5% of corpus.")
    pdf.body("Add public Discovery Engine URL in generate_deck.py LINKS before submit.", color=MUTED)

    # 4
    pdf.add_page()
    pdf.page_bg()
    pdf.title_bar(ascii('Pilot (n=10): "Probably" buyers leave the app to decide - no in-app way to resolve doubt'), 4)
    pdf.body(ascii("Google Form, one named item each. Designed segment: 24-30, Tier 1-2, 2-4x/month, 5+ wishlist, dormant 2+ weeks. Named items: 4/10 ethnic/occasion (Rakhi dress, wedding dress, kurta set, kurta)."), color=MUTED)
    pdf.gap(1)
    pdf.body("Main blocker (self-reported)", bold=True, color=NAVY)
    pdf.body("Price/budget 3/10 (out of scope) | Comparison 2/10 | Quality 2/10 | Occasion/style 2/10 | Fit 1/10")
    pdf.body("Confidence cluster = 7/10 once price is set aside. Intent: Probably 6/10 (target zone); Yes definitely 3; Not sure anymore 1.")
    pdf.body("Outside the app: 10/10 did at least one. Compare prices 6/10, visit store 6/10, Instagram 3/10, friends 3/10, YouTube/Google 3/10.")
    pdf.body("What would unstick: 7/10 wanted reviews/photos from similar buyers. Coping: order two and keep the fit; size-chart then exchange; leave until payday.")
    pdf.body(ascii("Caveat: directional, not powered. Screener leaky (Q2/Q3 blank for 7/10); one Rarely shopper included. Pursue 7/10 confidence, not 3/10 price-waiters."), color=MUTED)

    # 5
    pdf.add_page()
    pdf.page_bg()
    pdf.title_bar(ascii("The gap is in-app confidence at reconsideration - not lack of desire to buy"), 5)
    pdf.body(ascii("Segment: 24-30, Tier 1-2, 2-4x/month, impulsive savers, 5+ items sitting 2+ weeks, \"Probably\" intent, ethnic/occasion and fashion-forward (not basics)."))
    pdf.body("Product outcome: Decision Confidence Rate (funnel stage 2) on those SKUs.")
    pdf.body(ascii("Root cause: after impulsive save, no in-app way at revisit to resolve fit, quality/authenticity (fabric, threadwork vs photo), comparison across similar saved options, or occasion-fit. Users leave; most never complete the loop."))
    pdf.body("Workarounds: order extra sizes and return; screenshot to friends; visit stores; hunt reviews off-app; infinite wishlist.")
    pdf.body("User value: less anxiety, fewer return hassles, faster yes/no on high-stakes occasion buys, trust that expensive-looking online is real.")
    pdf.body("Business value: ethnic AOV > basics, so a modest confidence lift moves GMV from demand already saved - no acquisition, no discount. Guardrail: false confidence must not raise returns.")
    pdf.body(ascii("Thinking: WPCR -> stage-2 outcome -> AI discovery (quality+fit; price excluded) -> research (ethnic, Probably, leave-app) -> in-app confidence gap."), bold=True, color=NAVY)

    # 6
    pdf.add_page()
    pdf.page_bg()
    pdf.title_bar("Ethnic-wear decision confidence is the lever that fits the data and the no-discount constraint", 6)
    pdf.body("Largest allowed blocker: pilot 7/10 confidence vs 3/10 price. Discovery: quality 47.8% + fit 13%. Ethnic/forward is less \"safe\" than basics (fit + threadwork/fabric vs photo).")
    pdf.body("No margin giveaway: confidence tools do not require discounts.")
    pdf.body("Instrumentable: maps to Decision Confidence Rate on the WPCR funnel.")
    pdf.body("Data already exists: reviews, return reasons, size charts, past-order fit - no new collection program to ship v1.")
    pdf.body(ascii("Not basics: lower AOV, lower uncertainty, users already \"just order.\" Not price: real but forbidden. Not bookmarking: no purchase intent."))

    # 7
    pdf.add_page()
    pdf.page_bg()
    pdf.title_bar("MVP: an AI layer inside the wishlist that answers fit, quality, and comparison without leaving the app", 7)
    pdf.body("Fit & Confidence Assistant - not a new destination; it sits on the existing wishlist.", color=MUTED)
    pdf.body("1. Confidence score per item from reviews/return reasons, with provenance (never a fake absolute).")
    pdf.body("2. Ask-a-question on the saved SKU: fit, fabric/threadwork vs photo, occasion - replaces Google/Instagram/WhatsApp.")
    pdf.body("3. Personalized fit using past order/fit feedback on similar cuts or brands when available.")
    pdf.body("4. Comparison assist for at most 2-3 similar wishlisted items.")
    pdf.body("Mock: saved kurta set, 3 weeks, intent Probably -> labelled confidence + \"Will this work for a daytime wedding?\" grounded in reviews.")
    pdf.body("Add public MVP (Streamlit Tab 2) URL in LINKS before submit.", color=MUTED)

    # 8
    pdf.add_page()
    pdf.page_bg()
    pdf.title_bar(ascii("WPCR is the north star; we watch whether doubt is resolved - and that we do not inflate returns"), 8)
    pdf.body("North star: WPCR (30-day wishlist-to-purchase). Lagging business result.")
    pdf.body("Leading / adoption: % of in-scope wishlist visits that use the assistant. Unused tool cannot move stage 2.")
    pdf.body(ascii('Leading / resolution: Decision confidence rate = % of uses ending in add-to-cart or "this helped" / explicit decide-not-to-buy. Matches the Probably zone.'))
    pdf.body("Guardrail: return rate must not increase (false confidence).")
    pdf.body("Guardrail: wishlist add rate must not drop (do not punish browsing/saving).")
    pdf.body("Guardrail: fit/quality support contacts expected to fall if in-app answers replace tickets and leave-app workarounds.")

    # 9
    pdf.add_page()
    pdf.page_bg()
    pdf.title_bar("We de-risk cold start, hallucination, trust, hiding, and comparison overload before scale", 9)
    pdf.body("Cold start on thin-review ethnic SKUs: brand size charts + community Q&A; say insufficient evidence; no invented score.")
    pdf.body("Hallucination on fit/quality/threadwork: ground in review/return text; show provenance; caveats not absolute claims.")
    pdf.body("Low trust in AI-only answers: real reviews beside the summary, labelled as synthesis.")
    pdf.body("Low discoverability: embed in the wishlist row at hesitation, not a separate hub.")
    pdf.body("Comparison fatigue: cap at top 2-3 similar saved items.")

    # 10
    pdf.add_page()
    pdf.page_bg()
    pdf.title_bar("Resolve fit, quality, and comparison doubt at hesitation to lift ethnic-wear WPCR without touching price", 10)
    pdf.body("One-line recap", bold=True, color=NAVY)
    pdf.body(ascii('By resolving fit, quality (including online vs real fabric/threadwork), and comparison at hesitation on high-AOV ethnic/fashion-forward wishlist items - validated by discovery (quality+fit) and the n=10 pilot (7/10 confidence, 6/10 Probably, 10/10 leave-app) - we lift decision-confidence rate and thus WPCR, without touching price.'))
    pdf.gap(2)
    pdf.body("Artefacts (must work logged out / incognito)", bold=True, color=NAVY)
    pdf.body("AI Discovery Engine - add public URL")
    pdf.body("Deployed MVP - Fit & Confidence Assistant - add public URL")
    pdf.body("Primary-research Google Form - add viewform URL")
    pdf.gap(3)
    pdf.body("Product Manager, Growth Team  |  no monetary incentives", color=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
