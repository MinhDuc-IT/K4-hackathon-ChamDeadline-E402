# Reflection Cá Nhân: Nguyễn Minh Đức

- **Mã học viên:** 2A202601438
- **Phân công:** Retrieval, embedding, conflict handling

## 1. Vai trò trong nhóm và đóng góp
Mình làm phần "Não" của bot: biến văn bản thành Vector và tìm kiếm (RAG pipeline).
- Chọn dùng `intfloat/multilingual-e5-large` vì nó xịn với tiếng Việt.
- Dựng FAISS local để truy xuất cho nhanh.
- Thiết kế luồng xử lý mâu thuẫn (Conflict handling) bằng LLM.

## 2. Bài học rút ra
Vector Search không phải "cây đũa thần". Ban đầu cứ nghĩ xài RAG là xong, nhưng thực tế cosine similarity chỉ tìm ra độ tương đồng ngữ nghĩa. Ví dụ: user hỏi "ddl lab 5", nó lôi ra tin nhắn "hôm nay có lab không", vì có chung chữ lab.

Đau nhất là lúc chạy Eval ra cái lỗi "Conflict giả". Do 2 nguồn không liên quan bị nhét vào chung, thế là con Bot bảo "2 nguồn mâu thuẫn". Bài học là trước khi ném cho LLM tổng hợp, phải có 1 bước "Relevance Check" để lọc các nguồn `neutral` (không chứa câu trả lời). Thiết kế AI không chỉ là ráp thư viện, mà là kiểm soát cách luồng dữ liệu chạy.
