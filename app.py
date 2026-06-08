import streamlit as st
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.task10_generation import generate_with_citation
from src.task9_retrieval_pipeline import retrieve
from src.task4_chunking_indexing import run_pipeline as run_indexing
from src.task2_crawl_news import crawl_all
from src.task3_convert_markdown import convert_all
from src.task1_collect_legal_docs import generate_documents

# Page configurations
st.set_page_config(
    page_title="DrugLaw Search - Công cụ Tìm kiếm RAG",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium dark styling
st.markdown("""
<style>
    /* Dark Theme General Styles */
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Gradient styling */
    .app-header {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        margin-bottom: 5px;
        text-align: center;
    }
    
    .app-subtitle {
        text-align: center;
        color: #9ca3af;
        margin-bottom: 30px;
        font-size: 1.1rem;
    }
    
    /* Result card styling */
    .result-card {
        background-color: #161f30;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #28374d;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s, border-color 0.2s;
    }
    .result-card:hover {
        transform: translateY(-2px);
        border-color: #6366f1;
    }
    
    /* Badge tags */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 8px;
    }
    .badge-legal {
        background-color: #1e3a8a;
        color: #93c5fd;
        border: 1px solid #3b82f6;
    }
    .badge-news {
        background-color: #581c87;
        color: #f3e8ff;
        border: 1px solid #a855f7;
    }
    .badge-hybrid {
        background-color: #064e3b;
        color: #a7f3d0;
        border: 1px solid #10b981;
    }
    .badge-pageindex {
        background-color: #7c2d12;
        color: #ffedd5;
        border: 1px solid #f97316;
    }
    .score-badge {
        background-color: #111827;
        color: #10b981;
        border: 1px solid #10b981;
    }
</style>
""", unsafe_allow_html=True)

# App Title & Header
st.markdown('<div class="app-header">🔍 DrugLaw Search Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Công cụ tìm kiếm thông minh và phân tích pháp luật ma túy & tin tức nghệ sĩ</div>', unsafe_allow_html=True)

# Paths
DATA_DIR = Path(__file__).parent / "data"
VS_PATH = DATA_DIR / "vector_store.json"

# Sidebar settings & helpers
with st.sidebar:
    st.markdown("### ⚙️ Cấu Hình RAG Pipeline")
    
    # Check current system status
    vs_exists = VS_PATH.exists()
    st.markdown(f"**Trạng thái Index:** {'🟢 Sẵn sàng' if vs_exists else '🔴 Chưa khởi tạo'}")
    
    st.markdown("---")
    
    # Model config
    st.markdown("#### 🤖 Mô Hình & Ngưỡng")
    use_reranking = st.toggle("Kích hoạt Reranking (Gemini Flash)", value=True)
    score_threshold = st.slider("Ngưỡng điểm Fallback", min_value=0.0, max_value=1.0, value=0.3, step=0.05,
                                help="Nếu điểm Hybrid cao nhất dưới ngưỡng này, hệ thống sẽ gọi Fallback PageIndex.")
    top_k = st.slider("Số lượng kết quả trích xuất (top_k)", min_value=1, max_value=10, value=5)
    
    st.markdown("---")
    
    # Actions for setting up database
    st.markdown("#### 📂 Quản lý dữ liệu")
    if st.button("🚀 Khởi tạo toàn bộ Dữ liệu", help="Chạy tự động các tác vụ 1-4 để sinh văn bản pháp luật, bài báo, convert và index vào file store."):
        with st.status("Đang thiết lập dữ liệu hệ thống...", expanded=True) as status:
            status.update(label="1. Đang sinh văn bản pháp luật...", state="running")
            generate_documents()
            
            status.update(label="2. Đang crawl thông tin bài báo...", state="running")
            import asyncio
            asyncio.run(crawl_all())
            
            status.update(label="3. Đang chuyển đổi tài liệu sang Markdown...", state="running")
            convert_all()
            
            status.update(label="4. Đang lập chỉ mục (Embedding & Indexing)...", state="running")
            run_indexing()
            
            status.update(label="Hoàn tất khởi tạo dữ liệu!", state="complete")
        st.success("Hệ thống dữ liệu đã sẵn sàng! Bạn có thể bắt đầu tìm kiếm.")
        st.rerun()
        
    st.markdown("---")
    st.caption("DrugLaw Search - Build v2.0 | Advanced Agentic Coding @Google DeepMind")

# Main content
if not vs_exists:
    st.warning("⚠ Hệ thống dữ liệu chưa được khởi tạo. Vui lòng bấm vào nút **'Khởi tạo toàn bộ Dữ liệu'** ở thanh cấu hình bên trái để chuẩn bị tài liệu mẫu và index.")
else:
    # Search input field
    query = st.text_input("✍️ Nhập nội dung câu hỏi hoặc từ khóa tìm kiếm pháp luật...", 
                          placeholder="Ví dụ: Hình phạt cho tội tàng trữ ma túy? hoặc Ca sĩ Chi Dân bị bắt ở đâu?",
                          value="")

    if query:
        with st.spinner("Đang tìm kiếm thông tin và tổng hợp câu trả lời từ RAG..."):
            try:
                # Execute generation with citation (runs Task 9 and Task 10)
                # We overwrite top_k, use_reranking, score_threshold from UI settings
                # Modify retrieval params globally for this thread
                import src.task9_retrieval_pipeline as rp
                rp.SCORE_THRESHOLD = score_threshold
                rp.DEFAULT_TOP_K = top_k
                
                result = generate_with_citation(query, top_k=top_k)
                
                # Render results in tabs
                tab_ans, tab_docs = st.tabs(["💡 Câu trả lời tổng hợp", "📂 Tài liệu trích dẫn"])
                
                with tab_ans:
                    st.markdown("### 🤖 Câu trả lời từ Gemini Flash RAG:")
                    st.write(result["answer"])
                    
                    st.markdown("---")
                    st.caption(f"Phương thức Retrieval chính: **{result['retrieval_source'].upper()}**")
                
                with tab_docs:
                    st.markdown(f"### 📄 Đã trích xuất {len(result['sources'])} tài liệu liên quan:")
                    
                    for idx, src in enumerate(result["sources"], 1):
                        meta = src.get("metadata", {})
                        source_file = meta.get("source", "N/A")
                        doc_type = meta.get("type", "unknown")
                        score = src.get("score", 0.0)
                        ret_method = src.get("source", "hybrid")
                        
                        type_badge = f'<span class="badge badge-legal">Pháp Luật</span>' if doc_type == 'legal' else f'<span class="badge badge-news">Tin Tức</span>'
                        method_badge = f'<span class="badge badge-hybrid">Hybrid</span>' if ret_method == 'hybrid' else f'<span class="badge badge-pageindex">PageIndex Fallback</span>'
                        
                        st.markdown(f"""
                        <div class="result-card">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                                <strong>Đoạn {idx} | File: {source_file}</strong>
                                <div>
                                    {type_badge}
                                    {method_badge}
                                    <span class="badge score-badge">Score: {score:.3f}</span>
                                </div>
                            </div>
                            <div style="font-size:0.95rem; line-height:1.6; color:#e5e7eb;">
                                {src['content']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
            except Exception as e:
                st.error(f"❌ Có lỗi xảy ra trong quá trình xử lý: {e}")
                st.info("Gợi ý: Hãy kiểm tra xem biến môi trường GEMINI_API_KEY trong file `.env` đã được nhập đúng chưa.")
