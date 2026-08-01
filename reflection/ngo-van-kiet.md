# Reflection Cá Nhân: Ngô Văn Kiệt

- **Mã học viên:** 2A202601524
- **Phân công:** Evidence, survey, impact

## 1. Vai trò trong nhóm và đóng góp
Mình đảm nhận việc thu thập evidence ban đầu để chứng minh bài toán. Việc này bao gồm cả lập bảng câu hỏi khảo sát, rải link và đọc tay (mining) các file Discord data do BTC cung cấp.

- **Kết quả lớn nhất:** Thu thập đủ 33 lượt phản hồi và thống kê chứng minh hơn 85% người dùng bị ngộp kênh.
- **Khó khăn:** Một số survey form trả về khá nhiễu do học viên hiểu lầm câu hỏi. Cần phải lọc kỹ để không đưa data rác vào spec.

## 2. Bài học rút ra
Mình nhận ra là con số survey (dù là 100%) cũng không có nghĩa lý gì nếu AI không giải quyết được cái "pain" cốt lõi. Ban đầu tính làm bot tóm tắt cuối ngày (summary), nhưng khi nhìn data thấy học viên lúc làm bài cần giải đáp ngay, thế là đổi sang làm bot Knowledge RAG.

Việc "evidence-faithful" cực kỳ quan trọng, nhờ có data khảo sát rõ ràng mà mình thuyết phục được nhóm đổi thiết kế từ Automate sang Conditional (buộc bot phải kèm link nguồn, vì 59% học viên ưu tiên admin trả lời hơn là tốc độ).
