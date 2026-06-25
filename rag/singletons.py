from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer
    import chromadb as _chromadb

_embed_model = None
_chroma_client = None


def get_embed_model() -> "SentenceTransformer":
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        from config import EMBEDDING_MODEL
        _embed_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embed_model


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        import chromadb
        from config import CHROMA_PATH
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client
