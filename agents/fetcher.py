
import requests
import json
import os
import time
import uuid
from datetime import datetime
from config import GDELT_MAX_RECORDS, API_TIMEOUT, MAX_ARTICLES
from dotenv import load_dotenv

load_dotenv()

def fetch_gdelt(query: str, date_from: str, date_to: str) -> list[dict]:
    start = date_from.replace("-", "") + "000000"
    end = date_to.replace("-", "") + "235959"

    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": query,
        "mode": "artlist",
        "maxrecords": GDELT_MAX_RECORDS,
        "startdatetime": start,
        "enddatetime": end,
        "format": "json"
    }

    max_retries = 3
    retry_delay = 15

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=API_TIMEOUT)

            if response.status_code == 429:
                print(f"  [GDELT INFO] Rate limited (429). Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                continue

            response.raise_for_status()

            try:
                data = response.json()
            except Exception:
                if "limit requests" in response.text:
                    print(f"  [GDELT INFO] Rate limit warning text. Retrying in {retry_delay}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    continue
                else:
                    raise ValueError(f"Invalid JSON response from GDELT: {response.text[:200]}")

            articles = data.get("articles", [])

            results = []
            for a in articles:
                title = a.get("title", "").strip()
                url_val = a.get("url", "").strip()
                if not title or not url_val:
                    continue
                raw_date = a.get("seendate", "")
                try:
                    parsed_date = datetime.strptime(raw_date[:8], "%Y%m%d").strftime("%Y-%m-%d")
                except Exception:
                    parsed_date = None

                if not parsed_date:
                    continue

                results.append({
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "outlet": a.get("domain", "unknown"),
                    "date": parsed_date,
                    "url": url_val,
                    "snippet": title,
                    "source_api": "gdelt",
                    "country": a.get("sourcecountry", "unknown")
                })
            return results

        except Exception as e:
            if attempt == max_retries - 1:
                print(f"[GDELT WARNING] {e} - continuing without GDELT results.")
                return []
            else:
                print(f"  [GDELT INFO] Attempt failed: {e}. Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
    return []


def fetch_guardian(query: str, date_from: str, date_to: str) -> list[dict]:
    api_key = os.getenv("GUARDIAN_API_KEY")
    if not api_key or api_key == "your_guardian_key_here":
        print("[GUARDIAN WARNING] No valid GUARDIAN_API_KEY set - skipping The Guardian.")
        return []

    url = "https://content.guardianapis.com/search"
    params = {
        "q": query,
        "from-date": date_from,
        "to-date": date_to,
        "order-by": "relevance",
        "page-size": 50,
        "show-fields": "trailText,bodyText,headline",
        "api-key": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        data = response.json()

        if data.get("response", {}).get("status") != "ok":
            msg = data.get("response", {}).get("message", "unknown error")
            print(f"[GUARDIAN WARNING] {msg} - continuing without Guardian results.")
            return []

        results = []
        for a in data.get("response", {}).get("results", []):
            title = (a.get("webTitle") or "").strip()
            url_val = (a.get("webUrl") or "").strip()
            if not title or not url_val:
                continue

            fields = a.get("fields", {})
            snippet = (fields.get("trailText") or fields.get("bodyText") or title).strip()
            if len(snippet) > 500:
                snippet = snippet[:500]

            raw_date = a.get("webPublicationDate", "")
            parsed_date = raw_date[:10] if raw_date else date_from

            results.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "outlet": "The Guardian",
                "date": parsed_date,
                "url": url_val,
                "snippet": snippet,
                "source_api": "guardian",
                "country": "GB",
            })
        return results

    except Exception as e:
        print(f"[GUARDIAN WARNING] {e} - continuing without Guardian results.")
        return []


def fetch_gnews(query: str, date_from: str, date_to: str) -> list[dict]:
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key or api_key == "your_gnews_key_here":
        print("[GNEWS WARNING] No valid GNEWS_API_KEY set - skipping GNews.")
        return []

    url = "https://gnews.io/api/v4/search"
    params = {
        "q": query,
        "from": f"{date_from}T00:00:00Z",
        "to": f"{date_to}T23:59:59Z",
        "lang": "en",
        "max": 10,
        "sortby": "publishedAt",
        "token": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        data = response.json()

        if "errors" in data:
            print(f"[GNEWS WARNING] {data['errors']} - continuing without GNews results.")
            return []

        results = []
        for a in data.get("articles", []):
            title = (a.get("title") or "").strip()
            url_val = (a.get("url") or "").strip()
            if not title or not url_val:
                continue

            snippet = (a.get("description") or a.get("content") or title).strip()
            if len(snippet) > 500:
                snippet = snippet[:500]

            raw_date = a.get("publishedAt", "")
            parsed_date = raw_date[:10] if raw_date else date_from

            source_name = a.get("source", {}).get("name", "unknown")

            results.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "outlet": source_name,
                "date": parsed_date,
                "url": url_val,
                "snippet": snippet,
                "source_api": "gnews",
                "country": "unknown",
            })
        return results

    except Exception as e:
        print(f"[GNEWS WARNING] {e} - continuing without GNews results.")
        return []


def deduplicate(articles: list[dict]) -> list[dict]:
    seen_urls = set()
    seen_titles = set()
    unique = []
    for a in articles:
        url = a.get("url", "").strip()
        title = a.get("title", "").strip().lower()[:80]

        if not url:
            continue
        if url in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        seen_urls.add(url)
        if title:
            seen_titles.add(title)
        unique.append(a)
    return unique


def fetch_all(queries: list[str], date_from: str, date_to: str) -> list[dict]:
    all_articles = []

    for query in queries:
        print(f"  >> Fetching GDELT: {query}")
        gdelt_results = fetch_gdelt(query, date_from, date_to)
        all_articles.extend(gdelt_results)
        print(f"    {len(gdelt_results)} articles from GDELT")
        time.sleep(5)

        print(f"  >> Fetching Guardian: {query}")
        guardian_results = fetch_guardian(query, date_from, date_to)
        all_articles.extend(guardian_results)
        print(f"    {len(guardian_results)} articles from The Guardian")

        print(f"  >> Fetching GNews: {query}")
        gnews_results = fetch_gnews(query, date_from, date_to)
        all_articles.extend(gnews_results)
        print(f"    {len(gnews_results)} articles from GNews")

    unique = deduplicate(all_articles)

    unique = unique[:MAX_ARTICLES]

    os.makedirs("data", exist_ok=True)
    with open("data/articles_raw.json", "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)

    print(f"\nTotal unique articles fetched: {len(unique)}")
    print("Saved to data/articles_raw.json [OK]")
    return unique
