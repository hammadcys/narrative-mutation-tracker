
import os
from groq import Groq
from dotenv import load_dotenv
from config import TOP_K_RETRIEVAL, CHROMA_COLLECTION, LLM_MODEL
from rag.singletons import get_embed_model, get_chroma_client

load_dotenv()

def _get_llm_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_groq_key_here":
        raise ValueError("GROQ_API_KEY is not set. Please add it to your .env file.")
    return Groq(api_key=api_key)

def retrieve_and_answer(question: str, collection_name: str = CHROMA_COLLECTION) -> dict:
    try:
        collection = get_chroma_client().get_or_create_collection(collection_name)
    except Exception as e:
        return {"answer": f"Database error: {e}", "sources": []}

    try:
        query_embedding = get_embed_model().encode(question).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=TOP_K_RETRIEVAL,
        )
    except Exception as e:
        return {"answer": f"Retrieval error: {e}", "sources": []}

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]

    if not chunks:
        return {"answer": "No relevant articles found in the database.", "sources": []}

    context = ""
    for chunk, meta in zip(chunks, metadatas):
        context += f"\n[{meta.get('outlet', 'Unknown')} - {meta.get('date', 'unknown date')}]\n{chunk}\n"

    prompt = f"""You are a fact-checking assistant specialising in South Asian media.
Answer the question below using ONLY the provided news excerpts.
For every claim you make, cite the outlet name and date in brackets like [Dawn News - 2023-05-09].
If the context does not contain enough information to answer, say: "Insufficient data in retrieved articles."
Do NOT use any knowledge outside the provided context.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    try:
        llm = _get_llm_client()
        response = llm.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=800,
        )
        answer_text = response.choices[0].message.content.strip()
    except Exception as e:
        answer_text = f"LLM error: {e}"

    return {"answer": answer_text, "sources": metadatas}
