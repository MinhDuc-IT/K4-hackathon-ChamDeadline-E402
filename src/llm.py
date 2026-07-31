from typing import List
import openai
from src import config
from src.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE

from sentence_transformers import SentenceTransformer

# Khởi tạo client OpenAI cho phần Text Generation
client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL if config.OPENAI_BASE_URL else None
)

# Khởi tạo mô hình embedding cục bộ
print(f"Đang tải mô hình embedding: {config.EMBEDDING_MODEL}...")
embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)

def generate_embedding(text: str) -> List[float]:
    """
    Tạo một vector nhúng (embedding vector) cho văn bản truyền vào sử dụng SentenceTransformer.
    """
    # Thay thế các ký tự xuống dòng để tối ưu hiệu suất mô hình
    text = text.replace("\n", " ")
    
    # Mã hóa văn bản thành vector
    # normalize_embeddings=True rất quan trọng đối với cosine similarity / L2
    embedding = embedding_model.encode(text, normalize_embeddings=True)
    return embedding.tolist()

def generate_answer(question: str, context_chunks: List[str], conversation_history: List[dict] = None) -> str:
    """
    Sinh câu trả lời cho một câu hỏi CHỈ DỰA TRÊN ngữ cảnh (context chunks) được cung cấp.
    Có thể kèm lịch sử hội thoại để duy trì ngữ cảnh cuộc trò chuyện.
    """
    if conversation_history is None:
        conversation_history = []
        
    # Nếu không có ngữ cảnh nào, trả về câu trả lời mặc định
    if not context_chunks:
        return "[KHONG_BIET]"
        
    context_text = "\n\n---\n\n".join(context_chunks)
    user_prompt = RAG_PROMPT_TEMPLATE.format(context=context_text, question=question)
    
    import datetime
    current_time_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    dynamic_system_prompt = f"Thông tin hệ thống: Thời gian hiện tại là {current_time_str}.\n\n{SYSTEM_PROMPT}"
    
    # Xây dựng danh sách messages: System Prompt → Lịch sử hội thoại → Câu hỏi hiện tại
    messages = [{"role": "system", "content": dynamic_system_prompt}]
    
    # Thêm lịch sử hội thoại (nếu có)
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Thêm câu hỏi hiện tại (kèm ngữ cảnh RAG)
    messages.append({"role": "user", "content": user_prompt})
    
    # Debug: Thống kê kích thước prompt
    total_chars = sum(len(m["content"]) for m in messages)
    estimated_tokens = total_chars // 4  # Ước tính: 1 token ≈ 4 ký tự
    print(f"[DEBUG] 📊 Thống kê prompt:")
    print(f"  - System Prompt: {len(SYSTEM_PROMPT)} ký tự")
    print(f"  - Lịch sử hội thoại: {len(conversation_history)} tin nhắn")
    print(f"  - Context chunks: {len(context_chunks)} đoạn")
    print(f"  - Tổng: {total_chars} ký tự (~{estimated_tokens} tokens ước tính)")
    
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=0.5, # Giữ temperature ở mức 0 để tránh việc AI tự bịa thông tin
        max_tokens=1024   # Giới hạn output để tiết kiệm credits
    )
    
    # Debug: Thống kê token thực tế từ API
    usage = response.usage
    if usage:
        print(f"[DEBUG] 💰 Token thực tế: prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, total={usage.total_tokens}")
    
    return response.choices[0].message.content
