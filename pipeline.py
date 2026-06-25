
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from agents.normalizer import normalize_claim
from agents.fetcher import fetch_all
from agents.timeline import build_timeline
from agents.mutation_detector import detect_mutation
from agents.credibility_scorer import score_articles
from rag.embedder import embed_articles
from rag.retriever import retrieve_and_answer
from datetime import datetime, timedelta
import chromadb
from config import CHROMA_PATH, CHROMA_COLLECTION

def run_pipeline(claim: str, date_from: str = None, date_to: str = None) -> dict:

    if not date_to:
        date_to = datetime.today().strftime("%Y-%m-%d")
    if not date_from:
        date_from = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")

    claim = claim.strip()[:500]

    print(f"\n{'='*60}")
    print(f"  MISINFORMATION TRAIL TRACKER")
    print(f"{'='*60}")
    print(f"  Claim:      {claim}")
    print(f"  Date range: {date_from} >> {date_to}")
    print(f"{'='*60}\n")

    print("[1/6] Normalizing claim with Groq...")
    queries = normalize_claim(claim)
    print(f"  Queries generated: {queries}\n")

    print("[2/6] Fetching articles from GDELT + NewsAPI...")
    articles = fetch_all(queries, date_from, date_to)

    if not articles:
        return {"error": "No articles found for this claim and date range. Try broadening the date range or rephrasing the claim."}

    print(f"\n[3/6] Embedding {len(articles)} articles into ChromaDB...")

    try:
        chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        try:
            chroma_client.delete_collection(CHROMA_COLLECTION)
        except Exception:
            pass
        embed_articles(articles)
        print("  Embedded into collection [OK].")
    except Exception as embed_err:
        print(f"[PIPELINE] Embedding failed: {embed_err}")
        raise

    print("\n[4/6] Building timeline...")
    timeline = build_timeline(articles)
    origin = timeline.get("origin")
    if origin:
        print(f"  Origin: {origin.get('outlet')} - {origin.get('date')}")
        print(f"  '{origin.get('title')}'")

    print("\n[5/6] Detecting narrative mutation...")

    bucket_0 = timeline.get("buckets", [{}])[0].get("articles", [])
    if bucket_0:
        early_cutoff = str(bucket_0[-1].get("date", date_from))[:10]
    else:
        early_cutoff = date_from
    mutation = detect_mutation(claim, early_cutoff)
    score = mutation.get("mutation_score", -1)
    if score >= 0:
        flag = "HIGH DISTORTION" if score >= 7 else "MODERATE" if score >= 4 else "LOW"
        print(f"  Mutation score: {score}/10  [{flag}]")

    print("\n[6/6] Scoring source credibility...")
    credibility = score_articles(articles)
    bd = credibility["breakdown"]
    print(f"  Reliable: {bd['reliable']}  Mixed: {bd['mixed']}  Unknown: {bd['unknown']}")

    print(f"\n{'='*60}")
    print("  Pipeline complete.")
    print(f"{'='*60}\n")

    return {
        "claim": claim,
        "date_from": date_from,
        "date_to": date_to,
        "queries_used": queries,
        "total_articles": len(articles),
        "timeline": timeline,
        "mutation": mutation,
        "credibility": credibility,
    }

def ask_question(question: str) -> dict:
    return retrieve_and_answer(question)

if __name__ == "__main__":
    import json

    result = run_pipeline(
        claim="Imran Khan arrested May 2023",
        date_from="2023-05-09",
        date_to="2023-05-25",
    )
    print(json.dumps(result, indent=2, default=str))
