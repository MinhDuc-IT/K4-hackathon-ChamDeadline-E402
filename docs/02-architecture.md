# Cấu trúc Hệ thống & Kiến trúc RAG

Tài liệu này giải thích cách hoạt động của hệ thống dưới góc độ kỹ thuật để team dễ dàng maintain và phát triển thêm tính năng.

## 1. Cấu trúc thư mục (Directory Structure)
Mọi mã nguồn chính của hệ thống được đặt trong thư mục `src/`:
- `src/bot.py`: Trái tim của hệ thống. Quản lý kết nối Discord, lắng nghe lệnh `/ask` và chạy ngầm (background loop) chức năng cập nhật dữ liệu.
- `src/collector.py`: Bot tự động quét các kênh được cấu hình để thu thập lịch sử chat/forum, lưu thành file JSON.
- `src/ingest.py`: Đọc file JSON từ collector, chia nhỏ văn bản (chunking) và nhúng (embedding) vào cơ sở dữ liệu vector FAISS.
- `src/retrieval.py`: Xử lý logic tìm kiếm văn bản liên quan (Semantic Search) khi có câu hỏi từ người dùng.
- `src/rag.py`: Ráp nối giữa việc tìm kiếm ngữ cảnh và gọi LLM, xử lý luồng trả lời (Trả lời bình thường hoặc Báo lỗi nếu không biết).
- `src/llm.py`: Lớp giao tiếp trực tiếp với OpenAI / OpenRouter API (để trả lời) và SentenceTransformer cục bộ (để nhúng vector).
- `src/prompts.py`: Chứa các System Prompts và định dạng hướng dẫn cho LLM.
- `src/config.py`: Tải các biến môi trường.
- `src/utils.py`: Các hàm tiện ích hỗ trợ (như cắt chữ, làm sạch dữ liệu).

## 2. Luồng hoạt động của RAG (Retrieval-Augmented Generation)
Khi sinh viên sử dụng lệnh `/ask <câu hỏi>`:

1. **Tìm kiếm (Retrieval):** 
   `rag.py` gọi `retrieval.py` để tìm `TOP_K` đoạn văn bản gần giống với câu hỏi nhất từ FAISS Database.
2. **Gọi LLM (Generation):**
   Ngữ cảnh tìm được + Câu hỏi được ghép vào Prompt đưa cho LLM (`llm.py`).
3. **Phân tích Intent & Trả lời:**
   Dựa vào `prompts.py`, LLM sẽ có 3 hướng xử lý:
   - **(A) Giao tiếp thông thường:** Nếu người dùng chào hỏi, cảm ơn -> LLM trả lời kèm cờ `[GIAO_TIEP]`. Code sẽ xóa phần Nguồn trích dẫn đi.
   - **(B) Trả lời câu hỏi:** Nếu ngữ cảnh có thông tin, LLM tổng hợp và trả lời chi tiết. Trích dẫn Nguồn, Kênh, Chủ đề và Link cụ thể.
   - **(C) Ngoài vùng kiến thức:** Nếu ngữ cảnh hoàn toàn không có thông tin, LLM sẽ trả lời đúng câu xin lỗi mặc định. Code sẽ tự động bắt câu này, xóa nguồn và gắn thẻ tag `@MOD` để gọi TA vào hỗ trợ (tính năng "biết-mình-không-biết").

## 3. Luồng tự động cập nhật dữ liệu (Auto-Update)
Thay vì phải dùng tay chạy `collector.py` và `ingest.py` gây gián đoạn bot, hệ thống đã được thiết kế:
- Sử dụng `@tasks.loop(hours=24)` của Discord.py.
- Toàn bộ quá trình fetch dữ liệu nặng và embedding được đẩy vào luồng ngầm qua `asyncio.to_thread`.
- Nhờ vậy, Bot có thể tự học thêm kiến thức mới mỗi 24 tiếng mà **không bị treo** quá trình trả lời câu hỏi của người dùng.
