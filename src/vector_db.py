import os
import json
import faiss
import numpy as np
from typing import List, Dict, Tuple, Optional

class VectorDB:
    def __init__(self, index_path: str = "data/discord/faiss.index", metadata_path: str = "data/discord/metadata.json"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index: Optional[faiss.Index] = None
        # metadata lưu trữ ánh xạ từ ID (số nguyên) sang một dictionary chứa thông tin chi tiết
        self.metadata: Dict[int, Dict] = {}

    def create_index(self, dimension: int):
        """
        Khởi tạo một index rỗng sử dụng thuật toán L2 (Euclidean distance).
        """
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = {}
        
    def add_embeddings(self, embeddings: List[List[float]], metadata_list: List[Dict]):
        """
        Thêm danh sách các vector nhúng (embeddings) và metadata tương ứng vào index.
        """
        if self.index is None:
            raise ValueError("Index chưa được tạo hoặc chưa được tải (load) lên.")
            
        start_id = len(self.metadata)
        
        # Thêm vector vào cơ sở dữ liệu FAISS
        vectors = np.array(embeddings, dtype=np.float32)
        self.index.add(vectors)
        
        # Lưu lại siêu dữ liệu (metadata)
        for i, meta in enumerate(metadata_list):
            self.metadata[start_id + i] = meta

    def save_index(self):
        """
        Lưu FAISS index và file metadata xuống ổ đĩa.
        """
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            # json chỉ hỗ trợ key là string, nên ta phải ép kiểu int -> str trước khi lưu
            json.dump({str(k): v for k, v in self.metadata.items()}, f, ensure_ascii=False, indent=2)

    def load_index(self) -> bool:
        """
        Tải FAISS index và file metadata từ ổ cứng lên bộ nhớ. Trả về True nếu thành công.
        """
        if not os.path.exists(self.index_path) or not os.path.exists(self.metadata_path):
            return False
            
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Chuyển đổi ngược lại string -> int cho các key
                self.metadata = {int(k): v for k, v in data.items()}
            return True
        except Exception as e:
            print(f"Lỗi khi tải index: {e}")
            return False

    def similarity_search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[float, Dict]]:
        """
        Tìm kiếm top_k vector có độ tương đồng cao nhất.
        Trả về danh sách tuple: (khoảng_cách, metadata_dict)
        """
        if self.index is None or self.index.ntotal == 0:
            return []
            
        query = np.array([query_vector], dtype=np.float32)
        distances, indices = self.index.search(query, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx in self.metadata: # -1 nghĩa là không đủ kết quả tìm kiếm
                results.append((distances[0][i], self.metadata[idx]))
                
        return results
