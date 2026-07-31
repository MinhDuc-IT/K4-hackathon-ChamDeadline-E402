# Discord Bot Benchmark Report

- Benchmark: `Discord Knowledge Bot Benchmark - Evidence-faithful v2` (v2.0)
- Run at (UTC): `20260731T065948Z`
- Bot model: `gpt-4o-mini`
- Judge model: `gpt-5.6` (reasoning_effort=high)
- Auth: `OPENAI_API_KEY`
- Cache messages: `27`
- Benchmark pass: **YES**

## Metrics

- Final Pass Rate: 19/20 — 95.0%
- Behavior Accuracy: 100.0%
- Answer Correctness: 96.15%
- Groundedness: 100.0%
- Citation Accuracy: 100.0%
- Abstention Accuracy: 100.0%
- Conflict Resolution Accuracy: 100.0%
- Security Pass Rate: 100.0%
- Hallucination Rate: 0.0%

## Failed cases

### H13
- Reason: Thiếu hai ý bắt buộc: giải pháp Chatbot + RAG cho FAQ và kiến trúc hybrid để định tuyến FAQ sang Chatbot, tác vụ phức tạp sang Agent, lỗi sang Human.
- Notes: Bot trả lời đúng rằng FAQ không cần xây thành Agent, nêu đúng các trường hợp nên dùng Agent như suy luận nhiều bước, tương tác tool/API, quyết định động và nhiệm vụ kéo dài. Bot cũng viện dẫn đúng hai nguồn bắt buộc, nhưng chưa tổng hợp đầy đủ khuyến nghị Chatbot + RAG và hybrid nên không đạt answer_correctness=2.
- Bot answer:

```text
Câu hỏi:
Một bot chỉ tra cứu và trả lời FAQ từ tài liệu có cần xây thành AI Agent không? Khi nào mới nên dùng Agent?

Trả lời:
Một bot chỉ tra cứu và trả lời FAQ từ tài liệu không cần xây thành AI Agent, vì nó chỉ phản hồi dựa trên dữ liệu có sẵn mà không cần suy luận hay tự động hóa quy trình. Nên xem xét sử dụng AI Agent khi có yêu cầu:

1. **Multi-step Reasoning**: Cần suy luận nhiều bước.
2. **Tool Interaction**: Cần tương tác với các công cụ như API, Search, Database.
3. **Dynamic Decision**: Quyết định cần thay đổi theo kết quả.
4. **Long Horizon**: Nhiệm vụ kéo dài nhiều bước.

Từ chat:
- Ngô Huy Hoàn đã chat ở kênh #🦾-chia-sẻ / TÓM TẮT LÝ THUYẾT DAY 03: TỪ CHATBOT ĐẾN AGENTIC AGENT (ReAct) lúc 20:19 ngày 30/07/2026
  https://discord.com/channels/1531213864467693578/1532377163351851218/1532377163351851218
  (trả lời cho: TÓM TẮT LÝ THUYẾT DAY 03: TỪ CHATBOT ĐẾN AGENTIC AGENT (ReAct))
- Ngô Huy Hoàn đã chat ở kênh #😜-bài-học / Từ Chatbot đến AI Agent: Sự tiến hóa của tư duy tự động hóa lúc 20:32 ngày 30/07/2026
  https://discord.com/channels/1531213864467693578/1532380402562498721/1532380402562498721
  (trả lời cho: Từ Chatbot đến AI Agent: Sự tiến hóa của tư duy tự động hóa)
- Ngô Huy Hoàn đã chat ở kênh #🦾-chia-sẻ / 8 Kiến trúc RAG dành cho AI Engineers lúc 20:16 ngày 30/07/2026
  https://discord.com/channels/1531213864467693578/1532376288134697162/1532376288134697162
  (trả lời cho: 8 Kiến trúc RAG dành cho AI Engineers)
```
