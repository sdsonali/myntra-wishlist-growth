# Wishlist hesitation survey (Google Form)

Google Forms cannot AND three answers on one page. The screener is three sections with skip logic; only people who pass all three reach Q4–Q15. Failures land on a thank-you page that **submits immediately** so they never see the rest.

## Create the form

1. Open [script.google.com](https://script.google.com) → **New project**
2. Paste `create_google_form.gs` and save
3. Run `createWishlistSurveyForm` (first run: authorize the script)
4. **Executions** / **Logs**: copy the live URL and edit URL
5. In the form editor: **Responses → Link to Sheets**

The form appears in your Drive as **Wishlist shopping decisions**.

## Skip logic (already in the script)

| Question | Continues | Thank & exit (submit) |
|---|---|---|
| Q1 frequency | Weekly, 2–4 times a month, Once a month | Rarely |
| Q2 wishlist size | 10+ | Less than 5, 5–10 |
| Q3 stale item | Yes | No |
| Q15 interview | Yes → email/phone | No thanks → submit |

Q4–Q14 sit after the screener. Section help text reminds people to stay on the **one item** they named in Q4.

## After you have ~30–40 responses

This is a funnel into 5–6 interviews, not a large-n study.

1. Filter to people who reached Q4 (everyone else was screened out)
2. From Q15 = Yes, rank by how specific Q9, Q11, and Q14 are
3. Recruit those first
