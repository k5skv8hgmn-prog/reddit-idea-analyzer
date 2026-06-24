"""
Reddit Post Analyzer — powered by Anthropic Claude
Fetches posts from multiple subreddits and extracts:
  - Startup idea / problem being solved
  - General summary
  - Sentiment + category tag
  - Business plan (for high-scoring posts)

Setup:
    pip install praw anthropic python-dotenv
"""

import os
import csv
import time
import datetime
import praw
import anthropic
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

load_dotenv()

SUBREDDITS      = ["Entrepreneur", "startup", "SideProject", "smallbusiness"]
POST_LIMIT      = 10      # posts to fetch per subreddit
POST_SORT       = "new"   # "new" | "top" | "hot"
MAX_BODY_LEN    = 1500    # truncate long posts before sending to Claude
DELAY           = 1       # seconds between API calls

# ── Filters ───────────────────────────────────────────────────────────────────

MIN_SCORE           = 2   # skip posts below this score (0 = no filter)
BUSINESS_PLAN_SCORE = 10  # generate a business plan for posts at or above this score

CATEGORY_FILTER = []      # leave empty [] to show ALL categories
                          # or list categories to show only those, e.g.:
                          # ["Idea Validation", "Success Story", "Resource"]

# ── Clients ───────────────────────────────────────────────────────────────────

reddit = praw.Reddit(
    client_id     = os.getenv("REDDIT_CLIENT_ID"),
    client_secret = os.getenv("REDDIT_CLIENT_SECRET"),
    user_agent    = os.getenv("REDDIT_USER_AGENT", "reddit_analyzer/1.0"),
)

claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── Claude: Post Analysis ─────────────────────────────────────────────────────

ANALYSIS_PROMPT = """You are an analyst reviewing posts from entrepreneurship and startup subreddits.
For each post, extract and return EXACTLY the following fields, one per line:

IDEA: A one-sentence description of the startup idea or core problem being discussed.
SUMMARY: A 2-3 sentence plain-English summary of the post.
SENTIMENT: One word only — Positive, Negative, or Neutral.
CATEGORY: One tag only from this list: Idea Validation, Hiring, Funding, Marketing, Operations, Rant, Success Story, Question, Resource, Other.

If the post is too vague to extract an idea, write "N/A" for IDEA.
Do not include any other text, preamble, or explanation."""

def analyze_post(title: str, body: str) -> dict:
    content = f"TITLE: {title}\n\nBODY: {body[:MAX_BODY_LEN]}" if body else f"TITLE: {title}\n\nBODY: (no body text)"
    try:
        message = claude.messages.create(
            model="claude-haiku-4-5",
            max_tokens=300,
            system=ANALYSIS_PROMPT,
            messages=[{"role": "user", "content": content}]
        )
        return parse_analysis(message.content[0].text.strip())
    except Exception as e:
        return {"idea": "Error", "summary": f"Claude error: {e}", "sentiment": "N/A", "category": "N/A"}

def parse_analysis(raw: str) -> dict:
    result = {"idea": "N/A", "summary": "N/A", "sentiment": "N/A", "category": "N/A"}
    for line in raw.splitlines():
        if line.startswith("IDEA:"):
            result["idea"]      = line.replace("IDEA:", "").strip()
        elif line.startswith("SUMMARY:"):
            result["summary"]   = line.replace("SUMMARY:", "").strip()
        elif line.startswith("SENTIMENT:"):
            result["sentiment"] = line.replace("SENTIMENT:", "").strip()
        elif line.startswith("CATEGORY:"):
            result["category"]  = line.replace("CATEGORY:", "").strip()
    return result

# ── Claude: Business Plan ─────────────────────────────────────────────────────

BUSINESS_PLAN_PROMPT = """You are a startup advisor. Based on the Reddit post below, generate a concise business plan.
Return EXACTLY these fields, one per line:

PROBLEM: One sentence describing the core problem being solved.
TARGET MARKET: The specific customer segment who would pay for this.
REVENUE MODEL: How this business would make money (e.g. SaaS, marketplace, one-time purchase).
COMPETITORS: 2-3 existing competitors or alternatives people use today.
MOAT: The key advantage that would make this hard to copy.
NEXT STEPS: Three concrete first steps numbered 1) 2) 3).

Do not include any other text, preamble, or explanation."""

def generate_business_plan(title: str, body: str, idea: str, summary: str) -> dict:
    content = f"TITLE: {title}\n\nIDEA: {idea}\n\nSUMMARY: {summary}\n\nFULL POST: {body[:MAX_BODY_LEN]}"
    try:
        message = claude.messages.create(
            model="claude-haiku-4-5",
            max_tokens=600,
            system=BUSINESS_PLAN_PROMPT,
            messages=[{"role": "user", "content": content}]
        )
        return parse_business_plan(message.content[0].text.strip())
    except Exception as e:
        return {
            "bp_problem":      f"Error: {e}",
            "bp_target":       "N/A",
            "bp_revenue":      "N/A",
            "bp_competitors":  "N/A",
            "bp_moat":         "N/A",
            "bp_next_steps":   "N/A",
        }

def parse_business_plan(raw: str) -> dict:
    result = {
        "bp_problem":     "N/A",
        "bp_target":      "N/A",
        "bp_revenue":     "N/A",
        "bp_competitors": "N/A",
        "bp_moat":        "N/A",
        "bp_next_steps":  "N/A",
    }
    for line in raw.splitlines():
        if line.startswith("PROBLEM:"):
            result["bp_problem"]     = line.replace("PROBLEM:", "").strip()
        elif line.startswith("TARGET MARKET:"):
            result["bp_target"]      = line.replace("TARGET MARKET:", "").strip()
        elif line.startswith("REVENUE MODEL:"):
            result["bp_revenue"]     = line.replace("REVENUE MODEL:", "").strip()
        elif line.startswith("COMPETITORS:"):
            result["bp_competitors"] = line.replace("COMPETITORS:", "").strip()
        elif line.startswith("MOAT:"):
            result["bp_moat"]        = line.replace("MOAT:", "").strip()
        elif line.startswith("NEXT STEPS:"):
            result["bp_next_steps"]  = line.replace("NEXT STEPS:", "").strip()
    return result

# ── Reddit Fetching ───────────────────────────────────────────────────────────

def fetch_posts(subreddit_name: str) -> list:
    posts   = []
    sub     = reddit.subreddit(subreddit_name)
    feed    = getattr(sub, POST_SORT)(limit=POST_LIMIT)
    skipped = 0

    for post in feed:
        if post.score < MIN_SCORE:
            skipped += 1
            continue

        created  = datetime.datetime.fromtimestamp(post.created_utc, datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
        body     = post.selftext.strip() if post.selftext and post.selftext != "[removed]" else ""
        analysis = analyze_post(post.title, body)
        time.sleep(DELAY)

        if CATEGORY_FILTER and analysis["category"] not in CATEGORY_FILTER:
            continue

        # Generate business plan for high-scoring posts
        bp = {}
        if post.score >= BUSINESS_PLAN_SCORE and analysis["idea"] != "N/A":
            print(f"     Generating business plan for: {post.title[:50]}...")
            bp = generate_business_plan(post.title, body, analysis["idea"], analysis["summary"])
            time.sleep(DELAY)

        posts.append({
            "subreddit": subreddit_name,
            "title":     post.title,
            "created":   created,
            "url":       f"https://reddit.com{post.permalink}",
            "score":     post.score,
            **analysis,
            **bp,
        })

    if skipped:
        print(f"     (skipped {skipped} posts below score threshold of {MIN_SCORE})")

    return posts

# ── Output ────────────────────────────────────────────────────────────────────

def format_post(post: dict) -> str:
    lines = [
        f"\n{'=' * 70}",
        f"  r/{post['subreddit']}  |  {post['created']}  |  Score: {post['score']}",
        f"{'-' * 70}",
        f"  TITLE    : {post['title']}",
        f"  IDEA     : {post['idea']}",
        f"  SUMMARY  : {post['summary']}",
        f"  SENTIMENT: {post['sentiment']}  |  CATEGORY: {post['category']}",
        f"  URL      : {post['url']}",
    ]

    if post.get("bp_problem"):
        lines += [
            f"\n  ** BUSINESS PLAN (Score {post['score']} >= {BUSINESS_PLAN_SCORE}) **",
            f"  PROBLEM      : {post['bp_problem']}",
            f"  TARGET MARKET: {post['bp_target']}",
            f"  REVENUE MODEL: {post['bp_revenue']}",
            f"  COMPETITORS  : {post['bp_competitors']}",
            f"  MOAT         : {post['bp_moat']}",
            f"  NEXT STEPS   : {post['bp_next_steps']}",
        ]

    return "\n".join(lines)

def save_txt(all_posts: list, path: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"Reddit Analyzer — Run at {timestamp}\n")
        if CATEGORY_FILTER:
            f.write(f"Category filter : {', '.join(CATEGORY_FILTER)}\n")
        f.write(f"Min score       : {MIN_SCORE}\n")
        f.write(f"Business plan at: {BUSINESS_PLAN_SCORE}+ score\n")
        f.write(f"{'=' * 70}\n")
        for post in all_posts:
            f.write(format_post(post) + "\n")
        f.write(f"\n{'=' * 70}\n")
    print(f"  TXT saved : {path}")

def save_csv(all_posts: list, path: str):
    fields = [
        "subreddit", "title", "score", "created", "sentiment", "category",
        "idea", "summary",
        "bp_problem", "bp_target", "bp_revenue", "bp_competitors", "bp_moat", "bp_next_steps",
        "url"
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_posts)
    print(f"  CSV saved : {path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"\nFetching up to {POST_LIMIT} {POST_SORT.upper()} posts from: {', '.join('r/' + s for s in SUBREDDITS)}")
    print(f"Filters — Min score: {MIN_SCORE}  |  Business plan at: {BUSINESS_PLAN_SCORE}+  |  Categories: {CATEGORY_FILTER if CATEGORY_FILTER else 'All'}")
    print("Analyzing with Claude Haiku...\n")

    all_posts = []
    for subreddit in SUBREDDITS:
        try:
            print(f"  -> Pulling r/{subreddit}...")
            posts = fetch_posts(subreddit)
            all_posts.extend(posts)
            print(f"     {len(posts)} posts kept")
        except Exception as e:
            print(f"  X Failed to fetch r/{subreddit}: {e}")

    print(f"\n{'=' * 70}")
    print(f"  RESULTS: {len(all_posts)} posts after filters")
    print(f"{'=' * 70}")

    for post in all_posts:
        print(format_post(post))

    print(f"\n{'=' * 70}\n")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp  = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    save_txt(all_posts, os.path.join(script_dir, f"reddit_results_{timestamp}.txt"))
    save_csv(all_posts, os.path.join(script_dir, f"reddit_results_{timestamp}.csv"))

if __name__ == "__main__":
    main()