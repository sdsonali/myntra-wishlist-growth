# README 4 — MVP: Wishlist Confidence Copilot (Part 5 / Streamlit Tab 2)

## Wait for Part 4 before locking this in
The exact MVP depends on what your interviews (Part 3) confirm as the dominant blocker.
Do NOT start building this until the problem definition (Part 4) is locked — building the
wrong MVP (mismatched to your research) is the single biggest way to lose points here.

Below is the general build pattern — same shape regardless of which blocker wins.

## Two possible directions (pick based on interview findings)

### If the blocker is FIT UNCERTAINTY → "Fit Confidence Copilot"
- Input: user selects 1 wishlisted item + basic profile (height, usual size, body type)
- Output: grounded verdict from real reviews, e.g. "12 of 40 reviewers said this runs
  small; people your height ordered one size up — go with L, not M"

### If the blocker is COMPARISON PARALYSIS → "Wishlist Comparator"
- Input: user selects 2–3 wishlisted items
- Output: side-by-side table (fabric, sizing, occasion-fit, review sentiment) + a
  one-line recommendation with reasoning

### If the blocker is OCCASION/STYLING DOUBT → "Styling & Occasion Resolver"
- Input: user selects 1 item + types an occasion ("cousin's sangeet")
- Output: verdict + styling tips paraphrased from reviews that mention similar occasions

**Only build ONE of these** — whichever your interviews point to most strongly.

## Data you need — separate from the Discovery Engine dataset
The Discovery Engine (Tab 1) uses general reviews about Myntra behavior overall.
The MVP needs **product-specific** reviews for a small demo catalog.

### Step 1 — Choose 6–8 demo products (Aug 28)
Pick real Myntra products in one category relevant to your problem (e.g. ethnic wear
if occasion/fit is the blocker). Note product URLs.

### Step 2 — Scrape their reviews (Aug 28–29)
Simple script (BeautifulSoup or similar) pulling the reviews already shown on each
Myntra product page — no login needed, these are public.
Store as:
```json
{
  "product_id": "libas_anarkali_001",
  "name": "Libas Pink Anarkali Suit",
  "price": "₹1,499",
  "image_url": "...",
  "reviews": [
    "Runs small, ordered L instead of M",
    "Wore this for my cousin's sangeet, got compliments",
    "Fabric is thin, not great for winter functions"
  ]
}
```

### Step 3 — Handle sparse data honestly
If a product has few reviews, don't let the LLM fabricate. Instruct it explicitly:
"If there isn't enough review evidence to answer confidently, say so and fall back to
general category-level patterns." This also becomes a named risk in Part 7.

## Step 4 — Build Tab 2 UI (Aug 30–31)
- Show the 6–8 demo products as simple cards (image, name, price) — this is your fake
  "wishlist."
- Let user select item(s) + fill 1–2 small inputs depending on which direction you chose.
- One button: "Resolve my doubt" / "Compare these" / "Check for this occasion."
- On click: pull that product's review JSON → send to the free LLM API with a strict system prompt:

```
You are a shopping assistant. Only use the review excerpts provided below to answer.
Cite approximate counts where possible (e.g. "12 of 40 reviewers said...").
Never invent claims not supported by the reviews. If evidence is insufficient, say so
and offer general category guidance instead.

Reviews: {review_excerpts}
User question: {user_input}
```

- Display the LLM answer clearly — short, specific, actionable. This is the whole MVP.

## What makes this "minimum"
- No login, no cart, no persistent backend/database — stateless per session.
- No custom design polish needed — default Streamlit components are fine.
- Only needs to prove the core mechanic works end-to-end for a real user.

## What it must NOT be
- A static mockup/wireframe — it must actually call the LLM API and return real output.
- Disconnected from the problem defined in Part 4 — the blocker it solves must match
  exactly what your interviews surfaced.

## Deliverable
- Public Streamlit link (same app as Discovery Engine, Tab 2)
- Screenshot + short flow description for deck Slide 8
