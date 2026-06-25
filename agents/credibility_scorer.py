
import json
import os
import functools
from urllib.parse import urlparse

@functools.lru_cache(maxsize=1)
def load_ratings() -> dict:
    ratings_path = os.path.join(os.path.dirname(__file__), "..", "data", "outlet_ratings.json")
    ratings_path = os.path.normpath(ratings_path)
    with open(ratings_path, encoding="utf-8") as f:
        return json.load(f)

def get_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc
        return netloc.replace("www.", "").lower()
    except Exception:
        return "unknown"

def score_articles(articles: list[dict]) -> dict:
    try:
        ratings = load_ratings()
    except Exception as e:
        print(f"[CREDIBILITY] Could not load outlet_ratings.json: {e}")
        ratings = {}

    breakdown = {"reliable": 0, "mixed": 0, "tabloid": 0, "unknown": 0}
    outlet_counts: dict[str, int] = {}
    rated_articles = []

    for article in articles:
        domain = get_domain(article.get("url", ""))
        outlet_info = ratings.get(domain)

        if outlet_info:
            rating = outlet_info.get("rating", "unknown")
            outlet_display = outlet_info.get("name", domain)
        else:
            rating = "unknown"
            outlet_display = article.get("outlet", domain)

        if rating not in breakdown:
            rating = "unknown"

        breakdown[rating] += 1
        outlet_counts[outlet_display] = outlet_counts.get(outlet_display, 0) + 1

        rated_articles.append({
            **article,
            "credibility": rating,
            "domain": domain,
            "outlet_display": outlet_display,
        })

    total = len(articles)
    breakdown_pct = {
        k: round(v / total * 100) if total > 0 else 0
        for k, v in breakdown.items()
    }

    top_sources = sorted(outlet_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "breakdown": breakdown,
        "breakdown_pct": breakdown_pct,
        "rated_articles": rated_articles,
        "total": total,
        "top_sources": [{"outlet": o, "count": c} for o, c in top_sources],
    }
