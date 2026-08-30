# Myntra Wishlist Conversion Project — Master README

## Goal
Increase % of users who purchase ≥1 wishlisted item within 30 days — **without monetary incentives**.

## The 7 Parts (and where they live)

| Part | What it is | Output file/link |
|---|---|---|
| 1 | AI Discovery Engine (analyze reviews/Reddit/YouTube at scale) | Streamlit Tab 1 — see `docs/02_discovery_engine.md` |
| 2 | Metric decomposition (Wishlist → Purchase funnel) | 1 slide in deck |
| 3 | 5–6 user interviews validating the opportunity | Notes doc, summarized in deck |
| 4 | Problem definition (segment, root cause, why it matters) | 1–2 slides in deck |
| 5 | MVP — functional, deployed | Streamlit Tab 2 — see `docs/04_mvp.md` |
| 6 | Success metrics (north star, leading, guardrail) | 1 slide in deck |
| 7 | Risks & mitigation | 1 slide in deck |

Deck details: see `docs/03_slides.md`

## The Golden Thread (this is what actually gets graded)
```
Business Metric → Product Outcomes → AI Discovery → Primary Research → Problem Definition → MVP
```
Every part must visibly connect to the next. Don't let Part 1 (discovery) and Part 5 (MVP)
feel like separate projects — the MVP must solve exactly what your interviews (Part 3),
grounded in your discovery themes (Part 1), pointed to.

## Two Separate Datasets — Do Not Mix
1. **Discovery data** (Part 1): general reviews/Reddit/YouTube about Myntra experience,
   wishlist behavior, purchase hesitation. Used to find THEMES, not to fix one product.
2. **MVP data** (Part 5): product-specific reviews for 6–8 chosen demo products
   (scraped from actual Myntra product pages). Used to give the MVP real, grounded answers.

## Architecture Decision
One Streamlit app, two tabs, one deploy (Streamlit Community Cloud, free, public URL):
- **Tab 1** = Discovery Engine (Part 1 deliverable)
- **Tab 2** = Wishlist Confidence Copilot / MVP (Part 5 deliverable)

Same repo, one **free LLM API** (provider chosen when we wire up the code — e.g. Gemini,
Groq, Hugging Face, or similar free tier). Shared review-tagging code where possible.
Keep it simple — no n8n, no vector DB, no custom backend needed.

## LLM / API choice (decide when we build)
Use **free-tier APIs only** — no paid Claude or OpenAI required unless you choose to later.
Pick the provider when we wire up the tagging script (likely Aug 16–17). Candidates to compare then:
- **Google Gemini** — free tier, good for batch JSON extraction
- **Groq** — free tier, fast inference (Llama / Mixtral)
- **Hugging Face Inference API** — free tier for open models

Store the key in `.env` / Streamlit secrets — never commit it. Same key powers Tab 1 (tagging + synthesis) and Tab 2 (MVP answers).

## Timeline (today → Sep 4, 3:59 PM IST deadline)

| Dates | Focus |
|---|---|
| Aug 15–17 | Scrape/collect general reviews (discovery corpus), write offline LLM tagging script (free API) → theme JSON |
| Aug 18–20 | Build Tab 1 (query + theme dashboard), draft metric decomposition (Part 2) |
| Aug 21–25 | Recruit + conduct 5–6 interviews (Part 3), synthesize findings |
| Aug 26–27 | Lock problem definition (Part 4) — this decides what the MVP will be |
| Aug 28–30 | Scrape product-specific reviews for 6–8 demo products (MVP dataset) |
| Aug 30–31 | Build Tab 2 MVP logic + UI, deploy full Streamlit app |
| Sep 1–2 | Build 10-slide deck (14pt font strict, punchy titles) |
| Sep 3 | Full QA: test both tabs live, click every link in the deck, check font size, colorblind check |
| Sep 4 (before 3:59 PM) | Final submission, buffer built in — do not submit at the last minute |

## Hard Rubric Rules (don't lose free points)
- Fellow's name NOT anywhere in the deck.
- Max 10 slides.
- Font size 14 — strictly, everywhere.
- Slide titles = the key message, not generic labels ("Users delay purchase due to fit doubt," not "Findings").
- Any linked artifact (survey, sheet, etc.) must be accessible to the reader — test in incognito.
- Color choices must work for colorblind readers — avoid red/green as the only differentiator.

## Deliverables Checklist
- [ ] AI Discovery Engine — public testable link
- [ ] 1 slide in deck explaining how the discovery engine works
- [ ] 10-slide PDF deck (all parts covered, 14pt font)
- [ ] Deployed MVP — public testable link
