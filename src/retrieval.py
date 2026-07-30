from typing import List, Dict
from src import llm, config
from src.vector_db import VectorDB

def search(question: str, top_k: int = None) -> List[Dict]:
    """
    Tìm kiếm và lấy ra top_k tài liệu (documents) phù hợp nhất với câu hỏi.
    """
    if top_k is None:
        top_k = config.TOP_K
        
    db = VectorDB()
    if not db.load_index():
        return []
        
    try:
        # Tạo vector cho câu hỏi
        query_vector = llm.generate_embedding(question)
    except Exception as e:
        print(f"Lỗi khi tạo embedding cho câu hỏi: {e}")
        return []
        
    # Tìm kiếm trên cơ sở dữ liệu vector
    results = db.similarity_search(query_vector, top_k=top_k)
    return [metadata for distance, metadata in results]
