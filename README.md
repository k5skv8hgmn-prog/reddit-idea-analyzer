# Reddit Idea Analyzer

A Python tool that scrapes live posts from entrepreneurship subreddits, analyzes them with the Anthropic Claude API, and automatically generates business plans for high-scoring ideas.

Built by [k5skv8hgmn-prog](https://github.com/k5skv8hgmn-prog)

---

## What It Does

Each time you run it, the tool:

1. Pulls the latest posts from r/Entrepreneur, r/startup, r/SideProject, and r/smallbusiness
2. Filters out low-engagement posts below a score threshold
3. Sends each post to Claude Haiku to extract:
   - The core startup idea
   - A plain-English summary
   - Sentiment (Positive / Negative / Neutral)
   - Category (Idea Validation, Funding, Marketing, etc.)
4. For posts scoring 10+, automatically generates a full business plan including:
   - Problem statement
   - Target market
   - Revenue model
   - Competitors
   - Competitive moat
   - Concrete next steps
5. Saves results to a timestamped `.txt` and `.csv` file for easy review

---

## Example Output

```
======================================================================
  r/SideProject  |  2026-06-24 18:37 UTC  |  Score: 24
----------------------------------------------------------------------
  TITLE    : I built a tool that turns recipe URLs into clean, editable recipes
  IDEA     : A web tool that extracts recipes from bloated websites into clean, editable cards
  SUMMARY  : The creator built Recipe Decipher to solve cluttered recipe websites by offering
              a URL-to-clean-recipe conversion tool. They've launched the MVP and are seeking
              candid user feedback on whether the value proposition is clear.
  SENTIMENT: Positive  |  CATEGORY: Idea Validation
  URL      : https://reddit.com/r/SideProject/...

  ** BUSINESS PLAN (Score 24 >= 10) **
  PROBLEM      : Recipe websites bury content in ads and bloated pages.
  TARGET MARKET: Home cooks who frequently save and reference recipes online.
  REVENUE MODEL: Freemium SaaS with premium library and sharing features.
  COMPETITORS  : Paprika, Notion, copy-pasting into Google Docs.
  MOAT         : AI-powered extraction that works across any recipe site format.
  NEXT STEPS   : 1) Interview 10 home cooks. 2) Launch on Product Hunt. 3) Add recipe tagging.
======================================================================
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/k5skv8hgmn-prog/reddit-idea-analyzer.git
cd reddit-idea-analyzer
```

### 2. Install dependencies

```bash
pip install praw anthropic python-dotenv
```

### 3. Create a `.env` file

Create a file called `.env` in the project folder with the following:

```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=reddit_analyzer/1.0
ANTHROPIC_API_KEY=your_anthropic_api_key
```

**Getting your Reddit API credentials:**
- Go to reddit.com/prefs/apps
- Click "Create app" → select "script"
- Copy the client ID and secret

**Getting your Anthropic API key:**
- Go to console.anthropic.com
- Navigate to API Keys → Create Key
- Claude Haiku is used by default (very low cost — ~$0.01 per full run)

### 4. Run the tool

```bash
python WhatGPTThinks.py
```

---

## Configuration

All settings are at the top of `WhatGPTThinks.py` and easy to adjust:

| Setting | Default | Description |
|---|---|---|
| `SUBREDDITS` | 4 subreddits | Which communities to scrape |
| `POST_LIMIT` | 10 | Posts fetched per subreddit |
| `POST_SORT` | `new` | Sort by `new`, `top`, or `hot` |
| `MIN_SCORE` | 2 | Skip posts below this upvote count |
| `BUSINESS_PLAN_SCORE` | 10 | Generate business plan at this score+ |
| `CATEGORY_FILTER` | `[]` (all) | Filter to specific categories only |

**Example: Show only Idea Validation posts with business plans for score 25+**
```python
CATEGORY_FILTER     = ["Idea Validation", "Success Story"]
BUSINESS_PLAN_SCORE = 25
```

---

## Output Files

Every run saves two files to the project folder:

- `reddit_results_YYYY-MM-DD_HH-MM.txt` — human-readable formatted output
- `reddit_results_YYYY-MM-DD_HH-MM.csv` — spreadsheet with all fields as columns, openable in Excel

Each run creates new timestamped files so nothing is overwritten.

---

## Tech Stack

- **Python 3.10+**
- **PRAW** — Reddit API wrapper
- **Anthropic Python SDK** — Claude Haiku for analysis and business plan generation
- **python-dotenv** — secure credential management

---

## Project Structure

```
reddit-idea-analyzer/
├── WhatGPTThinks.py   # Main script
├── .env               # Your API keys (never committed)
├── .gitignore         # Ensures .env stays local
└── README.md          # This file
```

---

## Notes

- The `.env` file is excluded from this repository intentionally — never commit API keys
- Cost per full run is approximately $0.01 using Claude Haiku
- Reddit API credentials are free at reddit.com/prefs/apps
