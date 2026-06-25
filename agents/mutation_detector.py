
import os
import json
import re
import time
from groq import Groq
from dotenv import load_dotenv
from config import CHROMA_COLLECTION, LLM_MODEL
from rag.singletons import get_embed_model, get_chroma_client

load_dotenv()

def _get_llm_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_key_here":
        raise ValueError("GROQ_API_KEY is not set. Please add it to your .env file.")
    return Groq(api_key=api_key)

def detect_mutation(claim: str, early_date_cutoff: str, collection_name: str = CHROMA_COLLECTION) -> dict:
    default_error = {
        "mutation_score": -1,
        "mutation_summary": "Analysis unavailable — not enough data.",
        "early_framing": "",
        "late_framing": "",
        "key_changes": [],
    }

    try:
        collection = get_chroma_client().get_or_create_collection(collection_name)
    except Exception as e:
        print(f"[MUTATION] ChromaDB error: {e}")
        return default_error

    try:
        query_embedding = get_embed_model().encode(claim).tolist()
        results = collection.query(query_embeddings=[query_embedding], n_results=20)
    except Exception as e:
        print(f"[MUTATION] Embedding/query error: {e}")
        return default_error

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    early_chunks, late_chunks = [], []
    for chunk, meta in zip(chunks, metadatas):
        date = str(meta.get("date", ""))[:10]
        label = f"[{meta.get('outlet', 'unknown')} — {date}]\n{chunk}"
        if date and date <= early_date_cutoff:
            early_chunks.append(label)
        else:
            late_chunks.append(label)

    if not early_chunks or not late_chunks:
        return {
            "mutation_score": 0,
            "mutation_summary": "Not enough temporal spread to detect mutation. All articles are from a narrow date range.",
            "early_framing": "",
            "late_framing": "",
            "key_changes": [],
        }

    early_context = "\n\n".join(early_chunks[:5])
    late_context = "\n\n".join(late_chunks[:5])

    prompt = f"""You are a misinformation analyst. Compare how this claim was reported early vs later in the news cycle.

CLAIM: {claim}

EARLY COVERAGE (first few days):
{early_context}

LATE COVERAGE (later days):
{late_context}

Analyze the mutation and respond with ONLY valid JSON (no markdown, no code fences):
{{
    "mutation_score": <number from 1 to 10>,
    "mutation_summary": "<3-4 sentence plain English explanation of what changed>",
    "early_framing": "<one sentence describing the early narrative>",
    "late_framing": "<one sentence describing the late narrative>",
    "key_changes": ["<change 1>", "<change 2>", "<change 3>"]
}}

Scoring guide: 1-3 = story stayed mostly consistent, 4-6 = moderate drift, 7-10 = major distortion."""

    llm = _get_llm_client()

    for attempt in range(2):
        try:
            response = llm.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=600,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r"^```json\s*", "", text)
            text = re.sub(r"^```\s*", "", text)
            text = re.sub(r"\s*```$", "", text).strip()
            parsed = json.loads(text)
            score = float(parsed.get("mutation_score", -1))
            parsed["mutation_score"] = max(0.0, min(10.0, score))
            return parsed
        except Exception as e:
            print(f"[MUTATION] Attempt {attempt + 1} failed: {e}")
            if attempt == 0:
                time.sleep(2)

    return default_error
