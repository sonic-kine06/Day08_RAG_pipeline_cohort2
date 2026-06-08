"""
Task 5 — Semantic Search Module.

Viết module tìm kiếm ngữ nghĩa (dense retrieval) trên vector store.

Yêu cầu:
    - Input: query string + top_k
    - Output: danh sách chunks có score, sorted descending
    - Phải tương thích với embedding model và vector store ở Task 4
"""


import json
from pathlib import Path

VECTOR_STORE_PATH = Path(__file__).parent.parent / "data" / "vector_store.json"


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Tính cosine similarity giữa 2 vector."""
    try:
        import numpy as np
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm_v1 * norm_v2))
    except (ImportError, Exception):
        # Fallback sang thuần Python nếu không import được numpy
        dot = sum(x * y for x, y in zip(v1, v2))
        norm_v1 = sum(x * x for x in v1) ** 0.5
        norm_v2 = sum(y * y for y in v2) ** 0.5
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        return dot / (norm_v1 * norm_v2)


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm ngữ nghĩa sử dụng vector similarity với Gemini embeddings.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict
        }
    """
    if not VECTOR_STORE_PATH.exists():
        print("⚠ Vector store chưa được xây dựng. Hãy chạy Task 4 trước.")
        return []

    try:
        chunks = json.loads(VECTOR_STORE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠ Lỗi khi load vector store: {e}")
        return []

    from .gemini_client import get_embedding
    try:
        query_embedding = get_embedding(query)
    except Exception as e:
        print(f"⚠ Không thể sinh embedding cho query (có thể chưa set API Key): {e}")
        return []

    results = []
    for chunk in chunks:
        if "embedding" in chunk and chunk["embedding"]:
            score = cosine_similarity(query_embedding, chunk["embedding"])
            results.append({
                "content": chunk["content"],
                "score": score,
                "metadata": chunk.get("metadata", {})
            })

    # Sắp xếp giảm dần theo điểm tương đồng
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    # Test
    results = semantic_search("hình phạt cho tội tàng trữ ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

