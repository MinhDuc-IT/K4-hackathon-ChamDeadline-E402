from src import retrieval, llm

def get_answer(question: str) -> str:
    """
    Quy trình RAG cốt lõi:
    1. Lấy Top-K văn bản liên quan.
    2. Gọi LLM để sinh câu trả lời.
    3. Trích xuất và định dạng phần nguồn trích dẫn.
    """
    retrieved_docs = retrieval.search(question)
    
    if not retrieved_docs:
        return "Tôi không tìm thấy thông tin này trong cơ sở tri thức của Server."
        
    context_chunks = []
    unique_sources = []
    seen_urls = set()
    
    # Gom nhóm và loại bỏ các nguồn bị trùng lặp (dựa trên URL)
    for doc in retrieved_docs:
        context_chunks.append(doc.get("text", ""))
        
        url = doc.get("url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_sources.append({
                "channel": doc.get("channel", "Unknown"),
                "thread": doc.get("thread", ""),
                "url": url
            })
            
    try:
        # Gọi mô hình LLM để trả lời câu hỏi dựa trên ngữ cảnh vừa thu thập
        answer = llm.generate_answer(question, context_chunks)
    except Exception as e:
        print(f"Lỗi khi gọi LLM: {e}")
        return "Đã xảy ra lỗi trong quá trình tạo câu trả lời."
        
    # Xử lý trường hợp LLM không tìm thấy thông tin
    if "[KHONG_BIET]" in answer or "Câu này hơi ngoài hiểu biết của mình" in answer:
        clean_answer = "Câu này hơi ngoài hiểu biết của mình, để không trả lời sai thì mình tag MOD vào giúp bạn nha!"
        return clean_answer + " @MOD"
        
    # Xử lý trường hợp chỉ là câu chào hỏi/giao tiếp thông thường
    if answer.strip().startswith("[GIAO_TIEP]"):
        return answer.replace("[GIAO_TIEP]", "").strip()
        
    # Tạo câu trả lời cuối cùng bao gồm nội dung trả lời và danh sách nguồn trích dẫn
    final_answer = f"**Câu trả lời**\n\n{answer}\n\n**Xem chi tiết tại đây**\n\n"
    
    for src in unique_sources:
        final_answer += f"• Kênh: {src['channel']}\n"
        if src['thread']:
            final_answer += f"• Chủ đề: {src['thread']}\n"
        if src['url']:
            final_answer += f"• Link: {src['url']}\n"
        final_answer += "\n"
        
    return final_answer.strip()
