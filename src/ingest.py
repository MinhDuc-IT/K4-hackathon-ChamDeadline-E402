import os
from src import utils, llm
from src.vector_db import VectorDB

def run_ingestion():
    print("Bắt đầu quá trình nạp dữ liệu (ingestion)...")
    
    docs_path = "data/discord/documents.json"
    documents = utils.load_documents(docs_path)
        
    if not documents:
        print("Không có tài liệu nào. Vui lòng chạy file collector.py trước.")
        return

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
                    "message_id": doc.get("message_id", "")
                })
                
    print(f"Đã tạo ra {len(all_chunks)} đoạn văn bản (chunks). Bắt đầu tạo embeddings...")
    
    embeddings = []
    for i, chunk in enumerate(all_chunks):
        try:
            emb = llm.generate_embedding(chunk)
            embeddings.append(emb)
            if (i + 1) % 50 == 0:
                print(f"Đã xử lý {i + 1}/{len(all_chunks)} chunks...")
        except Exception as e:
            print(f"Lỗi khi tạo embedding cho một chunk: {e}")
            raise e
            
    if not embeddings:
        print("Không có embedding nào được tạo thành công.")
        return
        
    print("Đang xây dựng cơ sở dữ liệu FAISS...")
    
    dimension = len(embeddings[0])
    db = VectorDB()
    db.create_index(dimension)
    db.add_embeddings(embeddings, metadata_list)
    
    db.save_index()
    print("Index đã được lưu trữ thành công vào thư mục data/discord/")

if __name__ == "__main__":
    run_ingestion()
