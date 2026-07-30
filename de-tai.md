Xây dựng một Discord chatbot có khả năng tìm lại và tổng hợp các câu trả lời đã tồn tại trong server, thay vì để học viên tự tìm kiếm trong lịch sử tin nhắn hoặc hỏi lại TA.

Khi người dùng đặt câu hỏi, bot sẽ:

Tiếp nhận câu hỏi trực tiếp trên Discord.
Tìm trong kho dữ liệu gồm:
Tin nhắn và câu trả lời cũ trên Discord.
Tin nhắn được ghim.
FAQ.
Tài liệu hướng dẫn chính thức.
Các câu trả lời đã được TA xác nhận.
Chọn những đoạn thông tin liên quan nhất.
Dùng mô hình ngôn ngữ để tạo câu trả lời ngắn gọn.
Trả lời kèm:
Nguồn tin nhắn hoặc tài liệu.
Kênh Discord.
Người trả lời.
Thời gian câu trả lời được đăng.
Nếu không đủ thông tin hoặc độ tin cậy thấp, bot không tự đoán mà:
Hỏi lại người dùng để làm rõ.
Hoặc tag/chuyển câu hỏi cho TA.
Luồng hoạt động ví dụ

Người dùng hỏi:

Deadline nộp Checkpoint 1 là khi nào?

Bot tìm thấy một thông báo của mentor trong kênh #announcement, sau đó trả lời:

Deadline nộp Checkpoint 1 là 23:59 ngày XX/XX.
Nguồn: thông báo của mentor trong #announcement.
[Xem tin nhắn gốc]

Nếu bot tìm thấy hai deadline khác nhau, bot sẽ trả lời:

Mình tìm thấy hai thông tin không thống nhất về deadline nên chưa thể trả lời chắc chắn. Mình đã chuyển câu hỏi này cho TA xác nhận.