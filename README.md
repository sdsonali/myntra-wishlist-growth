# Myntra Wishlist Conversion

One Streamlit app, two tabs:
- **Tab 1** — AI Discovery Engine
- **Tab 2** — Fit & Confidence MVP

## Folder layout

```
myntra-wishlist-growth/
├── app.py                 # Streamlit entry (run this)
├── requirements.txt
├── .env                   # secrets (not committed)
├── docs/                  # project READMEs / briefs
│   ├── 01_overall.md
│   ├── 02_discovery_engine.md
│   ├── 03_slides.md
│   └── 04_mvp.md
├── discovery/             # Part 1 engine
│   ├── scraper.py
│   ├── tagger.py
│   ├── aggregate.py
│   └── data/              # reviews + tagged + opportunity table
├── mvp/                   # Part 5 assistant
│   ├── assistant.py
│   └── data/              # product catalog + images
├── shared/                # config + LLM client
├── survey/                # interview / form helpers
└── tools/                 # optional binaries (e.g. cloudflared)
```

## Run the UI

```powershell
.\pm-env\Scripts\Activate.ps1
streamlit run app.py
```

## Discovery pipeline

**One command (scrape → curate → tag → aggregate):**

```powershell
python discovery/run_pipeline.py
```

The Streamlit app reads the committed gold corpus. Refresh data locally with the pipeline, then restart the app (or push the updated JSON/CSV if you are deploying).

Reuse existing scrape or gold without re-fetching:

```powershell
python discovery/run_pipeline.py --skip-scrape
```

Or step by step:

```powershell
python discovery/scraper.py
python discovery/curate_gold.py
python discovery/tagger.py
python discovery/aggregate.py
```

The app will prefer the curated `gold_reviews.csv` / `gold_tagged_reviews.json` outputs when they exist, and fall back to the raw corpus otherwise. Gold is a rolling corpus (merge / dedupe / cap 1000); `reviews.csv` is a per-run scrape dump.

Config & API keys: edit `shared/config.py` and `.env`.

## Docs

| File | What |
|---|---|
| [docs/01_overall.md](docs/01_overall.md) | Master plan (7 parts) |
| [docs/02_discovery_engine.md](docs/02_discovery_engine.md) | Discovery build steps |
| [docs/03_slides.md](docs/03_slides.md) | Deck rules |
| [docs/04_mvp.md](docs/04_mvp.md) | MVP build pattern |
