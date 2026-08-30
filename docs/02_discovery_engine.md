# README 2 — AI Discovery Engine (Part 1 / Streamlit Tab 1)

## What it needs to prove
Not summarization, not sentiment analysis. It must **identify, quantify, and compare
opportunity areas** that could move wishlist→purchase conversion.

## Data sources to collect (general, not product-specific)
- Google Play Store reviews for Myntra
- App Store reviews for Myntra
- Reddit (r/india, r/IndianFashionAddicts, general shopping threads)
- YouTube comments on Myntra haul/unboxing/review videos
- Fashion/shopping community discussions (Twitter/X, forums)

Target: ~300–500 pieces of text minimum. More is fine, but this is enough to find
real patterns at 90%-score quality — don't over-scrape and burn your timeline.

## Step-by-step build

### Step 1 — Collect (Aug 15–16)
- Play Store: use a scraper library (e.g. `google-play-scraper` in Python) — free, no auth.
- Reddit: Reddit API (PRAW) or manual search + copy, targeting keywords like
  "wishlist", "myntra size", "myntra return", "still deciding", "ajio vs myntra".
- YouTube: YouTube Data API for comments on relevant videos, or manual collection.
- Store everything in one CSV: `source | text | date (if available)`.

### Step 2 — Tag with a free LLM API (offline script, Aug 16–17)
Write a Python script that batches ~20 reviews per API call using a **free LLM provider**
(exact API chosen when we build — e.g. Google Gemini free tier, Groq, Hugging Face).
Prompt shape:

```
You are analyzing user feedback about online fashion shopping (Myntra).
For each review below, extract:
- reason_for_wishlisting (if mentioned): e.g. price_wait, style_confirmation, gift_idea, just_browsing
- purchase_blocker (if mentioned): e.g. fit_uncertainty, price_change, found_alternative,
  forgot, quality_doubt, occasion_mismatch, no_urgency
- comparison_behavior (if mentioned): does the user compare multiple items before deciding?
- info_sought_outside_app: what (if anything) did they check outside Myntra before buying?

Return ONLY valid JSON, no preamble. One object per review.
```

Save all tagged output into one `tagged_reviews.json`.

### Step 3 — Aggregate into an opportunity table (Aug 17)
From the tagged JSON, compute simple frequency counts:
- Top 5 reasons for wishlisting (with % of mentions)
- Top 5 purchase blockers (with % of mentions)
- % of reviews showing comparison behavior
- % of reviews mentioning external research (Google, friends, influencers, etc.)

This table is your **opportunity comparison** — rank blockers by frequency to see
where the highest-potential problem is. This directly feeds Part 2 and Part 4.

### Step 4 — Build Tab 1 UI (Aug 18–20)
Keep it simple — no vector DB needed for this dataset size:
- A text box: "Ask a question about why users don't convert wishlisted items"
- On submit, a two-step agent (mirrors the MVP's router → writer):
  1. **Router** (`route_corpus_question`) — the LLM maps the question onto the tag
     vocabulary the corpus was actually labelled with (`BLOCKER_LABELS`,
     `REASON_LABELS`, comparison, external research). No keyword lists to maintain.
  2. **Retrieval** (`filter_reviews`) — rank rows by how many routed labels they
     carry; question wording only breaks ties, weighted by corpus-derived inverse
     document frequency so "and" cannot outrank "sangeet".
  3. **Writer** (`answer_question`) — gets the excerpts plus an explicit per-label
     count block, and returns JSON findings. Every figure it cites is checked
     against those counts (`_verify_counts`); unsupported points are discarded.
- A static chart (bar chart, `st.bar_chart`) showing the opportunity table frequencies.
- A short "How this works" caption block (this becomes your 1-slide explainer).

**Why routing beats keyword matching here:** "quality" appears in 21% of reviews and
"myntra" in 18%, so no single frequency cutoff separates signal from noise — and a
hand-written keyword list silently goes stale every time the corpus is refreshed.

**Optional upgrade (only if time allows near the end):** `sentence-transformers`
(all-MiniLM) embeddings + numpy cosine similarity for the tie-break stage. Not required
for a strong score — don't spend time here unless everything else is done early.

## What "quantify and compare" looks like in your output
Don't just say "fit uncertainty is a problem." Say:
> "Fit uncertainty appears in 34% of purchase-blocker mentions, more than price (18%)
> or forgetting (12%) — making it the single largest addressable blocker."

This sentence pattern is what separates discovery from just sentiment analysis.

## Deliverable
- Public Streamlit link (same app as MVP, Tab 1)
- 1 slide in the deck: simple flow diagram — Scrape → LLM tags themes → Aggregate →
  Browse/query findings live. Include the opportunity table as a small chart on this slide.
