"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (Weaviate khuyến cáo)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến
    - MarkdownHeaderTextSplitter: tốt cho file có heading
    - SemanticChunker: dùng embedding để tách (nâng cao)

Embedding model options:
    - sentence-transformers/all-MiniLM-L6-v2 (384 dim, nhẹ)
    - BAAI/bge-m3 (1024 dim, multilingual, tốt cho tiếng Việt)
    - OpenAI text-embedding-3-small (1536 dim, API)

Vector store options:
    - Weaviate (khuyến cáo: hỗ trợ hybrid search built-in)
    - ChromaDB (đơn giản, local)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers weaviate-client
"""

from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# TODO: Chọn chunking strategy và giải thích vì sao
CHUNK_SIZE = 500        # Vì sao chọn 500? ...
CHUNK_OVERLAP = 50      # Vì sao chọn 50? ...
CHUNKING_METHOD = "recursive"  # "recursive" | "markdown_header" | "semantic"

# TODO: Chọn embedding model và giải thích
EMBEDDING_MODEL = "BAAI/bge-m3"  # Vì sao? Multilingual, tốt cho tiếng Việt
EMBEDDING_DIM = 1024

# TODO: Chọn vector store
VECTOR_STORE = "weaviate"  # "weaviate" | "chromadb" | "faiss"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

import json
from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# CHUNK_SIZE = 500: Chọn 500 ký tự vì độ dài này tương đương khoảng 2-3 câu dài tiếng Việt,
# giúp giữ trọn vẹn ngữ nghĩa của một điều luật hoặc một đoạn tin tức mà không làm quá tải
# context length của LLM hoặc gây loãng thông tin.
CHUNK_SIZE = 500        

# CHUNK_OVERLAP = 50: Chọn overlap là 50 để đảm bảo các câu từ bị ngắt ở ranh giới các chunk
# vẫn được kết nối liền mạch, không làm mất ngữ cảnh chuyển tiếp.
CHUNK_OVERLAP = 50      
CHUNKING_METHOD = "recursive"

# Sử dụng mô hình text-embedding-004 của Gemini vì hiệu năng tốt, hỗ trợ tiếng Việt xuất sắc,
# và đúng theo yêu cầu sử dụng API của Gemini từ người dùng.
EMBEDDING_MODEL = "text-embedding-004"  
EMBEDDING_DIM = 768

VECTOR_STORE = "local_json"  # Sử dụng file JSON cục bộ làm Vector Store để ổn định nhất


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    documents = []
    if not STANDARDIZED_DIR.exists():
        print(f"⚠ Thư mục {STANDARDIZED_DIR} không tồn tại.")
        return documents

    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file.as_posix()) else "news"
        documents.append({
            "content": content,
            "metadata": {"source": md_file.name, "type": doc_type}
        })
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo RecursiveCharacterTextSplitter.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(splits):
            chunks.append({
                "content": chunk_text,
                "metadata": {**doc["metadata"], "chunk_index": i}
            })
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng Gemini Embedding API.
    """
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent))
    from gemini_client import get_embedding

    print(f"Embedding {len(chunks)} chunks using Gemini text-embedding-004 API...")
    for i, chunk in enumerate(chunks, 1):
        if i % 5 == 0 or i == len(chunks):
            print(f"  - Embedded {i}/{len(chunks)} chunks...")
        chunk["embedding"] = get_embedding(chunk["content"])
    return chunks


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store cục bộ dạng file JSON.
    """
    vector_store_path = Path(__file__).parent.parent / "data" / "vector_store.json"
    vector_store_path.parent.mkdir(parents=True, exist_ok=True)
    vector_store_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Đã index thành công vào: {vector_store_path}")


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    try:
        chunks = embed_chunks(chunks)
        print(f"✓ Embedded {len(chunks)} chunks")

        index_to_vectorstore(chunks)
        print("✓ Indexed to vector store")
    except Exception as e:
        print(f"⚠ Lỗi khi embed / index (có thể chưa set GEMINI_API_KEY): {e}")


if __name__ == "__main__":
    run_pipeline()
