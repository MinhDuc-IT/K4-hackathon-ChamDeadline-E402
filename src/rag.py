import re
from typing import List, Dict
from src import retrieval, llm

def get_answer(question: str, conversation_history: List[Dict] = None) -> str:
    """
    Quy trình RAG cốt lõi:
    1. Lấy Top-K văn bản liên quan.
    2. Gọi LLM để sinh câu trả lời (kèm lịch sử hội thoại nếu có).
    3. Trích xuất và định dạng phần nguồn trích dẫn.
    """
    if conversation_history is None:
        conversation_history = []
        
    retrieved_docs = retrieval.search(question)
    print(f"[DEBUG] 🔎 Đã tìm thấy {len(retrieved_docs)} tài liệu liên quan từ FAISS.")
    
    if not retrieved_docs:
        print("[DEBUG] ❌ Không tìm thấy thông tin phù hợp, trả về báo lỗi mặc định.")
        return "Tôi không tìm thấy thông tin này trong cơ sở tri thức của Server."
        
    # Lọc trùng lặp: Nếu tin nhắn rời nằm trong một thread dài hơn, ưu tiên giữ thread dài
    # và loại bỏ tin nhắn rời, ĐỒNG THỜI giữ nguyên thứ tự xếp hạng (relevance) của FAISS.
    filtered_docs = []
    for i, doc in enumerate(retrieved_docs):
        text = doc.get("text", "")
        is_duplicate = False
        for j, other_doc in enumerate(retrieved_docs):
            if i == j:
                continue
            other_text = other_doc.get("text", "")
            if text in other_text:
                if text == other_text:
                    if j < i: # Nếu giống hệt nhau, chỉ giữ lại document xuất hiện trước (rank cao hơn)
                        is_duplicate = True
                        break
                else:
                    # Nếu text hiện tại là một phần của text khác dài hơn, bỏ qua text hiện tại
                    is_duplicate = True
                    break
        if not is_duplicate:
            filtered_docs.append(doc)
            
    context_chunks = []
    unique_sources_map = {}
    
    for idx, doc in enumerate(filtered_docs):
        text = doc.get("text", "")
        
        author = doc.get("author", "Unknown")
        created_at = doc.get("created_at", "Unknown time")
        channel = doc.get("channel", "Unknown")
        is_mod = doc.get("is_mod", False)
        
        # Đánh dấu [MOD] vào tên tác giả nếu người đó có Role MOD - LLM sẽ ưu tiên nguồn này
        author_label = f"[MOD] {author}" if is_mod else author
        
        source_id = idx + 1
        # Bọc metadata vào chung với text để LLM hiểu rõ bối cảnh
        formatted_chunk = f"[Nguồn số: {source_id} | Tác giả: {author_label}, Thời gian: {created_at}, Kênh: {channel}]\n{text}"
        context_chunks.append(formatted_chunk)
        
        url = doc.get("url", "")
        if url:
            unique_sources_map[source_id] = {
                "channel": channel,
                "thread": doc.get("thread", ""),
                "url": url
            }
            
    try:
        # Gọi mô hình LLM để trả lời câu hỏi dựa trên ngữ cảnh vừa thu thập (kèm lịch sử hội thoại)
        print(f"[DEBUG] 🧠 Đang gọi LLM để sinh câu trả lời...")
        answer = llm.generate_answer(question, context_chunks, conversation_history)
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
    if re.search(r"\[MAU_THUAN\]", answer, re.IGNORECASE):
        # Xóa tag nhưng KHÔNG return sớm, để code chạy tiếp xuống dưới và ghép thêm khối Nguồn
        answer = re.sub(r"\[MAU_THUAN\]\s*", "", answer, flags=re.IGNORECASE).strip()
        
    # Trích xuất các ID nguồn được LLM trích dẫn
    cited_ids = [int(x) for x in re.findall(r"\[Nguồn số:\s*(\d+)\]", answer, flags=re.IGNORECASE)]
    
    # Xóa các tag nguồn khỏi câu trả lời để hiển thị sạch sẽ
    answer = re.sub(r"\[Nguồn số:\s*\d+\]", "", answer, flags=re.IGNORECASE).strip()
    
    # Tạo câu trả lời cuối cùng bao gồm nội dung trả lời và danh sách nguồn trích dẫn
    final_answer = f"**Câu trả lời**\n\n{answer}\n\n**Xem chi tiết tại đây**\n\n"
    
    top_sources = []
    seen_urls_in_output = set()
    
    if cited_ids:
        for cid in cited_ids:
            if cid in unique_sources_map:
                src = unique_sources_map[cid]
                if src["url"] not in seen_urls_in_output:
                    seen_urls_in_output.add(src["url"])
                    top_sources.append(src)
                    
    # Nếu LLM quên trích dẫn, hoặc không có cited_ids hợp lệ, lấy mặc định 2 nguồn đầu tiên
    if not top_sources:
        top_sources = list(unique_sources_map.values())[:2]
        
    # Chỉ hiển thị tối đa 3 nguồn trích dẫn tốt nhất
    top_sources = top_sources[:3]
    
    for src in top_sources:
        final_answer += f"• Kênh: {src['channel']}\n"
        if src['thread']:
            final_answer += f"• Chủ đề: {src['thread']}\n"
        if src['url']:
            final_answer += f"• Link: {src['url']}\n"
        final_answer += "\n"
        
    return final_answer.strip()
