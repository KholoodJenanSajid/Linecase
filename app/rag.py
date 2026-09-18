from __future__ import annotations

import os
from pathlib import Path

from app.config import api_key

CORPUS_DIR = Path(__file__).resolve().parents[1] / "data" / "corpus"

_DOCS: list[dict] | None = None
_COL = None


def _docs() -> list[dict]:
    global _DOCS
    if _DOCS is None:
        _DOCS = []
        for path in sorted(CORPUS_DIR.glob("*.md")):
            _DOCS.append(
                {
                    "source": path.name,
                    "text": path.read_text(encoding="utf-8"),
                }
            )
    return _DOCS


def _chroma():
    """Vector store when a key is usable; None means fall back to keyword search."""
    global _COL
    if _COL is not None:
        return _COL
    key = api_key()
    if key is None:
        return None
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        model = os.environ.get("EMBEDDING_MODEL", "models/text-embedding-004")
        ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=key,
            model_name=model.replace("models/", ""),
        )
        client = chromadb.Client()
        col = client.get_or_create_collection(name="apex_plant", embedding_function=ef)
        if col.count() == 0:
            rows = _docs()
            col.add(
                documents=[r["text"] for r in rows],
                ids=[Path(r["source"]).stem for r in rows],
                metadatas=[{"source": r["source"]} for r in rows],
            )
    except Exception:
        return None
    _COL = col
    return col


def collection_count() -> int:
    return len(_docs())


def retrieve(query: str, k: int = 4) -> list[dict]:
    col = _chroma()
    if col is not None:
        n = min(k, max(col.count(), 1))
        res = col.query(query_texts=[query], n_results=n)
        hits = []
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            hits.append(
                {
                    "source": (meta or {}).get("source", "unknown"),
                    "text": doc,
                    "distance": dist,
                }
            )
        return hits
    tokens = {t.lower() for t in query.split() if len(t) > 3}
    ranked = []
    for row in _docs():
        text_l = row["text"].lower()
        score = sum(1 for t in tokens if t in text_l)
        ranked.append((score, row))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [
        {"source": r["source"], "text": r["text"], "distance": None}
        for _, r in ranked[:k]
    ]
