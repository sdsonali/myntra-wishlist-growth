# Claude brief — rebuild `Myntra_Wishlist_Confidence_Gap_FINAL.pptx` (PDF-only)

Paste **this entire file** into Claude. Attach:

1. `Myntra_Wishlist_Confidence_Gap_FINAL.pptx` (starting visual system)
2. Screenshots listed in §8 (if you have them)
3. Optional: SkillCycle reference PDF — [NextLeap copy](https://assets.nextleap.app/submissions/NL_SKILLCYCLE-ba717086-5b0c-41f0-8eb9-d15709c840cb.pdf) (same deck as the Drive file `NL_SKILLCYCLE.pdf`)

**Job:** recreate a **10-slide, 16:9** submission deck. A grader will receive **PDF only** — no speaker notes, no you talking. Every slide must be self-explanatory.

**Additive rule:** do **not** erase the current argument. Keep claims, funnel, blocker chart, golden thread, honesty caveats, verdict vocabulary, and SHIPPED vs PLANNED. **Add** the blocks specified per slide (personas, click-path, competitive table, metric definitions, risk *steps*).

**Do not** invent an 11th slide. **Do not** put any personal / Fellow name. Footer: `Product Manager, Growth Team` + slide number.

---

## 0. Hard constraints

- Exactly **10 slides**.
- **14pt everywhere visible** (titles, eyebrows, chips, table/chart labels, footers, page numbers, screenshot captions). Hierarchy = weight / colour / UPPERCASE / panels — **never font size**. If it overflows: two columns, crop screenshots, cut repeated jargon. **Never shrink below 14pt.**
- Slide titles = the key message, not “Findings” / “MVP”.
- Colourblind-safe: IN/OUT text on scoped bars; never red vs green as the only cue.
- PDF-only: **no speaker notes** as a hiding place for meaning.
- Linked artefacts must work **logged out**. Use the URLs in §1. Delete the old converter form.

**Design system (keep from the current file):** navy titles, amber eyebrows, cool/warm panels, IN/OUT chips. One system across all 10. Study SkillCycle for *information density* (persona cards, competitor table, Risk | Why | Mitigation) — not for a new colour palette.

---

## 1. Artefact links (hyperlink like SkillCycle “Source / Resources”)

| Label | URL | Put on slides |
|---|---|---|
| Live app (Tab 1 Discovery + Tab 2 MVP) | `https://myntra-wishlist-growth.streamlit.app/` | 1, 3, 4, 8 |
| Interview form (view, not edit) | `https://docs.google.com/forms/d/e/1FAIpQLSdPOnDtw1lQGARNYOo2zOoUMpwlOAcLxIzmPaLz27XYN0TjNQ/viewform` | 1, 5 |

**Delete** if still present: `https://docs.google.com/forms/d/1Cie5So0fzPwsrBEB230FvdVQPjqDDbiQST6mWEK-ukE/viewform`

Do not use `/edit` URLs.

---

## 2. Numbers (do not mix layers, do not invent lift %)

### Discovery corpus (gold)

- **424** LLM-curated, LLM-tagged public reviews
- Sources: Play Store **154** · YouTube **212** · App Store **58** (no Reddit)
- Purchase-blocker mentions = **340**
- Blockers (% of those 340): quality doubt **44.7%** · price change **23.8%** (**OUT** of scope) · fit **20.3%** · found alternative **7.9%** · no urgency **2.1%**
- Comparison behaviour **7.5%** (32 rows)
- External research **10.8%** (46 rows)
- Of outside-app mentions: other apps **60.9%** · YouTube **17.4%** · friends/family **10.9%** · Google **8.7%** · Instagram **2.2%**
- Wishlist reasons (% of 122 reason mentions): liked look **47.5%** · compare later **32.8%** · occasion **8.2%** · style confirmation **7.4%** · just browsing **1.6%**

**How they are computed (put a short version on slide 3):**

- **424** = count of rows in the gold tagged JSON after scrape → LLM curate → tag.
- **Blocker %** = count of that label ÷ **340** blocker mentions (not ÷ 424 reviews).
- **7.5%** = share of tagged rows with comparison behaviour true.
- **10.8%** = share of tagged rows that mention leaving the app.

### Survey overlay (second layer — never average with 10.8%)

- **n = 6** (directional). Caption: public reviews mention leaving the app in 10.8%; survey respondents (n=6) almost all did. Two layers, not one combined rate.

Recast old n=10 copy:

| | Old | Now |
|---|---|---|
| Left the app | 10/10 | **6/6** |
| Main blocker in confidence cluster (quality + fit + compare + occasion) | 7/10 | **6/6** |
| Price as *main* blocker | 3/10 | **0/6** |
| Similar-buyer reviews/photos as unstick | 7/10 | **4/6** (+ 1/6 wanted clearer fit) |
| Assistant would help decide faster | — | **4/6 Yes**, **2/6 Maybe** |

### MVP product (Tab 2)

Verdicts (exact): `Go for it` · `Size up, then buy` · `Hesitate` · `Skip` · `Need more info`

Not built: numeric confidence %, personal fit from order history, support chatbot. Thin evidence → `Too few reviews` / `Need more info`, never guess.

Express: demo pin→hub prefixes in catalog; **not live logistics**; no discount.

---

## 3. Golden thread (must still read from titles alone)

WPCR → stage-3 decision confidence (not re-engagement, not price) → discovery ranks quality/fit in and price out → research confirms confidence for intenders → in-wishlist assistant (+ compare, + demo 30-min) → metrics → risks with steps.

---

## 4. Slide-by-slide specification

### Slide 1 — Title + framing

**Keep:** eyebrow `PRODUCT STRATEGY — MYNTRA GROWTH`; title `CLOSING THE WISHLIST CONFIDENCE GAP`; body about improving wishlist-to-purchase by resolving in-app decision doubt without discounts/coupons/cashback; chips FOCUS / LEVER / CONSTRAINT.

**Add so-what line (14pt):**  
`For 24–30 shoppers with at least one unsold saved item, resolve fit / quality / compare doubt on the wishlist — so WPCR moves without discounts.`

**Add resource hyperlinks** (SkillCycle “Source” style): Live app · Interview form.

---

### Slide 2 — Metric + where the MVP moves it

**Keep:** title about saved demand dying at **decision confidence**, not re-engagement; WPCR definition (share of users who purchase ≥1 wishlisted item within **30 days of adding it**); funnel: Add to wishlist → Reconsideration trigger → **Confidence resolution (TARGET)** → Decision → Checkout; IN (confidence-blocked intenders, ethnic/occasion/fashion-forward) vs OUT (price-only waiters, rare shoppers).

**Add table — highest-potential areas (from discovery) × how the MVP changes WPCR.** No fake “+8%”. Mechanism only:

| Opportunity (corpus) | MVP surface | How it can move WPCR |
|---|---|---|
| Quality doubt 44.7% | Still deciding — this SKU’s reviews | Converts “photo vs real” freeze into yes/no without leaving the app |
| Fit 20.3% | Size + verdict (`Size up, then buy` / `Need more info`) | Cuts “order two sizes and wait” delay |
| Found alt 7.9% + leave-app 10.8% | Compare 2–3 + in-app answer | Closes the loop on Myntra instead of another app |
| Price 23.8% | **Out of scope** | No monetary lever in the brief |
| No urgency 2.1% | Express 30-min **demo** | Optional urgency nudge; not the hero; not live logistics |

---

### Slide 3 — How the discovery engine works **and** what it found

This slide absorbs **old slides 3 + 4**. Two columns.

**Left — how to use it (clicks):**

1. Open [live app](https://myntra-wishlist-growth.streamlit.app/) → tab **Discovery Engine**.
2. Click a **theme shortcut** or type a PM question (e.g. why wishlist items stall).
3. Click **Get grounded answer**.
4. Read numbered findings + “Validate in interviews”. Writer figures that don’t match the count block are **discarded**.
5. Right rail **Opportunity comparison**: headline, 424 / 7.5% / 10.8%, source-mix bars, blocker bars, reason bars.

**Offline pipeline (keep):** Scrape Play + App Store + YouTube → LLM curate gold → tag 4 dimensions (reason, blocker, comparison, outside research) → aggregate opportunity table.

**Live agent (keep):** Router (real tag vocabulary) → Retrieval (matched signals, IDF, source spread) → Writer + anti-hallucination.

**How 424 / 7.5% / 10.8% / blocker % are made:** use §2. Identify, **quantify**, **compare** opportunities that could move **WPCR** (stage 3). Price ranks #2 but is OUT.

**Right — findings (keep graph + copy):**

- Title-level finding: quality 44.7%; fit 20.3%; price larger but off-limits.
- Horizontal bars with % and **IN/OUT** on each bar.
- Patterns (paraphrase, never quote reviews): quality = fabric/finish cheaper than listing or authenticity doubt; fit = don’t trust size chart without a planned exchange; found alternative = check same item on another app (other apps 60.9% of outside-app mentions).
- Caveats: reviews under-index the silent freeze; quality bucket is broad (keyword fallback on null tags).

Screenshot of Tab 1 if attached. Hyperlink the app.

---

### Slide 4 — MVP product tour (make it interesting to read)

Old findings left this slot. **This is the shopper UI** (same URL, Tab **Fit & Confidence Assistant**).

Layout: screenshot collage + short “how it works / impact” like SkillCycle feature cards.

1. **Wishlist** — cards (image, brand, price, review badge). Filters: pills **All / Ethnic Wear / In stock**.
2. **Still deciding** — usual size, occasion, free-text question → **Get answer** → one of five verdicts + proof bullets → **Add to bag** or **Still not sure**. Grounded in **this product’s reviews only**, not the 424 discovery corpus.
3. **Compare** — tick 2–3 saved items → recommendation + table. Cap at 3.
4. **30-min Express (out of the box)** — “Want delivery in 30 mins?” → enter pincode → **Check**. If pin matches a demo hub and SKU+size are in hub stock: prompt Yes / Not now / Get it in 30 mins. Else: not in area, or size not in hub (standard delivery). **Demo lookup, not live dark stores. No coupon.**
5. **Could-have (say this plainly):** wanted **virtual try-on** (upload a photo, see the dress on you). **Not shipped** — no free API was good enough. Next iteration if a usable model is available. Do not draw it as if it exists.

Keep “deliberately not built”: no % score, no order-history personalization, no support bot.

Hyperlink the app.

---

### Slide 5 — Who we talked to (SkillCycle persona layout)

**Keep:** 24–30, Tier 1–2, shops at least monthly, ethnic/occasion or fashion-forward, “Probably” intent. **Correct:** screener is **≥1 unsold wishlist item**, not 5+. (5+ / dormant 2+ weeks = designed *preference* for a worse freeze, captured on the form, not an exit.)

**Method:** live Google Form + 1:1-style write-up. n=6 overlay + **3 interview cards**.

**Caption (required, 14pt):**  
`Three interview cards are directional composites from the dormant-item form themes and the catalog-tied pilot — not a statistically powered sample.`

**Three cards (SkillCycle: name, age, role/context, Pain, JTBD, Quote):**

**Aadyant, 26 — occasion ethnic, intent “Probably”**  
- Why wishlisted: liked the look; saved for a family function.  
- Pain: listing photos vs threadwork/fabric in daylight.  
- JTBD: know if it will look cheap in person *before* buying.  
- Workaround: Google / cousin.  
- Quote: “I still don’t know if the embroidery will look cheap in daylight.”

**Meera, 28 — two saved looks**  
- Why: comparing options on the wishlist.  
- Pain: gown vs kurta-set for the same evening; opens other apps.  
- JTBD: pick one SKU without leaving Myntra.  
- Quote: “I keep opening the other saved piece instead of deciding.”

**Kabir, 24 — fit freeze, sitting 2+ weeks**  
- Why: liked the look; not sure on size.  
- Pain: usual M vs reviews that say size up.  
- JTBD: a clear size call so the item leaves the list.  
- Quote: “I’ll order when I know whether to take M or L.”

**Also on the slide (SkillCycle: survey vs 1:1 vs secondary):**

- **Form:** monthly+ fashion; **at least one unsold** item; questions = why saved, still intend *this* item, main blocker *now*, what would unstick in 30 days, info still needed, alternatives, outside the app. Link the viewform. Screenshot of the form if attached.
- **1:1 insights:** confidence (quality / compare / fit) dominates these intenders; they leave the app to decide.
- **Secondary (corpus):** leave-app **10.8%** of tagged rows; when they leave, **other shopping apps 60.9%** of those mentions. Do not merge with 6/6.

---

### Slide 6 — What research confirmed and changed

**Keep CONFIRMED / CHANGED structure.**

**Confirmed:** 6/6 left the app; 6/6 main blockers in the confidence cluster; 4/6 wanted similar-buyer reviews/photos; 4/6 said an in-app assistant would help decide faster. Personas on slide 5 illustrate quality (Aadyant), compare (Meera), fit (Kabir).

**Changed:** corpus n=424 ranks **price #2 at 23.8%**; these intenders **0/6** price as main blocker, **6/6** confidence. Target the confidence cluster. Price waiters remain OUT (no money lever).

**Footer:** two evidence layers (10.8% vs n=6). Never one blended rate. Drop 10/10, 7/10, 3/10, and the leaky 7-of-10 screener line.

---

### Slide 7 — Problem, segment, hypothesis, competition

**Keep** the 6-cell grid: Segment · Product outcome (decision-confidence rate, funnel stage 3) · Root cause (no in-app resolve for fit / quality-vs-photo / compare at reconsideration) · Workarounds (two sizes, friends, stores, off-app reviews, list grows) · User value · Business value (higher-AOV ethnic demand converts without discounting). Golden-thread strip.

**Correct target segment:**

- **Must:** ≥1 fashion item **still on the wishlist and not purchased**; shops monthly+; 24–30; Tier 1–2; “Probably” on a named ethnic/occasion or fashion-forward item.
- **Not the gate:** 5+ items. WPCR is “purchase ≥1 wishlisted item in 30 days.” One frozen high-intent SKU is enough. 5+ / several dormant 2+ weeks = where the freeze is *worse*, used to filter quotes, not to define the population.

**Why this segment:** already expressed intent (saved); high cost of being wrong (occasion, returns); in-app at reconsideration; brief forbids discounts so we cannot buy conversion from price-waiters.

**Impact:** lift **decision-confidence rate** at stage 3 → lift **WPCR**; fewer wasted trips off-app; fewer blind two-size orders (guardrail: returns must not rise).

**Hypotheses (SkillCycle style):**

1. Review-grounded verdicts **on the card** beat leaving for Google/YouTube.
2. Compare **2–3** saved items beats open-ended browsing.
3. A 30-min prompt (demo) can add urgency **without** a coupon.  
**Riskiest hypothesis:** they still will not buy without a physical / photo try-on → try-on is the named future, not this MVP.

**Competitive table (hyperlink public pages if you cite them):**

| Player / behaviour | What they do | Gap this MVP fills |
|---|---|---|
| Status quo | Two sizes + return, friends, YouTube, Instagram | No in-app close on the saved SKU |
| Amazon / Flipkart | Size charts, Q&A | Not Myntra wishlist; not occasion/threadwork grounded in *this* listing’s reviews |
| AJIO / Nykaa Fashion | Same wishlist freeze | Same confidence hole |
| Virtual try-on (paid / studio tools) | Photo on body | Better for drape; **not free** here; listed as could-have |
| **This MVP** | In-wishlist agent + compare + demo 30-min | Grounded yes/no without money; try-on not shipped |

---

### Slide 8 — How the MVP solves the problem on slide 7

**Do not** repeat the full tour from slide 4. This is **problem → solution**.

| Slide 7 cell | MVP response |
|---|---|
| Root cause: no in-app resolve | Still deciding on the wishlist card |
| Quality vs photo | Reviews for *this* SKU; proof bullets |
| Fit | Usual size + `Size up, then buy` / `Need more info` |
| Comparison | Compare 2–3 |
| Workaround: leave app | Keep the loop on Myntra |
| Workaround: two sizes | Verdict instead of guessing; returns as guardrail |
| No urgency | Express demo (secondary) |
| Physical try-on still missing | Honest could-have; not faked |

Keep one worked example (`Size up, then buy` / runs small) **or** a screenshot — not both long. Keep not-built list. Link the app.

---

### Slide 9 — Metrics (definition + rationale — do not skip)

SkillCycle-style table. **Type | Metric | Definition | What it measures | Why we chose it.** All 14pt. No invented target percentages.

| Type | Metric | Definition | What it measures | Why we chose it |
|---|---|---|---|---|
| North star | **WPCR** | % of users who purchase ≥1 item that was on their wishlist, within 30 days of the add | The brief’s business outcome | Every slide exists to move this, without money |
| Leading | Assistant engagement | % of in-scope wishlist sessions that open Still deciding / Compare / Express check | Whether the tool is found at hesitation | If they never open it, WPCR cannot move via this lever |
| Leading | Resolution rate | % of uses that end in add-to-bag, explicit “this helped”, **or** a clear decide-not-to-buy | Doubt actually closed | A confident no is a success (better than freeze) |
| Leading | Express attach (eligible pins only) | % of eligible pin checks that bag as Express | Whether urgency works without a coupon | Optional; must not outrank confidence |
| Guardrail | Return rate (fit/quality SKUs) | Returns ÷ orders on items that used the assistant | False confidence | A wrong “Go for it” would show up here |
| Guardrail | Wishlist-add rate | Adds to wishlist per session / user | Saving behaviour | Tool should resolve doubt, not scare people off saving |
| Guardrail | Fit / quality support contacts | Contacts tagged fit or fabric/photo | Whether in-app answers absorb those questions | Expected to **fall** if the assistant works |

---

### Slide 10 — Risks **and** mitigation steps

SkillCycle pattern: **Risk | Why it matters | Mitigation steps**. Keep SHIPPED / PLANNED. Standing line: never a discount/coupon/cashback tool.

| Risk | Why it matters | Mitigation steps | Status |
|---|---|---|---|
| Hallucinated fit/quality | Wrong buy → returns (guardrail) | Writer sees only supplied reviews; discovery figures verified vs aggregate; discard unsupported counts; offline fallback shows closest reviews, no fake verdict | SHIPPED |
| Thin evidence on new SKUs | Guessing is worse than freeze | Badge `Too few reviews`; verdict `Need more info`; demo includes a thin-review item | SHIPPED |
| Distrust of “AI” | They won’t use it | Proof bullets from real reviews beside every answer | SHIPPED |
| Comparison overload | More freeze | Hard cap 2–3 items | SHIPPED |
| Buried in a hub | Engagement leading stays ~0 | Embed on the wishlist card at hesitation | PLANNED (placement); demo already in-tab |
| 30-min read as live ops | Credibility hit | Copy + data = demo hubs/prefixes; ineligible pin or missing size → standard delivery | SHIPPED (demo) |
| Need physical try-on | Riskiest hypothesis | Do not fake try-on; name it as next if a free/good model exists | PLANNED |

---

## 5. Suggested titles (sharpen wording, keep meaning)

1. Closing the Wishlist Confidence Gap  
2. Saved demand dies at decision confidence, not at re-engagement  
3. The discovery engine ranks opportunities for WPCR — quality leads, price is out  
4. On the wishlist: ask, compare, or (demo) get it in 30 minutes  
5. Three intenders, one freeze: they leave the app to decide  
6. Corpus ranks price #2; these intenders are blocked by confidence  
7. No in-app way to resolve fit, quality, or compare on a saved item  
8. The MVP closes that gap on the card — without a coupon  
9. WPCR is the outcome; engagement, resolution, and guardrails tell us it’s real  
10. Solution-specific risks, and the steps already shipped to de-risk them  

---

## 6. What you must not do

- Do not change 424 / 44.7 / 23.8 / 20.3 / 10.8 / 7.5.
- Do not add Reddit as a scraped source.
- Do not restore n=10 or the leaky 7-of-10 screener.
- Do not describe the form as converters / “what finally made you buy.”
- Do not add discounts or a numeric confidence %.
- Do not present try-on as built.
- Do not use MVP product names as *discovery* evidence.
- Do not quote public reviews verbatim.
- Do not invent WPCR lift or TAM/SAM ₹ figures.
- Do not put the author’s name anywhere.

---

## 7. Screenshots to attach (filenames you can use)

If missing, draw a labeled wireframe and stamp `[SCREENSHOT]`.

| File | Capture |
|---|---|
| `tab1-ask.png` | Discovery: question + Get grounded answer + findings |
| `tab1-opportunity.png` | Right rail: 424, bars, headline |
| `tab2-wishlist-filters.png` | Cards + All / Ethnic Wear / In stock |
| `tab2-still-deciding.png` | Verdict + proof + Add to bag |
| `tab2-compare.png` | Compare table |
| `tab2-express.png` | Pincode + 30-min prompt |
| `form.png` | Google Form first page (incognito) |

---

## 8. Deliverable from Claude

1. Edited 10-slide `.pptx` (16:9).  
2. Export PDF (that is what the interviewer sees).  
3. Self-audit: 10 slides · 14pt · no name · n=6 not n=10 · ≥1 unsold not 5+ as gate · form URL is `/e/.../viewform` · Streamlit on 1/3/4/8 · try-on is could-have · every metric has definition + rationale · every risk has steps · titles-only story still holds.

**QA:** click every link incognito · grayscale check · read only the 10 titles.
