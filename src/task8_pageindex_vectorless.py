"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Hướng dẫn:
    1. Đăng ký account tại pageindex.ai
    2. Lấy API key
    3. Upload documents
    4. Query sử dụng PageIndex API
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents():
    """
    Upload toàn bộ markdown documents lên PageIndex.
    """
    if not PAGEINDEX_API_KEY or PAGEINDEX_API_KEY.startswith("pi_") or PAGEINDEX_API_KEY == "":
        raise NotImplementedError("PAGEINDEX_API_KEY chưa được cấu hình hợp lệ.")

    try:
        from pageindex import PageIndex
        pi = PageIndex(api_key=PAGEINDEX_API_KEY)
        
        for md_file in STANDARDIZED_DIR.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            pi.upload(
                content=content,
                metadata={"filename": md_file.name, "type": md_file.parent.name}
            )
            print(f"  ✓ Uploaded: {md_file.name}")
    except Exception as e:
        print(f"⚠ Lỗi khi upload tài liệu lên PageIndex: {e}")
        raise e


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    """
    if not PAGEINDEX_API_KEY or PAGEINDEX_API_KEY.startswith("pi_") or PAGEINDEX_API_KEY == "":
        raise NotImplementedError("PAGEINDEX_API_KEY chưa được cấu hình.")

    try:
        from pageindex import PageIndex
        pi = PageIndex(api_key=PAGEINDEX_API_KEY)
        results = pi.query(query=query, top_k=top_k)
        
        return [
            {
                "content": getattr(r, "text", getattr(r, "content", str(r))),
                "score": getattr(r, "score", 0.5),
                "metadata": getattr(r, "metadata", {}),
                "source": "pageindex"
            }
            for r in results
        ]
    except Exception as e:
        print(f"⚠ Lỗi khi tìm kiếm qua PageIndex: {e}")
        raise e


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("⚠ Hãy set PAGEINDEX_API_KEY trong file .env")
        print("  Đăng ký tại: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        try:
            upload_documents()
            print("\nTest query:")
            results = pageindex_search("hình phạt sử dụng ma tuý", top_k=3)
            for r in results:
                print(f"[{r['score']:.3f}] {r['content'][:100]}...")
        except NotImplementedError as e:
            print(f"Skipped: {e}")

