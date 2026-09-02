# Wishlist interview form (Google Forms)

**Segment:** monthly+ fashion shoppers who still have **unsold** wishlist items (the freeze the brief asks you to discover).

The interview item must be something still sitting on the wishlist. Buying a *different* wishlisted item in the last 30 days is allowed as context — it is not a gate, and it is not the item they answer about.

## Update the live form (keep the same URL)

Existing form: [edit](https://docs.google.com/forms/d/1pAxwhdTkoDF-I8U6HfzbnQ91UW9nkpmxIaEo9-qTEvQ/edit) · [view](https://docs.google.com/forms/d/e/1FAIpQLSdPOnDtw1lQGARNYOo2zOoUMpwlOAcLxIzmPaLz27XYN0TjNQ/viewform)

1. Open [script.google.com](https://script.google.com) → **New project**
2. Paste all of `create_google_form.gs` → Save
3. Run **`rebuildExistingDormantForm`** (opens that form by ID, deletes old questions, writes the dormant-wishlist interview)
4. Approve **Google Forms** access if asked
5. **Executions / Logs** should print the same live URL
6. Open the viewform in incognito and walk the new screener
7. Form editor → **Responses** → **Link to Sheets** if not already linked

Old converter answers in the Sheet will not line up with the new columns. Do not mix them into the write-up.

## Create a brand-new form (new URL)

Only if you want a clean form instead of rebuilding the published one:

1. Run **`createDormantWishlistInterviewForm`**
2. Copy the new viewform URL into the deck

`createMvpWishlistInterviewForm` is an alias for that create function.

## Do not import the old CSV

`responses/Wishlist shopping decisions.csv` is a **synthetic converter pilot** tied to the MVP catalog. It will not match this form’s columns or screener. Leave it in the repo as archive only.

## Screener

| Step | Continues | Exit |
|---|---|---|
| Shops fashion online | Weekly / 2–4× month / Once a month | Rarely |
| Has ≥1 wishlist item **not** purchased | Yes | No |

Collected on the next page (required, so the segment can be filtered — not used as exits):

- Age (target 24–30)
- City tier (target Tier 1–2)
- Wishlist size (target 5+)
- Several items dormant 2+ weeks
- Whether they *also* converted a different wishlist item in the last 30 days (Yes/No both continue)

## Interview topics (one unsold item)

Maps to the assignment brief:

| Brief | Form question |
|---|---|
| Why they saved | Why did you save this item? |
| Whether they still intend to purchase | Intent when saved + **do you still intend to buy THIS item** |
| What is stopping them | MAIN thing stopping you **now** |
| What would make them purchase | What would make you buy it **in the next 30 days** |
| Information they still need | What information do you still need? |
| Alternatives | Considering something else instead? |
| Outside the app | Google, friends, Instagram, store, etc. |
| How they overcome uncertainty | Open text (two sizes, exchange, leave it sitting, …) |
| MVP probe | Would an in-app assistant help you **decide yes or no faster**? + optional question |

## After the form: 5–6 live interviews

The brief asks for interviews, not only a form. Use form respondents who tick follow-up, plus anyone you recruit into the same segment.

Talk 20–25 minutes about **the same unsold item**. Probe:

- Walk through the last time they opened that wishlist card. What did they still not know?
- If they left the app, where, and did they come back?
- If the blocker is price, note it and do not steer them toward discounts. You cannot offer money in the solution.
- Ask them to compare this item with at most two other saved items if they are stuck between options.

Write an anonymized notes doc (quotes, no names) and link that from the deck alongside the viewform URL.

Filter the sample before you quote it: prefer 24–30, Tier 1–2, monthly+, 5+ items, dormant 2+ weeks, ethnic / occasion / fashion-forward, intent “Probably.” Report who you dropped and why.
