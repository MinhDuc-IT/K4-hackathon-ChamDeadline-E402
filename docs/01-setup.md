# Hướng dẫn Cài đặt và Chạy Bot

Tài liệu này hướng dẫn các thành viên trong team cách thiết lập môi trường và chạy Bot RAG Discord nội bộ.

## 1. Yêu cầu hệ thống
- **Python:** Phiên bản 3.9 trở lên.
- **Môi trường ảo (Virtual Environment):** Bắt buộc sử dụng `.venv` để tránh xung đột thư viện.

## 2. Cài đặt thư viện (Dependencies)
Cài đặt tất cả các thư viện cần thiết bằng lệnh:
```bash
python -m pip install -r requirements.txt
```

## 3. Cấu hình biến môi trường (.env)
Bạn cần tạo một file tên là `.env` ở thư mục gốc (nằm cùng chỗ với file `run.py`). Bạn có thể copy nội dung từ file `.env.example` qua và điền thông tin thật của mình:

- `DISCORD_TOKEN`: Token của bot lấy từ trang [Discord Developer Portal](https://discord.com/developers/applications).
- `DISCORD_GUILD_ID`: ID của Server Discord mà bạn muốn thu thập dữ liệu (Bật Developer Mode trên Discord > Chuột phải vào Server > Copy Server ID).
- `OPENAI_API_KEY`: API Key của mô hình ngôn ngữ (Lấy từ OpenRouter, OpenAI, hoặc nền tảng tương tự).
- `OPENAI_BASE_URL`: Link API của nền tảng (Ví dụ OpenRouter là `https://openrouter.ai/api/v1`).
- `OPENAI_MODEL`: Tên mô hình dùng để trả lời (Ví dụ: `gpt-4o-mini`).
- `EMBEDDING_MODEL`: Tên mô hình nhúng vector (Ví dụ mặc định: `intfloat/multilingual-e5-large` để chạy cục bộ).

## 4. Cách khởi chạy Bot
Từ nay, bạn **chỉ cần dùng một lệnh duy nhất** để khởi động toàn bộ hệ thống:

```bash
python run.py
```

Khi chạy lệnh này, hệ thống sẽ tự động:
1. Đăng nhập và bật Discord Bot online.
2. Tự động chạy một luồng ngầm (Background Thread) để lấy toàn bộ dữ liệu tin nhắn từ Discord về (quét các kênh có chứa từ khóa được cấu hình trong `src/collector.py`).
3. Tự động chia nhỏ văn bản và nhúng (Embed) vào Vector Database FAISS.
4. Tự động lặp lại quá trình lấy dữ liệu này mỗi **24 giờ**.

## 5. Cấp quyền cho Bot (Lưu ý quan trọng)
Để Bot có thể đọc được tin nhắn từ Discord và tải về kho dữ liệu, bạn **BẮT BUỘC** phải bật tính năng `Message Content Intent` trên Discord Developer Portal:
1. Vào ứng dụng Bot của bạn.
2. Chọn tab **Bot** bên trái.
3. Cuộn xuống phần **Privileged Gateway Intents**.
4. Bật công tắc ở mục **Message Content Intent**.
5. Nhấn **Save Changes**.
