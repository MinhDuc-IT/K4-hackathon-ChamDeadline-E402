# Discord Knowledge Bot MVP

Bot Discord MVP cho hackathon: nhan cau hoi qua lenh `/ask`, truy hoi cac cau tra loi tu dataset Discord, va tra lai cau tra loi kem nguon.

## Tinh nang hien tai

- Bot Discord that voi slash command `/ask`
- Tu dong sinh `knowledge.json` tu `../discord_dataset_with_ids.json` neu file chua ton tai
- Truy hoi lexical nhe, khong can vector DB
- Uu tien nguon co dau hieu `coach` / `ta`
- Neu co `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` thi tom tat bang LLM
- Neu khong co LLM, bot van tra loi bang extractive fallback

## Cai dat

```bash
cd codebase
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Bien moi truong

Bat buoc:

- `DISCORD_BOT_TOKEN`

Khuyen nghi cho slash command sync nhanh trong server test:

- `DISCORD_GUILD_ID`

Tuy chon cho LLM:

- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`

## Chay bot

```bash
cd codebase
python app.py
```

## Chuan bi knowledge base thu cong

Neu muon tao `knowledge.json` truoc khi chay bot:

```bash
cd codebase
python knowledge_builder.py
```

## Ghi chu MVP

- Dataset hien tai duoc bien doi theo kieu: message dau thread = cau hoi, cac message sau = candidate answers.
- Day la MVP phuc vu demo hackathon, chua phan loai chat che nguon chinh thuc / nguon da TA xac nhan.
- De tang do tin cay, buoc tiep theo nen them nhan `official`, `ta_confirmed`, hoac `needs_handoff`.
