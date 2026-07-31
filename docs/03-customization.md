# Hướng dẫn tùy chỉnh Bot (Customization Guide)

Tài liệu này giúp các thành viên trong team biết cách thay đổi các thông số quan trọng của Bot mà không sợ làm hỏng hệ thống.

## 1. Cách cấu hình các kênh thu thập dữ liệu
Nếu bạn tạo thêm các kênh mới trên Discord và muốn Bot thu thập dữ liệu từ đó, hãy mở file `src/collector.py`.

Ở đầu file, bạn sẽ thấy biến:
```python
TARGET_CHANNELS = ["hỏi-đáp", "chia-sẻ", "bài-học"]
```
Bạn chỉ cần thêm từ khóa của tên kênh vào đây. **Lưu ý:** Bạn không cần phải copy các Emoji (như 😇, 🦾) ở đầu tên kênh. Code đã được thiết lập để nhận diện chuỗi con, tức là chỉ cần kênh chứa chữ "hỏi-đáp" thì nó sẽ tự động thu thập.

## 2. Cách thay đổi ID Tag MOD
Khi Bot gặp câu hỏi khó không có trong kho dữ liệu, nó sẽ tự động nhận diện "biết-mình-không-biết" và gọi MOD vào trả lời.

Hiện tại nó đang in ra chữ `@MOD` dạng text thường. Để nó có thể **nhắc tên (Ping)** Role MOD thật sự trên Discord:
1. Bật tính năng Developer Mode trên Discord (User Settings > Advanced > Developer Mode).
2. Vào Server, vào phần Roles (Vai trò), chuột phải vào Role của MOD/TA và chọn **Copy Role ID** (ví dụ: `123456789`).
3. Mở file `src/rag.py`, tìm đến dòng ~41:
```python
clean_answer = "Câu này hơi ngoài hiểu biết của mình, để không trả lời sai thì mình tag MOD vào giúp bạn nha!"
return clean_answer + " @MOD"
```
Thay thế `@MOD` bằng cú pháp `<@&123456789>` (thay 123456789 bằng ID bạn vừa copy).

## 3. Cách tùy chỉnh độ "ảo tưởng" (Hallucination) của AI
Nếu bạn thấy AI quá cứng nhắc (từ chối trả lời dù có thông tin), hoặc quá phóng khoáng (hay bịa chuyện), hãy điều chỉnh:
- **Nội dung Prompt:** Chỉnh sửa các nguyên tắc trong file `src/prompts.py`.
- **Thông số Temperature:** Mở file `src/llm.py` và tìm dòng `temperature=0.0`. 
  - Tăng dần lên `0.2` hoặc `0.3` nếu muốn câu văn tự nhiên và sáng tạo hơn.
  - Giữ nguyên `0.0` để AI trả lời bám sát dữ liệu thực tế nhất (rất quan trọng đối với RAG).
