# Older numbers-only brief (superseded)

Use [CLAUDE_PPTX_REBUILD.md](CLAUDE_PPTX_REBUILD.md) for the PDF rebuild. Below is the earlier n=6 / Express-only edit list.

Paste this file **and** attach `Myntra_Wishlist_Confidence_Gap_FINAL.pptx`.

**Job:** edit the existing 10-slide deck in place. Keep layout, palette, icons, charts, and visual system. Change copy, numbers, method language, one MVP callout, and hyperlinks so the deck matches the product and research as they exist now.

**Do not** rebuild from a blank deck. **Do not** add an 11th slide. **Do not** put any personal name anywhere. Footer stays `Product Manager, Growth Team`.

---

## 1. Hard constraints (graded)

- Exactly **10 slides**, 16:9.
- **14pt everywhere** that is visible (titles, eyebrows, chips, table/chart labels, footers, page numbers). Hierarchy = weight / colour / uppercase / panels — never font size.
- Slide titles = the argument, not category labels. Keep current titles unless a title is now factually wrong.
- Colourblind-safe: in-scope vs out-of-scope already uses `IN` / `OUT` labels — keep those.
- Linked artefacts must work **logged out / incognito**.
- Speaker notes may hold extra explanation; they are not on-slide and are not 14pt-bound. Current notes are empty except page numbers — you may add short notes.

---

## 2. What changed in the work (why this edit exists)

The deck you are holding is already the right *story*. These product/research changes landed **after** that story was written. Sync the deck. Do not invent a new thesis.

| Area | In the current PPT | True now |
|---|---|---|
| Primary research n | `n = 10`, `10/10`, `7/10`, `3/10`, “screener blank for 7 of 10” | Live discovery overlay is **`n = 6`**. Recast every survey count onto 6 people. Drop the 7-of-10 leaky-screener line. |
| Who we interviewed | Sounds like converters (“item they own”, retrospective “before deciding”) | **Dormant / unsold** wishlist items. The interview item is still sitting on the list. Buying a *different* wishlisted SKU in the last 30 days is context only — not a gate. |
| Google Form URL | Old converter form (wrong ID) | New dormant-item form (URLs below) |
| MVP | Fit & confidence agent only | Same agent **plus** an optional **30-min Express prompt** after pincode check. Demo lookup, not live logistics. Not the hero of the story. |
| Discovery numbers | 424 reviews, quality 44.7%, price 23.8%, fit 20.3%, found alt 7.9%, external 10.8%, other apps 60.9% | **Unchanged — keep.** |
| Discovery sources | Play Store, App Store, YouTube | **Unchanged — keep.** Do not add Reddit. |

Golden thread (do not break):

`WPCR → Stage-3 decision confidence → AI discovery (quality/fit in; price out) → primary research (confidence cluster) → in-app Fit & Confidence Assistant`

30-min Express is a **secondary urgency nudge** (addresses freeze / no-urgency without money). It must not replace confidence as the problem.

---

## 3. Artefact links (replace, then test)

| Slide | Visible label | Correct URL |
|---|---|---|
| 3 | AI Discovery Engine | `https://myntra-wishlist-growth.streamlit.app/` |
| 8 | Deployed MVP | `https://myntra-wishlist-growth.streamlit.app/` (same app, Tab 2) |
| 5 | Primary research form | `https://docs.google.com/forms/d/e/1FAIpQLSdPOnDtw1lQGARNYOo2zOoUMpwlOAcLxIzmPaLz27XYN0TjNQ/viewform` |

**Delete** the current slide-5 hyperlink:

`https://docs.google.com/forms/d/1Cie5So0fzPwsrBEB230FvdVQPjqDDbiQST6mWEK-ukE/viewform`

That is the old converter survey. Do not use `/edit` URLs. Do not use `forms/d/<id>/viewform` without the `/e/` published path.

---

## 4. Numbers to use (do not mix layers)

### Discovery corpus (slides 3–4, 6 “CHANGED” left column)

Keep exactly:

- `n = 424` LLM-curated, LLM-tagged public reviews
- Purchase-blocker mentions = **340**
- Quality doubt **44.7%** · price change **23.8%** (OUT of scope) · fit uncertainty **20.3%** · found alternative **7.9%** · no urgency **2.1%**
- Comparison behaviour **7.5%** · external research in corpus **10.8%**
- Of outside-app mentions: other apps **60.9%** · YouTube **17.4%** · friends/family **10.9%** · Google **8.7%** · Instagram **2.2%**

Two layers, never merged. Caption language to keep:

> Public reviews mention leaving the app in 10.8%; survey respondents (n=6) almost all did. These are two evidence layers, not one combined rate.

### Primary research (slides 5–6) — recast from n=10 to n=6

Use these counts. They are directional, not powered.

| Finding | Old (n=10) | New (n=6) |
|---|---|---|
| Left the app before deciding | 10/10 | **6/6** |
| Main blocker in the confidence cluster (comparison + quality + occasion/style + fit) | 7/10 | **6/6** |
| Price as *main* blocker | 3/10 | **0/6** (price still #2 in the *corpus*; scoped out) |
| Similar-buyer reviews/photos named as unstick / info needed | 7/10 | **4/6** named similar-buyer reviews or photos; another **1/6** wanted clearer fit/sizing |
| Assistant would have helped decide faster | (implied) | **4/6 Yes**, **2/6 Maybe**, **0 No** |
| Intent when saved | 6/10 Probably | **4/6 Probably**, **2/6 Yes, definitely** |

Honesty (replace the leaky-screener caveat):

- n=6 is directional, not statistically powered.
- Public reviews under-index the silent freeze (nobody reviews an item they never bought).
- Quality-doubt bucket is broad (keyword fallback on null tags can absorb some service/delivery noise). **Keep this.**
- Do **not** quote reviews verbatim. Paraphrase patterns only.
- Do **not** use MVP catalog product names as discovery evidence.

---

## 5. Slide-by-slide edits

Current on-slide copy is quoted so you can find the boxes. Change only what is listed. Keep everything else.

### Slide 1 — leave as-is

Title/framing, three chips (FOCUS / LEVER / CONSTRAINT), and “no monetary incentives” stay.

### Slide 2 — leave as-is except optional one-word tighten

Funnel and IN/OUT chips are correct. Do not add Express here. Confidence resolution remains the target stage.

### Slide 3 — leave pipeline as-is; keep the anti-hallucination line

Offline 1–4 and live Router / Retrieval / Writer are accurate. Keep:

> any figure the writer cites that the counts don’t support is discarded before it reaches a slide.

Confirm the Streamlit hyperlink (table in §3).

### Slide 4 — leave numbers; only fix if a leftover `n=10` exists

Chart and patterns stay. Keep both caveats (under-index freeze; broad quality bucket).

### Slide 5 — **rewrite method + n**

**Title (keep):** `WHO WE TALKED TO AND WHY`

**Replace subtitle**

- From: `A recruited pilot of 10 monthly+ shoppers with dormant wishlist items`
- To: `A recruited pilot of 6 monthly+ shoppers with unsold wishlist items`

**TARGET SEGMENT — keep** the 24–30 / Tier 1–2 / monthly+ / 5+ items / dormant 2+ weeks / “Probably” / ethnic-occasion-fashion-forward list.

**METHOD — replace the whole panel**

- Recruited pilot, **n = 6**, screened to the segment above.
- Each person named **one saved item they have not purchased** (still on the wishlist).
- Asked: why they saved it, whether they still intend to buy **this** item, the main thing stopping them **now**, what would make them buy in the **next 30 days**, information still needed, alternatives, outside-app behaviour, how they cope today, and whether an in-app assistant would help them decide faster.
- “Bought a different wishlisted item in the last 30 days?” is context only — Yes and No both continue.
- Read directionally, not statistically: **n = 6**.

**Delete:** “screener left shopping frequency and wishlist size blank for 7 of 10 respondents.”

**Link label:** `Primary research form` → new viewform URL.

### Slide 6 — **rewrite counts; keep the pivot**

**Title (keep):** `WHAT PRIMARY RESEARCH CONFIRMED, AND CHANGED`

**CONFIRMED — replace**

- 6/6 left the app to do something before deciding — the confidence gap is real, not theoretical.
- 6/6 main blockers sit in the confidence cluster: comparison, quality, occasion, fit. Price was not the main blocker for anyone in this pilot.
- 4/6 named similar-buyer reviews/photos as what would unstick them; 4/6 said an in-app assistant would have helped them decide faster — that is what the MVP delivers.

**CHANGED — replace the n=10 lines only**

Keep the corpus side:

> Discovery corpus (n=424): price is the #2 blocker overall at 23.8%.

Replace intender side:

> These intenders (n=6): price is 0/6 as the main blocker; the confidence cluster is 6/6.

Keep the scoping sentence (target the confidence cluster, not price waiters / no monetary lever).

**Footer caption:** change `survey respondents almost universally did` to mention **n=6**. Do not merge 10.8% with 100%.

### Slide 7 — leave structure; tiny method alignment

Segment / outcome / root cause / workarounds / user / business value stay. Optional: in SEGMENT, say “unsold saved items” instead of anything that sounds like they already bought.

Do **not** put Express on this slide.

### Slide 8 — keep the agent as hero; add a small Express callout

**Title (keep):** `THE MVP: HOW IT SOLVES THIS`  
**Subtitle (keep):** `An agent reads this item’s reviews and gives a verdict, inside the wishlist`

Keep the three-step flow and the worked example (Size up, then buy / runs small). Keep DELIBERATELY NOT BUILT (no numeric score, no personal order-history fit, no support chatbot, thin evidence → “Too few reviews”, never guess).

**Verdict vocabulary (must match the product):** exactly one of  
`Go for it` · `Size up, then buy` · `Hesitate` · `Skip` · `Need more info`

**Add one compact panel** (do not blow up the slide). Suggested copy:

> **Also in the wishlist (optional):** after the shopper checks a pincode, eligible items can prompt “Want delivery in 30 mins?” Size must be in the hub or it stays on standard delivery. **Demo pin→hub lookup, not live logistics.** No discount. Purpose: convert freeze into a time-bound yes without money.

If space is tight: one line under DELIBERATELY NOT BUILT is enough. Do not retitle the slide around Express.

**Link:** Deployed MVP → Streamlit URL.

### Slide 9 — optional one-line leading indicator

Keep WPCR, engagement, resolution, and the three guardrails.

You may add under LEADING (only if it fits without shrinking type below 14pt):

> Express attach rate among eligible pins — shows whether the 30-min prompt adds urgency without becoming the product.

If it does not fit at 14pt, skip it. Guardrails stay as written.

### Slide 10 — add one risk; keep SHIPPED vs PLANNED

Keep the four shipped risks + discoverability PLANNED + standing no-discount constraint.

**Add:**

| Risk | Mitigation | Status |
|---|---|---|
| 30-min prompt read as live dark-store ops | Copy and data are a demo hub/prefix table; ineligible pin or missing size falls back to standard delivery | SHIPPED (demo) |

Do not claim live 30-min coverage.

---

## 6. What you must not do

- Do not change 424 / 44.7 / 23.8 / 20.3 / 10.8.
- Do not put Reddit on slide 3.
- Do not restore n=10, 10/10, 7/10, 3/10, or the leaky 7-of-10 screener.
- Do not describe the form as “what finally made you purchase” / converters.
- Do not add discounts, coupons, cashback, or a numeric confidence %.
- Do not use MVP product names (Libas, Sassafras, etc.) on discovery slides.
- Do not quote reviews.
- Do not redesign the palette or invent new illustration styles.
- Do not put the author’s name anywhere.

---

## 7. Design system (do not restyle)

Carry forward from the file: navy titles, amber eyebrows, cool/warm panels, IN/OUT chips, footer `Product Manager, Growth Team` + slide number. One system across all 10 slides.

---

## 8. Deliverable

1. Edited `.pptx` (same 10 slides, 16:9).
2. Short self-audit:
   - slide count = 10
   - no personal name
   - every visible run is 14pt
   - n=6 everywhere the survey is cited
   - form link is the `/e/.../viewform` URL above
   - Streamlit link on slides 3 and 8
   - Express is present on slide 8 (and optionally 9–10) but not the title story
   - titles-only read still tells: confidence gap → discovery → research pivot → in-app assistant → metrics → risks

If a box overflows at 14pt, cut words. Never shrink the font.
