# Deck build prompt

Paste everything below the line into the cloud agent. It is self-contained — the agent needs
no access to the repo.

---

# TASK

You are a senior product design partner producing the **final 10-slide submission deck** for a
Myntra product-management case study: *increase the share of users who purchase at least one
wishlisted item within 30 days, without monetary incentives.*

Two artefacts are already built and deployed as one Streamlit app with two tabs — an AI
Discovery Engine and a working MVP. Your job is to turn the work described below into the deck.

**Deliver:** a runnable `python-pptx` script that writes `Myntra_Wishlist_Confidence_Gap_FINAL.pptx`
at 13.333 × 7.5 in (16:9), followed by a short self-audit against the hard constraints. No
other prose.

You may put the long-form explanation of each slide into PowerPoint **speaker notes** — notes
are not slides and are not subject to the on-slide font rule. Keep what is *visible* sparse.

---

# PART 1 — HARD CONSTRAINTS

These come from the graded rubric. Each one is free points lost if broken.

1. **Maximum 10 slides.** Exactly 10 is expected. Never 11.
2. **Font size 14 — everywhere, strictly.** The QA instruction is literally "check every text
   box is 14pt, no exceptions." That includes titles, eyebrow labels, footers, page numbers,
   table cells, chart axis labels and chart data labels. Build visual hierarchy from **bold
   weight, colour, UPPERCASE, letter-spacing, panel fills and whitespace — never from size.**
3. **No personal name anywhere in the deck.** The author is only ever
   "Product Manager, Growth Team".
4. **Every slide title is the key message, not a category label.** Write
   "Users delay purchase due to fit doubt", never "Findings". The test: someone reading only
   the 10 titles, in order, must understand the entire argument.
5. **Colourblind-safe.** Never let red/green be the only differentiator. Anything marked
   in-scope vs out-of-scope must *also* carry a text label ("IN" / "OUT") or an icon.
6. **Every linked artefact must open for a logged-out reader.** Links go on the discovery
   engine, the MVP, and the primary-research form.

Design notes, also from the rubric:

- One consistent colour and style system across all slides — no per-slide redesigns.
- Prefer simple bar charts and funnel diagrams over walls of text.

---

# PART 2 — DESIGN SYSTEM

Carry this over unchanged from the previous version; do not invent a new palette.

| Token | Hex | Use |
|---|---|---|
| Navy | `07293E` | titles, dark panels, primary |
| Mid navy | `0B3D5C` | panel on dark background |
| Amber | `E8A33D` | accent, the highlighted funnel stage, eyebrows on navy |
| Dark amber | `B97A1E` | eyebrow text on white |
| Cool panel | `F4F7F9` | neutral content panels |
| Warm panel | `FCEFDA` | caveats and honesty callouts |
| Ink | `1A1A1A` | body text |
| Muted | `5C6B73` | secondary text, footers |
| Light on navy | `C7D6E0` / `E3ECF2` | body text on navy |

Every content slide: white background · UPPERCASE amber eyebrow · bold navy key-message title ·
content · footer with "Product Manager, Growth Team" left and the slide number right. All 14pt.

---

# PART 3 — WHAT WAS ACTUALLY BUILT

Read this carefully. Slides 3 and 8 must describe this accurately, and nothing anywhere in the
deck may contradict it.

## 3A. Tab 1 — the AI Discovery Engine

**Purpose:** find, at scale and from public evidence, what actually blocks people from buying
things they already saved — and let a PM interrogate that evidence live.

### Stage 1 — Collect (offline)

Three free public sources, no scraping of private data:

- **Google Play** reviews of the Myntra app (`google-play-scraper`, India/English, newest first).
- **Apple App Store** reviews via the public iTunes RSS feed, across several storefronts
  because the India feed is often sparse.
- **YouTube** comments via the Data API on Myntra haul/review/unboxing videos — this is where
  people talk about how garments actually arrived.

Roughly 1,000 raw rows land in a CSV. Final source mix in the tagged corpus:
YouTube 212 · Google Play 154 · App Store 58.

### Stage 2 — Curate a gold corpus (LLM)

Raw app-store reviews are mostly noise for this question — delivery complaints, login bugs,
one-word praise. An LLM judges every review in small batches and returns, per review:
`keep_for_gold`, a 0–100 relevance score, a `primary_signal` label, a rationale, and a
`noise_category`.

- **Kept:** fit uncertainty, quality doubt, price hesitation, comparison behaviour, occasion or
  styling mismatch, liked-the-look saving, wishlist delay, external research.
- **Dropped:** generic app praise, pure delivery/refund/service complaints, spam, off-topic.

Results merge into a rolling, de-duplicated gold corpus. If the LLM quota dies mid-run, a
keyword heuristic finishes the batch so the pipeline always completes.

### Stage 3 — Tag each surviving review (LLM)

Every gold review is tagged on four dimensions, using a fixed label vocabulary:

| Field | Labels |
|---|---|
| `reason_for_wishlisting` | liked_look · occasion_save · compare_later · need_uncertainty · style_confirmation · price_wait · budget_wait · just_browsing |
| `purchase_blocker` | fit_uncertainty · price_change · found_alternative · forgot · quality_doubt · occasion_mismatch · no_urgency |
| `comparison_behavior` | true / false / null |
| `info_sought_outside_app` | instagram · youtube · google · friend_family · other_apps · physical_store · influencer |

The prompt enforces one hard separation: **why they saved it** must never be confused with
**why they haven't bought it**. Output is canonicalised against the vocabulary, the tag schema
is versioned, and runs resume by normalised review text so a refresh only pays for new rows.

Result: **424 tagged reviews.**

### Stage 4 — Aggregate

Frequency counts become an opportunity table: top wishlisting reasons and top purchase
blockers as a share of mentions, share of the corpus showing comparison behaviour, share
researching outside the app, and a per-source breakdown. The n=10 survey is attached as a
separate overlay and **never merged** into the corpus percentages — they are two evidence
layers, not one rate.

### Stage 5 — Ask it questions live (a three-step agent)

This is the part worth putting on a slide. A PM types a question and three steps run:

1. **Router (LLM).** Given the *actual* tag vocabularies, the model maps the question onto the
   labels that can answer it, returning the intent plus which blockers, which reasons, and
   whether comparison or outside-app research is in play. Anything it returns that isn't a real
   label is discarded. There are **no keyword lists and no stopword list anywhere in the
   system** — the question is interpreted, not string-matched.
2. **Retrieval.** Rows are ranked by *how many* of the routed signals they carry. Question
   wording only breaks ties between rows that tie on labels, weighted by inverse document
   frequency learned from the corpus itself. This mattered: the word "quality" appears in 21%
   of reviews and "myntra" in 18%, so no frequency cutoff can separate signal from noise, and a
   hand-written stopword list would silently rot every time the corpus is refreshed. Picks are
   then spread across sources so a single platform can't own an answer.
3. **Writer (LLM), with its arithmetic checked.** The writer receives the selected excerpts
   *plus an explicit count block* — the real per-label counts for this matched set. It returns
   structured findings ranked by blocker size, plus one question worth asking a real shopper.
   **Every figure it cites is then verified in code against those counts, and any finding
   citing a number the corpus does not support is discarded before the PM ever sees it.**

That last control is the headline: the engine cannot quote a statistic it invented. During
testing the model did fabricate counts — including copying an example figure out of its own
instructions — and the verification layer is what stops that reaching a slide.

The tab also shows which signals the question was routed to, consensus metrics, and bar charts
of blockers, reasons and source mix. It never dumps raw review text at the user.

## 3B. Tab 2 — the MVP: Fit & Confidence Assistant

**The problem it solves:** at the moment of hesitation over a saved item, there is no way
inside the app to settle "will this look like the photo?" and "will it fit?", so people leave
to research elsewhere and mostly never come back to finish the purchase.

**The data:** seven real ethnic/occasion products presented as a mock wishlist, each with
genuinely scraped product-page reviews — 15, 14, 14, 12, 10, 9 and **3**. The three-review item
is deliberate: it exists to demonstrate honest behaviour when evidence is thin.

**The card badge.** Cheap local text signals produce a plain-language hint, with no API call
and **never a numeric score**: *Mostly true to size · Several say size up · Mixed on fit · Some
quality cautions · Quality reads well · Reviews are mixed · Too few reviews.*

**Ask a question — a two-step agent.** The shopper picks an item, optionally gives their usual
size and the occasion, and asks in their own words:

1. **Router (LLM).** The item's reviews are numbered. The model decides what the shopper is
   actually stuck on and selects the specific review numbers that answer *that* question —
   3 to 6 of them, and it is required to include reviews on **both sides** where opinion splits
   rather than only the flattering ones. A floor tops the selection up so the writer is never
   starved of context.
2. **Writer (LLM).** Sees only the selected reviews and returns a verdict, a direct answer, and
   proof. The verdict is exactly one of five: **Go for it · Size up, then buy · Hesitate ·
   Skip · Need more info.** It must address the shopper in the second person, its opening must
   agree with its own verdict, and "Size up, then buy" is only permitted when reviewers say the
   item runs small — if it runs large, it must say to take the usual size or go down.

**What the shopper sees:** the verdict, a short direct answer, an "If it goes wrong" line using
honest exchange-path language (it never promises a support outcome), and "From reviews" proof
bullets drawn from real review text.

**Compare** is capped at the 2–3 saved items the shopper ticked — a hard cap, to avoid
re-creating the decision fatigue the feature exists to remove.

**When the model is unreachable** the assistant retrieves the closest *real* reviews and says
it is unavailable. It never fabricates a verdict to fill the space.

**A presenter-view toggle** reveals the agent's trace (what the router read, how many reviews
it picked, what the writer concluded). It is off by default, because a shopper wants an answer,
not a system diagram.

**Deliberately not built** — and the deck must not imply otherwise:

- No numeric confidence score of any kind.
- No personalised fit from the shopper's own order or return history.
- No customer-support chatbot and no promise of better support. The strategy is to stop people
  *needing* support for questions the reviews already answer.

## 3C. Shared foundation

One free-tier LLM provider abstraction (Hugging Face / Groq / Gemini interchangeable) with
retries, JSON-mode enforcement and tolerant JSON parsing. Keys live in `.env`, never in the
repo. No vector database, no orchestration framework, no custom backend — one Streamlit app,
two tabs, one deploy.

---

# PART 4 — VERIFIED DATA

Regenerated 30 Aug 2026. **Use these figures and no others.** Do not carry over numbers from
any earlier draft of this deck.

**Corpus:** 424 LLM-curated, LLM-tagged public reviews.
Sources: YouTube 212 · Google Play 154 · App Store 58.

**Purchase blockers** — share of 340 blocker mentions:

| Blocker | Share | Count | Scope |
|---|---|---|---|
| Quality / authenticity doubt | 44.7% | 152 | IN |
| Price change / deal-waiting | 23.8% | 81 | **OUT** |
| Fit / size uncertainty | 20.3% | 69 | IN |
| Found an alternative | 7.9% | 27 | IN |
| No urgency | 2.1% | 7 | IN |

**Why they saved it** — share of 122 reason mentions:
liked the look 47.5% · compare later 32.8% · saving for an occasion 8.2% ·
style confirmation 7.4% · just browsing 1.6%

**Corpus behaviour:** comparison behaviour 7.5% (32 rows) · researched outside the app 10.8%
(46 rows).

**Where they go when they leave** — share of 46 external-research mentions:
other shopping apps 60.9% · YouTube 17.4% · friends/family 10.9% · Google 8.7% · Instagram 2.2%

**Generated headline, quotable as-is:** "Quality doubt appears in 44.7% of purchase-blocker
mentions, more than price change (23.8%) or fit uncertainty (20.3%) — making it the single
largest addressable blocker in this corpus."

**Primary research — pilot survey, n = 10.** Recruited to a designed segment: 24–30, Tier 1–2
India, shops fashion at least monthly, 5+ wishlist items with several dormant 2+ weeks. One
named real saved item each; 4/10 named ethnic or occasion wear.

- Main blocker: price/budget 3 · comparison 2 · quality 2 · occasion/style 2 · fit 1.
  **Confidence cluster (comparison + quality + occasion + fit) = 7/10.**
- Purchase intent: "Probably" 6/10 · "Yes, definitely" 3/10 · "Not sure" 1/10.
- **10/10 did at least one thing outside the app before deciding:** compare prices 6 ·
  visit a store 6 · Instagram 3 · friends 3 · YouTube/Google 3.
- **7/10 wanted reviews or photos from similar buyers.**
- Coping today: order two sizes and keep the one that fits · order per the size chart then
  exchange · leave it in the wishlist until payday.

---

# PART 5 — HONESTY REQUIREMENTS

These earn credit. Do not sand them off to make the story cleaner.

- Public reviews **under-index the silent wishlist freeze** — nobody writes a review about an
  item they never bought. Reviews set direction; the survey probes the freeze directly.
- The pilot is **n=10, directional, not statistically powered**, and the screener was leaky
  (frequency and wishlist-size blank for 7 of 10 respondents).
- The quality-doubt bucket is **broad**. Where the tagger returned null it was filled by
  keyword, so the bucket absorbs some service and delivery complaints. Describe it as the
  broadest bucket rather than implying it is purely photo-versus-real fabric doubt.
- **Price is the #2 blocker at 23.8% and is deliberately out of scope**, because the brief
  allows no monetary levers. State this as an explicit scoping decision, not an omission — and
  show that the in-scope confidence themes (44.7 + 20.3 + 7.9) still dominate the addressable
  set.
- Two evidence layers must never be merged: reviews mention leaving the app in 10.8%, survey
  respondents almost universally did.
- Comparing options and leaving the app are **decision behaviour**, not a lifestyle preference.
- Never recommend fixing catalogue quality, logistics or customer support — those are not this
  team's levers.

---

# PART 6 — CORRECTIONS TO THE PREVIOUS DRAFT

An earlier version of this deck exists. It is wrong in these specific ways.

**Stale numbers** (the corpus was re-scraped and re-tagged since):

| Previous draft | Correct now |
|---|---|
| n = 550 reviews | **424** |
| Quality 47.8% | **44.7%** |
| Fit 13.0% | **20.3%** — fit is materially stronger than before |
| Price 13.9%, ranked below fit | **23.8%, now the #2 blocker overall**, still out of scope |
| Comparison 11.8% | **7.5%** |
| External research 10.5% | **10.8%** |
| Found alternative 5.2% | **7.9%** |
| Occasion mismatch 2.6%, listed as a top blocker | **No longer in the top five** — drop it; fifth is "no urgency" at 2.1% |

**Fabricated MVP claims.** The previous MVP slide described a product that does not exist.
Delete all of these outright:

- ❌ A numeric confidence score ("Confidence: 87%")
- ❌ "87% of similar buyers say true to size — based on 214 verified reviews"
- ❌ "Personalized fit cross-reference — uses the user's own past order/fit history"
- ❌ Any implication of a support chatbot or improved customer service

**Structural gap.** The previous draft had no dedicated slide explaining how the discovery
engine works — it compressed that into a one-line caption above a chart. That explainer is a
required Part 1 deliverable and gets its own slide here (slide 3).

**Font.** The previous draft used seventeen different font sizes from 9.5pt to 40pt. Everything
visible in this deck is 14pt.

---

# PART 7 — SLIDE-BY-SLIDE SPECIFICATION

This structure is prescribed by the rubric. Follow it. Titles below state the intended
message — sharpen the wording, keep the meaning.

**1 · Title + framing.**
"Closing the Wishlist Confidence Gap" — framed as fixing a specific blocker, not as a generic
project name. Subtitle: improving wishlist-to-purchase conversion by resolving in-app decision
doubt, without discounts, coupons or cashback. Three chips: FOCUS ethnic / occasion /
fashion-forward saved items · LEVER in-app decision confidence, not price · CONSTRAINT no
monetary incentives.

**2 · The business metric, broken down.**
Title states which stage is targeted and why — e.g. "Saved demand dies at decision confidence,
not at re-engagement." North star: WPCR, the share of users purchasing ≥1 wishlisted item
within 30 days of adding it. Funnel: Add to wishlist → Reconsideration trigger → **Confidence
resolution** → Decision → Checkout, with the confidence stage visually marked as the target.
Close with in-scope vs out-of-scope segments (in: confidence-blocked intenders, ethnic over
basics; out: price-only waiters, since no monetary lever exists).

**3 · How the AI Discovery Engine works** — the required Part 1 explainer.
Left: the offline pipeline as a simple four-step diagram — scrape three public sources → LLM
curates a gold corpus → LLM tags four dimensions per review → aggregate into an opportunity
table. Right: the live three-step agent — router maps the question onto the real tag vocabulary
→ retrieval ranks by routed labels with IDF tie-breaking → writer produces findings **whose
every figure is verified against the aggregate, with unsupported claims discarded.** Call that
verification out as the anti-hallucination control; it is the strongest thing on this slide.
Link the live engine.

**4 · What the discovery engine found.**
Title carries the finding — e.g. "Quality doubt leads at 44.7%; fit is real at 20.3%; price is
larger still but off-limits." Horizontal bar chart of the five blockers, each with an IN/OUT
text label so scope never depends on colour. Add one or two **paraphrased** example patterns per
top blocker — describing the *pattern*, never quoting a review verbatim. Draw these only from
the app-review corpus described in Part 3A: fabric or finish arriving cheaper than the listing
suggested and doubts about authenticity (quality); not trusting the size chart enough to commit
without an exchange (fit); checking the same item on another shopping app before deciding
(found alternative — note other apps are 60.9% of all outside-app research). Put the
under-indexing and broad-bucket caveats in a warm panel.

**Do not mix the two datasets.** The discovery corpus is general app reviews about Myntra
behaviour and exists to find *themes* (slides 3–4). The MVP's seven products have their own
separate product-page reviews and exist to give the MVP grounded answers (slide 8). Never use
an MVP product example as discovery evidence, or quote a discovery review on the MVP slide.

**5 · Who we talked to and why.**
Target segment definition plus method: a recruited pilot survey, n=10, one named real saved item
per respondent, screened for monthly+ fashion shoppers with dormant wishlist items. Say plainly
what was asked. Lead with the caveat that this is directional and the screener was leaky. Link
the form.

**6 · What primary research confirmed, and what it changed.**
This slide proves the thread converges. Confirmed: 10/10 leave the app to decide, and 7/10 of
main blockers sit in the confidence cluster, so the in-app confidence gap is real. Changed: the
discovery corpus ranks price second overall, but among these intenders price is only 3/10 and
confidence is 7/10 — so the target is the confidence cluster, not the price waiters. Also:
7/10 explicitly wanted similar-buyer reviews and photos, which is what the MVP delivers.

**7 · The problem, precisely defined.**
One tight slide, labelled grid: **segment** (24–30, Tier 1–2, monthly+ fashion shopper, 5+
saved items with several dormant, "Probably" intent, ethnic/occasion or fashion-forward) ·
**product outcome** (decision-confidence rate, funnel stage 3) · **root cause** (no in-app
mechanism at reconsideration to resolve fit, quality-versus-photo, or comparison doubt, so
users leave and the loop rarely closes) · **workarounds today** (order two sizes and return,
ask friends, visit stores, search off-app reviews, let the wishlist grow forever) · **user
value** (less anxiety, fewer returns, a faster yes or no on high-stakes occasion buys) ·
**business value** (higher-AOV ethnic demand already saved converts without discounting).
Foot the slide with the golden-thread strip: WPCR → stage-3 outcome → AI discovery → primary
research → in-app confidence gap.

**8 · The MVP: how it solves this.**
Title carries the mechanism — e.g. "An agent reads this item's reviews and gives a verdict, in
the wishlist." Show the flow in one line: shopper's question → router selects the reviews that
answer it, both sides where opinion splits → writer returns one of five verdicts with proof
from real reviews. Include a real worked example (a plain-language badge plus a verdict and a
proof bullet). State what it deliberately does **not** do: no confidence score, no personal fit
history, no support promises — and that with thin evidence it says "Too few reviews" rather than
guessing. Link the deployed MVP.

**9 · How we'll know it's working.**
Each metric gets a one-line rationale for why it was chosen. North star: WPCR. Leading
indicators: assistant engagement rate (share of in-scope wishlist visits that use it) and
resolution rate (share of uses ending in add-to-cart, an explicit "this helped", or a clear
decide-not-to-buy — a confident no is a success). Guardrails: return rate must not increase
(false confidence is the failure mode), wishlist-add rate must not decrease, and fit/quality
support contacts are expected to fall.

**10 · Risks and how we'd de-risk them.**
Top risks specific to this solution, not generic ones. Mark each mitigation **SHIPPED** or
**PLANNED** — that distinction is the point of this slide:

- Hallucinated fit/quality claims — *shipped*: answers grounded only in supplied reviews,
  every discovery figure verified against the aggregate, honest offline fallback.
- Thin evidence on new items — *shipped*: a 3-review item in the demo, a "Too few reviews"
  badge, and a "Need more info" verdict rather than a guess.
- Users distrusting an AI summary — *shipped*: real review proof shown beside every answer.
- Low discoverability if buried — *planned*: embed in the wishlist card at the moment of
  hesitation, not in a separate hub.
- Comparison overload — *shipped*: hard cap at 2–3 saved items.

Close with the standing constraint: never a discount, coupon or cashback tool.

---

# PART 8 — LINKS

Use these literal placeholders as both the visible text and the hyperlink target, so a script
can swap in real URLs later:
`[LINK: AI Discovery Engine]` · `[LINK: Deployed MVP]` · `[LINK: Primary research form]`

---

# PART 9 — SELF-AUDIT BEFORE YOU FINISH

Report on each:

- [ ] Exactly 10 slides
- [ ] Every visible text run is 14pt — titles, eyebrows, footers, page numbers, chart labels
- [ ] No personal name anywhere
- [ ] All 10 titles are messages; read in order they tell the whole argument unaided
- [ ] Nothing relies on red/green alone; IN/OUT carry text labels
- [ ] Every number traces to Part 4; none invented, none carried over from the old draft
- [ ] No claim about the MVP contradicts Part 3B, and none of the Part 6 fabrications survive
- [ ] One consistent style system; no per-slide redesign
- [ ] Three links present as placeholders
