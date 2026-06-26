

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv
from config import LLM_MODEL

load_dotenv()

def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_key_here":
        raise ValueError("GROQ_API_KEY is not set. Please add it to your .env file.")
    return Groq(api_key=api_key)

def normalize_claim(raw_claim: str) -> list[str]:
    raw_claim = raw_claim.strip()[:500]

    client = _get_client()
    prompt = f"""A user entered this claim: "{raw_claim}"

Generate exactly 3 broad, 1-to-3 word search queries to find news articles about this claim.
IMPORTANT: Do NOT write full sentences. Use extremely broad, simple keywords (e.g., "PTA ATM", "submarine cable", "internet shutdown").
Focus on Pakistani and South Asian media coverage.
Focus on Pakistani and South Asian media coverage.
Return ONLY a valid JSON object with a single key "queries" containing an array of 3 strings.

Example output: {{"queries": ["pakistan blackout", "power failure", "cyberattack rumors"]}}"""

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content.strip()
            
            parsed = json.loads(text)
            queries = parsed.get("queries", [])
            if isinstance(queries, list) and len(queries) >= 1:
                return [str(q) for q in queries[:3]]
        except Exception as e:
            print(f"[NORMALIZER] Attempt {attempt + 1} failed: {e}")

    print("[NORMALIZER] Falling back to raw claim as single query.")
    return [raw_claim]
