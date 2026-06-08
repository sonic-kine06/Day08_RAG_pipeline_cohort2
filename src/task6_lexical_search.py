"""
Task 6 — Lexical Search Module (BM25).

Mặc định sử dụng BM25. Nếu dùng phương pháp khác (TF-IDF, Elasticsearch,
Weaviate BM25 built-in), hãy giải thích cơ chế trong buổi demo → +5 bonus.

Cài đặt:
    pip install rank-bm25

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - Formula: score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
"""

from pathlib import Path

from pathlib import Path
import json
from rank_bm25 import BM25Okapi
import numpy as np

# Load corpus từ data/standardized/ hoặc từ vector store
CORPUS: list[dict] = []  
_bm25 = None


def load_corpus() -> list[dict]:
    """Tải corpus từ vector store hoặc tự chunking trên fly."""
    vector_store_path = Path(__file__).parent.parent / "data" / "vector_store.json"
    if vector_store_path.exists():
        try:
            return json.loads(vector_store_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Fallback nếu chưa chạy indexing
    try:
        from .task4_chunking_indexing import load_documents, chunk_documents
        docs = load_documents()
        return chunk_documents(docs)
    except Exception as e:
        print(f"⚠ Không thể load corpus: {e}")
        return []


def get_bm25_index():
    """Lấy hoặc khởi tạo BM25 index và corpus."""
    global CORPUS, _bm25
    if not CORPUS:
        CORPUS = load_corpus()
    if _bm25 is None and CORPUS:
        _bm25 = build_bm25_index(CORPUS)
    return _bm25, CORPUS


def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}
    """
    # Tokenize đơn giản bằng cách lowercase và split cho tiếng Việt
    tokenized_corpus = [doc["content"].lower().split() for doc in corpus]
    return BM25Okapi(tokenized_corpus)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,      # BM25 score
            'metadata': dict
        }
        Sorted by score descending.
    """
    bm25, corpus = get_bm25_index()
    if not bm25 or not corpus:
        return []

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Lấy top_k kết quả có điểm số cao nhất
    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            "content": corpus[idx]["content"],
            "score": float(scores[idx]),
            "metadata": corpus[idx].get("metadata", {})
        })
    
    # Đảm bảo danh sách được sort chính xác theo score giảm dần
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


if __name__ == "__main__":
    # Test
    results = lexical_search("Điều 248 tàng trữ trái phép chất ma tuý", top_k=5)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content'][:100]}...")

