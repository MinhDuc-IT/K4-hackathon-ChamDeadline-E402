import json
from typing import List, Dict

def load_documents(filepath: str) -> List[Dict]:
    """
    Tải danh sách các tài liệu (documents) từ file JSON.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Không tìm thấy file: {filepath}")
        return []
    except Exception as e:
        print(f"Lỗi khi tải tài liệu: {e}")
        return []

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Hàm chia nhỏ văn bản (text splitter) dựa trên số lượng ký tự, có đoạn chồng lặp (overlap).
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        if end >= text_length:
            chunks.append(text[start:])
            break
            
        break_point = end
        # Cố gắng cắt chuỗi ở vị trí đẹp (xuống dòng, dấu câu, khoảng trắng)
        for separator in ["\n\n", "\n", ". ", " "]:
            last_sep = text.rfind(separator, start, end)
            if last_sep != -1 and last_sep > start + (chunk_size // 2):
                break_point = last_sep + len(separator)
                break
                
        chunks.append(text[start:break_point].strip())
        start = break_point - overlap
        
        if start <= 0 or break_point <= start:
            start = break_point
            
    return chunks
