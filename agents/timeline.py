

from datetime import datetime

def parse_date(d: str) -> datetime:
    for fmt in ["%Y-%m-%d", "%Y%m%d"]:
        try:
            return datetime.strptime(str(d)[:10], fmt)
        except Exception:
            pass
    return datetime.min

def build_timeline(articles: list[dict]) -> dict:

    dated = [a for a in articles if a.get("date")]
    sorted_articles = sorted(dated, key=lambda a: parse_date(a["date"]))

    if not sorted_articles:
        return {"origin": None, "origin_date": None, "buckets": [], "total_count": 0}

    origin = sorted_articles[0]
    origin_date = parse_date(origin["date"])

    buckets = [
        {"label": "Days 1–3 (Origin)", "articles": []},
        {"label": "Days 4–7 (Spread)", "articles": []},
        {"label": "Day 8+ (Amplification)", "articles": []},
    ]

    for article in sorted_articles:
        article_date = parse_date(article["date"])
        delta = (article_date - origin_date).days

        if delta <= 2:
            buckets[0]["articles"].append(article)
        elif delta <= 6:
            buckets[1]["articles"].append(article)
        else:
            buckets[2]["articles"].append(article)

    return {
        "origin": origin,
        "origin_date": origin["date"],
        "buckets": buckets,
        "total_count": len(sorted_articles),
    }
