# Reflection Cá Nhân: Ngô Huy Hoàn

- **Mã học viên:** 2A202601925
- **Phân công:** Discord integration và sync dữ liệu

## 1. Vai trò trong nhóm và đóng góp
Nhiệm vụ của mình là lấy dữ liệu từ Discord và làm phần vỏ bot.
- Tích hợp `discord.py` để bot chạy và nhận lệnh `/ask`.
- Viết `collector.py` để gom nhóm các thread Forum và Text channel, xuất ra JSON.

## 2. Bài học rút ra
Xử lý dữ liệu chat cực hơn mình nghĩ. Khác với văn bản thuần, tin nhắn Discord có thể rất rời rạc, có emoji, có tag tên (@).
- Ban đầu mình chỉ lấy nội dung, kết quả là bot lúc trích dẫn chẳng biết ai nói câu đó. Rút kinh nghiệm, mình đã bổ sung metadata (Tác giả, Thời gian, Link tin nhắn, Role).
- Đặc biệt, khi xử lý Forum, việc gom toàn bộ reply trong một thread thành một "document" duy nhất là quyết định sáng suốt nhất, giúp cho việc Embedding sau này không bị mất bối cảnh (context).
