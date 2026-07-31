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

def generate_answer(question: str, context_chunks: List[str]) -> str:
    """
    Sinh câu trả lời cho một câu hỏi CHỈ DỰA TRÊN ngữ cảnh (context chunks) được cung cấp.
    """
    # Nếu không có ngữ cảnh nào, trả về câu trả lời mặc định
    if not context_chunks:
        return "[KHONG_BIET]"
        
    context_text = "\n\n---\n\n".join(context_chunks)
    user_prompt = RAG_PROMPT_TEMPLATE.format(context=context_text, question=question)
    
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.0 # Giữ temperature ở mức 0 để tránh việc AI tự bịa thông tin
    )
    
    return response.choices[0].message.content
