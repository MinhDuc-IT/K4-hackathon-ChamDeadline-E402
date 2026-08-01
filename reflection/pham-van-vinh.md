# Reflection Cá Nhân: Phạm Văn Vinh

- **Mã học viên:** 2A202601988
- **Phân công:** Prompt, benchmark và eval

## 1. Vai trò trong nhóm và đóng góp
Mình đảm nhận việc đánh giá chất lượng bot, thiết kế Golden Set và tinh chỉnh System Prompt.
- Soạn 20 case khó (Benchmark v2).
- Cấu hình Judge bằng GPT-5.6 để tự động chấm điểm output.
- Chạy thực địa validation với user.

## 2. Bài học rút ra
Viết Prompt khó hơn mình tưởng. Cứ thêm 1 rules mới thì bot lại có nguy cơ lờ đi rule cũ. Ví dụ: thêm rule "ưu tiên nguồn của TA", nó lại "quên" mất rule "nếu mâu thuẫn thì phải hỏi lại". 

Về phần Eval, việc định nghĩa bộ metrics cứng (Answer Correctness, Hallucination Rate, Abstention Accuracy) đã cứu cả team. Nhìn bảng kết quả tuột dốc xuống 15% Pass Rate ở bản v2 làm cả team hơi hốt hoảng, nhưng bù lại chúng mình thấy rõ mồn một lỗi "False Conflict" nằm ở đâu để sửa. Thà fail lúc test còn hơn fail lúc user dùng thật.
