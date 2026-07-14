#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Tool for SaerixAgent - ChromaDB default embedder (no sentence_transformers)
"""
from langchain_core.tools import tool
import chromadb

CHROMA_DIR = "./rag_db"
COLLECTION_NAME = "osw1_knowledge"
TOP_K = 5

_collection = None

def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=CHROMA_DIR)
        _collection = client.get_collection(COLLECTION_NAME)
    return _collection


@tool
def knowledge_query(query: str, top_k: int = TOP_K) -> str:
    """
    OSW1 veri setinde bilgi arar (RAG).
    Python, ML, kod, yazılım mühendisliği, Wikipedia konularında kullan.
    
    Args:
        query: Arama sorgusu
        top_k: Kaç sonuç (default: 5)
    
    Returns:
        İlgili bağlam metni
    """
    try:
        col = _get_collection()
        results = col.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas"]
        )
        
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        
        if not docs:
            return "Bilgi tabanında ilgili içerik bulunamadı."
        
        parts = []
        for i, (doc, meta) in enumerate(zip(docs, metas)):
            source = meta.get("source", "unknown")
            parts.append(f"[Kaynak {i+1}: {source}]\n{doc}")
        
        return "\n\n---\n\n".join(parts)
    except Exception as e:
        return f"RAG hatası: {e}"


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Python async await nedir"
    print(knowledge_query(q))