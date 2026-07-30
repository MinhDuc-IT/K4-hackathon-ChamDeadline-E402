# MVP Pipeline — Discord Knowledge Bot

## Mục tiêu

Xây dựng chatbot Discord có thể:

1. Nhận câu hỏi từ học viên.
2. Tìm câu hỏi hoặc hướng dẫn tương tự trong dữ liệu có sẵn.
3. Dùng AI tạo câu trả lời dựa trên dữ liệu tìm được.
4. Trả lời kèm nguồn tham khảo.

---

## Input và Output

### Input

```text
/ask Golden set cần bao nhiêu case?
```

### Output

```text
Golden set cần ít nhất 20 case.

Nguồn:
- Hackathon Guide
- Thread Discord đã được TA trả lời
```

---

## Pipeline MVP

```text
Câu hỏi từ Discord
        ↓
Nhận input qua lệnh /ask
        ↓
Tìm câu hỏi tương tự trong file JSON
        ↓
Lấy câu trả lời và nguồn liên quan
        ↓
Gửi câu hỏi + dữ liệu tìm được cho LLM
        ↓
LLM tạo câu trả lời ngắn gọn
        ↓
Bot trả kết quả lên Discord
```

---

## Dữ liệu MVP

Chưa cần crawl toàn bộ Discord.

Tạo thủ công file `knowledge.json` gồm khoảng 10–20 câu hỏi và hướng dẫn.

```json
[
  {
    "question": "Golden set cần bao nhiêu case?",
    "answer": "Golden set cần ít nhất 20 case.",
    "source": "Hackathon Guide",
    "source_url": "https://discord.com/channels/..."
  },
  {
    "question": "Deadline commit spec là khi nào?",
    "answer": "Deadline commit spec là 23:59 ngày đầu tiên.",
    "source": "Thông báo chính thức",
    "source_url": "https://discord.com/channels/..."
  }
]
```

---

## Cách tìm câu hỏi tương tự

Trong MVP một giờ, chưa cần ChromaDB.

Có thể chọn một trong hai cách:

### Cách đơn giản nhất

Gửi toàn bộ 10–20 knowledge items cùng câu hỏi cho LLM và yêu cầu model chọn thông tin phù hợp.

```text
Câu hỏi người dùng
        +
Danh sách knowledge items
        ↓
LLM chọn nguồn phù hợp và trả lời
```

### Cách tốt hơn một chút

Dùng `sentence-transformers` để tìm ba câu hỏi gần nhất, sau đó gửi ba kết quả này cho LLM.

```text
Câu hỏi
    ↓
Embedding
    ↓
Cosine similarity
    ↓
Top 3 knowledge items
    ↓
LLM tạo câu trả lời
```

Với giới hạn một giờ, ưu tiên cách đầu tiên.

---

## Công nghệ

```text
Python
discord.py
LLM API
JSON
python-dotenv
```

Cài đặt:

```bash
pip install discord.py python-dotenv
```

Cài thêm SDK tương ứng với LLM API đang sử dụng.

---

## Cấu trúc thư mục

```text
project/
├── app.py
├── knowledge.json
├── .env
├── .gitignore
└── requirements.txt
```

---

## Luồng xử lý trong code

```python
async def answer_question(question: str) -> str:
    knowledge = load_knowledge("knowledge.json")

    prompt = build_prompt(
        question=question,
        knowledge=knowledge,
    )

    answer = call_llm(prompt)

    return answer
```

Discord command:

```python
@bot.tree.command(name="ask")
async def ask(interaction, question: str):
    await interaction.response.defer()

    answer = await answer_question(question)

    await interaction.followup.send(answer)
```

---

## Prompt MVP

```text
Bạn là trợ lý Discord của khóa học.

Chỉ sử dụng thông tin trong KNOWLEDGE để trả lời câu hỏi.

Nếu tìm thấy thông tin phù hợp:
- Trả lời ngắn gọn.
- Ghi tên nguồn.
- Đưa link nguồn nếu có.

Nếu không tìm thấy:
- Nói rằng chưa có thông tin phù hợp.
- Không tự suy đoán.

QUESTION:
{question}

KNOWLEDGE:
{knowledge}
```

---

## Phạm vi một giờ

### Cần hoàn thành

* Tạo Discord bot.
* Tạo slash command `/ask`.
* Chuẩn bị khoảng 10–20 knowledge items.
* Gọi LLM thật.
* Trả lời được ít nhất ba câu hỏi mẫu.
* Hiển thị nguồn trong câu trả lời.

### Chưa cần làm

* Crawl toàn bộ Discord.
* ChromaDB.
* Embedding model.
* Evaluation.
* Golden set.
* Feedback system.
* Trang quản trị.
* Tự động cập nhật knowledge base.
* Deploy cloud 24/7.
* Phân quyền nguồn phức tạp.

---

## Kịch bản demo

### Câu hỏi có trong dữ liệu

```text
User:
/ask Golden set cần bao nhiêu case?

Bot:
Golden set cần ít nhất 20 case.

Nguồn: Hackathon Guide
```

### Câu hỏi được diễn đạt khác

```text
User:
/ask Bộ test tối thiểu phải có mấy câu?

Bot:
Golden set cần ít nhất 20 case.

Nguồn: Hackathon Guide
```

### Câu hỏi chưa có dữ liệu

```text
User:
/ask Mentor chấm bài theo tiêu chí bí mật nào?

Bot:
Mình chưa tìm thấy thông tin phù hợp trong dữ liệu hiện có.
Bạn nên hỏi TA hoặc mentor để được xác nhận.
```

---

## Definition of Done

MVP hoàn thành khi:

* Bot xuất hiện online trên Discord.
* Người dùng sử dụng được `/ask`.
* Bot gọi một LLM thật.
* Bot trả lời dựa trên `knowledge.json`.
* Bot hiển thị nguồn.
* Bot không tự đoán khi dữ liệu không có.
* Demo được ít nhất ba trường hợp đầu vào–đầu ra.
