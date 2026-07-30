# Skill: Retrieval-Augmented Generation (RAG)

## 1. Purpose
This skill teaches the agent how to build robust Retrieval-Augmented Generation pipelines. RAG enables the LLM to generate grounded, fact-based answers by fetching relevant chunks from a knowledge base before generation.

## 2. Responsibilities
- Designing ingestion pipelines: parsing, cleaning, and chunking documents.
- Generating semantic embeddings for text chunks.
- Executing Top-K similarity search against a Vector Database.
- Reranking retrieved documents for higher precision.
- Assembling context dynamically for the LLM prompt.
- Mitigating hallucination by ensuring answers rely strictly on retrieved context.

## 3. When to use
- When the chatbot needs to answer questions based on a specific, dynamic, or private dataset (e.g., student FAQs, course documentation).
- When factual accuracy and citations are strictly required.

## 4. When NOT to use
- For simple conversational chit-chat where general knowledge suffices.
- When real-time low-latency is more critical than accuracy (RAG adds retrieval and processing overhead).

## 5. Workflow
1. **Ingestion**: Read document -> Preprocess -> Chunk (e.g., via LangChain text splitters) -> Embed -> Store in DB.
2. **Retrieval**: Receive query -> Embed query -> Search DB for Top-K chunks.
3. **Reranking**: (Optional) Pass Top-K through a Cross-Encoder to re-order by true relevance.
4. **Generation**: Combine user query and Top retrieved chunks into a prompt -> Call LLM -> Return answer with citations.

## 6. Best practices
- **Chunking Strategy**: Use overlap (e.g., 500 tokens with 50 overlap) to avoid cutting context mid-sentence.
- **Hybrid Search**: Combine Dense (Embeddings) and Sparse (BM25/Keyword) retrieval if the Vector DB supports it.
- **Citation Tracking**: Store metadata (source file, line number) with each chunk and require the LLM to output these metadata tags as citations.

## 7. Coding conventions
- Decouple components: The Retriever, the Embedder, and the Generator should be distinct classes/interfaces.
- Use asynchronous clients for LLM and Embedding API calls to prevent blocking the bot.

## 8. Example prompts
- "Build a pipeline that takes a user question, retrieves the top 3 relevant chunks from our Vector DB, and formulates an answer."
- "Implement a text chunking utility using RecursiveCharacterTextSplitter for our FAQ markdown files."

## 9. Example tasks
- "Create an ingest script that reads all `.md` files in `data/`, chunks them, and upserts them into FAISS."
- "Write an LLM prompt that forces the model to say 'I don't know' if the context doesn't contain the answer."

## 10. Common pitfalls
- **Lost in the Middle**: Providing too many chunks to the LLM, causing it to ignore information in the middle of the context. (Keep Top-K reasonable, e.g., 3-5).
- **Hallucination**: The model relying on its parametric memory instead of the provided context. Fix this with strict prompt engineering.
- **Poor Chunking**: Splitting text blindly without semantic boundaries (e.g., splitting a code block in half).

## 11. Directory structure
```
src/
├── rag/
│   ├── __init__.py
│   ├── ingestion.py
│   ├── retriever.py
│   └── generator.py
```

## 12. Suggested libraries
- `langchain` or `llama-index` (for chunking/orchestration)
- `sentence-transformers` (for local embeddings/reranking)
- `openai` / `litellm` (for generation)

## 13. References
- [Pinecone RAG guide](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [LangChain RAG Docs](https://python.langchain.com/docs/use_cases/question_answering/)
