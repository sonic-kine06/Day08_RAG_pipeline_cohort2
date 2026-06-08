"""
Task 7 — Reranking Module.

Chọn 1 trong các phương pháp:
    - Cross-encoder reranker: Jina Reranker v2 (multilingual) hoặc Qwen3-Reranker
    - MMR (Maximal Marginal Relevance): tự implement
    - RRF (Reciprocal Rank Fusion): tự implement

Nếu dùng MMR hoặc RRF, đảm bảo hiểu và giải thích được cơ chế.
"""

from typing import Optional


from typing import Optional
import re
import json

# helper for cosine similarity
from .task5_semantic_search import cosine_similarity


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng Gemini Flash làm Cross-Encoder Reranker.

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by rerank_score descending.
    """
    if not candidates:
        return []

    from .gemini_client import generate_content

    # Tạo prompt yêu cầu Gemini Flash đánh giá độ liên quan của từng đoạn
    prompt = f"""Bạn là chuyên gia đánh giá kết quả tìm kiếm (RAG).
Hãy đánh giá mức độ liên quan của các đoạn văn bản bên dưới đối với câu hỏi của người dùng: "{query}".

Với mỗi đoạn văn bản, hãy chấm điểm mức độ liên quan từ 0.0 (không liên quan chút nào) đến 1.0 (hoàn toàn liên quan và trả lời trực tiếp câu hỏi).
Chỉ trả về duy nhất một danh sách điểm dạng JSON, ví dụ: [0.9, 0.35, 0.8] ứng với thứ tự các đoạn văn bản đầu vào. Không giải thích hay bình luận gì thêm.

Các đoạn văn bản cần chấm điểm:
"""
    for i, c in enumerate(candidates):
        prompt += f"\n--- Đoạn {i} ---\n{c['content']}\n"

    try:
        response = generate_content(prompt, temperature=0.0)
        # Regex tìm chuỗi JSON list [..., ...]
        match = re.search(r'\[\s*[-+]?[0-9]*\.?[0-9]+(?:,\s*[-+]?[0-9]*\.?[0-9]+)*\s*\]', response)
        if match:
            scores = json.loads(match.group(0))
            if len(scores) == len(candidates):
                # Update score cho từng candidate
                for c, s in zip(candidates, scores):
                    c["score"] = float(s)
                
                # Sort và return
                candidates.sort(key=lambda x: x["score"], reverse=True)
                return candidates[:top_k]
    except Exception as e:
        print(f"  ⚠ Lỗi khi rerank bằng Gemini Flash: {e}. Dùng kết quả ban đầu.")

    # Fallback sắp xếp lại theo score ban đầu
    candidates.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return candidates[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))
    """
    if not candidates:
        return []

    # Đảm bảo các candidates đều có vector embedding, nếu thiếu thì sinh mới
    from .gemini_client import get_embedding
    for c in candidates:
        if "embedding" not in c or not c["embedding"]:
            try:
                c["embedding"] = get_embedding(c["content"])
            except Exception:
                c["embedding"] = [0.0] * 768

    selected = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float('-inf')

        for idx in remaining:
            # Relevance đối với query
            relevance = cosine_similarity(query_embedding, candidates[idx]["embedding"])

            # Điểm tương đồng lớn nhất với các tài liệu đã chọn
            max_sim_to_selected = 0.0
            for sel_idx in selected:
                sim = cosine_similarity(candidates[idx]["embedding"], candidates[sel_idx]["embedding"])
                max_sim_to_selected = max(max_sim_to_selected, sim)

            # Công thức tính MMR
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected.append(best_idx)
            remaining.remove(best_idx)

    return [candidates[i] for i in selected]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))
    """
    rrf_scores = {}  # content -> score
    content_map = {}  # content -> full dict

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in content_map:
                content_map[key] = item

    # Sắp xếp giảm dần theo RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = score
        results.append(item)

    return results


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Giao diện reranking hợp nhất.
    """
    if method == "cross_encoder":
        return rerank_cross_encoder(query, candidates, top_k)
    elif method == "mmr":
        from .gemini_client import get_embedding
        try:
            query_embedding = get_embedding(query)
        except Exception:
            query_embedding = [0.0] * 768
        return rerank_mmr(query_embedding, candidates, top_k)
    elif method == "rrf":
        return rerank_rrf([candidates], top_k)
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    # Test với dummy data
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý", "score": 0.8, "metadata": {}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý", "score": 0.7, "metadata": {}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ", "score": 0.6, "metadata": {}},
    ]
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=2)
    for r in results:
        print(f"[{r['score']:.3f}] {r['content']}")

