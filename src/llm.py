from typing import List
import openai
from src import config
from src.prompts import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE

# Khởi tạo client OpenAI
client = openai.OpenAI(
    api_key=config.OPENAI_API_KEY,
    base_url=config.OPENAI_BASE_URL if config.OPENAI_BASE_URL else None
)

def generate_embedding(text: str) -> List[float]:
    """
    Tạo một vector nhúng (embedding vector) cho văn bản truyền vào.
    """
    # Thay thế các ký tự xuống dòng để tối ưu hiệu suất mô hình
    text = text.replace("\n", " ")
    response = client.embeddings.create(
        input=[text],
        model=config.EMBEDDING_MODEL
    )
    return response.data[0].embedding

def generate_answer(question: str, context_chunks: List[str]) -> str:
    """
    Sinh câu trả lời cho một câu hỏi CHỈ DỰA TRÊN ngữ cảnh (context chunks) được cung cấp.
    """
    # Nếu không có ngữ cảnh nào, trả về câu trả lời mặc định
    if not context_chunks:
        return "Tôi không tìm thấy thông tin này trong cơ sở tri thức của Server."
        
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
