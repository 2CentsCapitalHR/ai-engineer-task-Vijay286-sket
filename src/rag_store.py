from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Any

import chromadb
from chromadb.utils import embedding_functions


@dataclass
class RAGConfig:
    collection_name: str = "adgm_refs"
    persist_dir: str = ".rag_chroma"


class RAGStore:
    def __init__(self, cfg: RAGConfig | None = None) -> None:
        self.cfg = cfg or RAGConfig()
        os.makedirs(self.cfg.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.cfg.persist_dir)
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.client.get_or_create_collection(
            name=self.cfg.collection_name,
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedder,
        )

    def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]] | None = None, ids: List[str] | None = None) -> None:
        if not texts:
            return
        if metadatas is None:
            metadatas = [{} for _ in texts]
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        self.collection.add(documents=texts, metadatas=metadatas, ids=ids)

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not query.strip():
            return []
        res = self.collection.query(query_texts=[query], n_results=k)
        out: List[Dict[str, Any]] = []
        for i in range(len(res.get("ids", [[]])[0])):
            out.append({
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "metadata": res["metadatas"][0][i],
                "distance": res["distances"][0][i] if "distances" in res else None,
            })
        return out


