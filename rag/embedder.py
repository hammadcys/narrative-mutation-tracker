
import uuid
from config import CHUNK_SIZE, CHROMA_COLLECTION
from rag.singletons import get_embed_model, get_chroma_client


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def embed_articles(articles: list[dict], collection_name: str = CHROMA_COLLECTION) -> None:
    model = get_embed_model()
    client = get_chroma_client()
    collection = client.get_or_create_collection(collection_name)

    ids, embeddings, documents, metadatas = [], [], [], []

    for article in articles:
        text = (article.get("snippet") or article.get("title") or "").strip()
        if not text:
            continue

        chunks = chunk_text(text)
        article_url = article.get("url", "")

        for j, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            embedding = model.encode(chunk).tolist()

            ids.append(chunk_id)
            embeddings.append(embedding)
            documents.append(chunk)
            metadatas.append(
                {
                    "outlet": str(article.get("outlet", "unknown")),
                    "date": str(article.get("date", "")),
                    "url": str(article_url),
                    "title": str(article.get("title", "")),
                    "source_api": str(article.get("source_api", "")),
                }
            )

    if not ids:
        print("[EMBEDDER] No chunks to embed - skipping.")
        return

    batch_size = 100
    for i in range(0, len(ids), batch_size):
        collection.add(
            ids=ids[i : i + batch_size],
            embeddings=embeddings[i : i + batch_size],
            documents=documents[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    print(f"[EMBEDDER] Stored {len(ids)} chunks in ChromaDB collection '{collection_name}' [OK]")
