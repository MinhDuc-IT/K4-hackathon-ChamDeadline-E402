# Discord History Bot MVP

Bot Discord: sync history + embed local vào cache, `/ask` chỉ search vector đã lưu.

## Flow

```text
Bot start / lệnh /sync
  → đọc Text + Forum history
  → embed tin mới
  → lưu cache/messages.json + cache/embeddings.npy

/ask
  → chỉ embed câu hỏi
  → cosine với cache local
  → LLM / fallback hỏi TA
```

## Chạy

```bash
cd codebase
.venv\Scripts\activate
python app.py
```

Lần đầu start sẽ sync + embed, có thể hơi lâu. Sau đó `/ask` sẽ nhanh hơn nhiều.

## Conflict handling

Ưu tiên **LLM classify** sau bước retrieve:

- LLM gắn `affirm` / `deny` / `neutral` cho từng nguồn
- nếu `conflict=true` → liệt kê 2 phía + handoff TA/BTC
- marker hardcode chỉ dùng khi LLM lỗi hoặc chưa cấu hình

Không conflict thì LLM trả lời bình thường, kèm nguồn.

## Biến môi trường

- `DISCORD_BOT_TOKEN`
- `DISCORD_GUILD_ID`
- `DISCORD_SEARCH_CHANNEL_IDS`
- `DISCORD_HISTORY_LIMIT`
- `EMBEDDING_MODEL`
- `EMBEDDING_MIN_SCORE`
- `SYNC_INTERVAL_MINUTES` (mặc định 10)
- `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`
