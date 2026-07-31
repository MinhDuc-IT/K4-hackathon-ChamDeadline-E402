from src import retrieval, llm

def get_answer(question: str) -> str:
    """
    Quy trình RAG cốt lõi:
    1. Lấy Top-K văn bản liên quan.
    2. Gọi LLM để sinh câu trả lời.
    3. Trích xuất và định dạng phần nguồn trích dẫn.
    """
    retrieved_docs = retrieval.search(question)
    print(f"[DEBUG] 🔎 Đã tìm thấy {len(retrieved_docs)} tài liệu liên quan từ FAISS.")
    
    if not retrieved_docs:
        print("[DEBUG] ❌ Không tìm thấy thông tin phù hợp, trả về báo lỗi mặc định.")
        return "Tôi không tìm thấy thông tin này trong cơ sở tri thức của Server."
        
    context_chunks = []
    unique_sources = []
    seen_urls = set()
    
    # Gom nhóm và loại bỏ các nguồn bị trùng lặp (dựa trên URL)
    for doc in retrieved_docs:
        text = doc.get("text", "")
        author = doc.get("author", "Unknown")
        created_at = doc.get("created_at", "Unknown time")
        channel = doc.get("channel", "Unknown")
        
        # Bọc metadata vào chung với text để LLM hiểu rõ bối cảnh
        formatted_chunk = f"[Tác giả: {author}, Thời gian: {created_at}, Kênh: {channel}]\n{text}"
        context_chunks.append(formatted_chunk)
        
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
        print(f"[DEBUG] 🧠 Đang gọi LLM để sinh câu trả lời...")
        answer = llm.generate_answer(question, context_chunks)
        print(f"[DEBUG] 🤖 LLM Output Raw:\n{answer}\n{'-'*40}")
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
        
    # Xử lý trường hợp phát hiện mâu thuẫn thông tin
    if "[MAU_THUAN]" in answer:
        # Xóa tag nhưng KHÔNG return sớm, để code chạy tiếp xuống dưới và ghép thêm khối Nguồn
        answer = answer.replace("[MAU_THUAN]", "").strip()
        
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
