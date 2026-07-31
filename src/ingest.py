import os
import hashlib
import json
from src import utils, llm
from src.vector_db import VectorDB

def run_ingestion():
    print("Bắt đầu quá trình nạp dữ liệu (ingestion)...")
    
    docs_path = "data/discord/documents.json"
    documents = utils.load_documents(docs_path)
        
    if not documents:
        print("Không có tài liệu nào. Vui lòng chạy file collector.py trước.")
        return

    # Check Hash để xem file có bị thay đổi không
    hash_path = "data/discord/documents.json.md5"
    try:
        with open(docs_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
            
        if os.path.exists(hash_path) and os.path.exists("data/discord/faiss.index"):
            with open(hash_path, 'r') as f:
                if f.read().strip() == file_hash:
                    print("Dữ liệu không có sự thay đổi, bỏ qua quá trình Embedding để tiết kiệm thời gian.")
                    return
    except Exception as e:
        print(f"Lỗi khi kiểm tra MD5: {e}")

    print(f"Đã tải {len(documents)} tin nhắn.")
    
    all_chunks = []
    metadata_list = []
    
    for doc in documents:
        chunks = utils.chunk_text(doc.get("text", ""))
        for chunk in chunks:
            if chunk.strip():
                all_chunks.append(chunk)
                metadata_list.append({
                    "text": chunk,
                    "channel": doc.get("channel", ""),
                    "thread": doc.get("thread", ""),
                    "url": doc.get("url", ""),
                    "author": doc.get("author", ""),
                    "message_id": doc.get("message_id", ""),
                    "created_at": doc.get("created_at", "")
                })
                
    print(f"Đã tạo ra {len(all_chunks)} đoạn văn bản (chunks). Bắt đầu tạo embeddings...")
    
    cache_path = "data/discord/embeddings_cache.json"
    embedding_cache = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                embedding_cache = json.load(f)
        except Exception as e:
            print(f"Không thể tải cache cũ: {e}")

    embeddings = []
    new_chunks_count = 0
    for i, chunk in enumerate(all_chunks):
        try:
            # Dùng mã hash của text để làm key cho cache
            chunk_hash = hashlib.md5(chunk.encode('utf-8')).hexdigest()
            if chunk_hash in embedding_cache:
                emb = embedding_cache[chunk_hash]
            else:
                emb = llm.generate_embedding(chunk)
                embedding_cache[chunk_hash] = emb
                new_chunks_count += 1
                
            embeddings.append(emb)
            if (i + 1) % 50 == 0:
                print(f"Đã xử lý {i + 1}/{len(all_chunks)} chunks...")
        except Exception as e:
            print(f"Lỗi khi tạo embedding cho một chunk: {e}")
            raise e
            
    if new_chunks_count > 0:
        print(f"Đã tạo embedding mới cho {new_chunks_count} chunks. Lưu lại cache...")
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(embedding_cache, f, ensure_ascii=False)
        except Exception as e:
            print(f"Không thể lưu cache: {e}")
    else:
        print("Tất cả chunks đều đã được cache từ trước, không cần gọi model.")
            
    if not embeddings:
        print("Không có embedding nào được tạo thành công.")
        return
        
    print("Đang xây dựng cơ sở dữ liệu FAISS...")
    
    dimension = len(embeddings[0])
    db = VectorDB()
    db.create_index(dimension)
    db.add_embeddings(embeddings, metadata_list)
    
    db.save_index()
    
    # Lưu lại mã Hash mới nhất
    try:
        with open(hash_path, 'w') as f:
            f.write(file_hash)
    except:
        pass
        
    print("Index đã được lưu trữ thành công vào thư mục data/discord/")

if __name__ == "__main__":
    run_ingestion()
