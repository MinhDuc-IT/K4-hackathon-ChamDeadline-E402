# Skill: Vector Database Integration

## 1. Purpose
This skill guides the agent in integrating, managing, and optimizing Vector Databases (like FAISS, Chroma, Qdrant) to store embeddings and perform high-speed semantic similarity searches.

## 2. Responsibilities
- Initializing and configuring vector database clients.
- Designing vector indexes (dimensionality, distance metrics).
- Inserting, updating, and deleting embeddings with associated metadata.
- Executing K-Nearest Neighbors (KNN) searches efficiently.
- Managing database persistence (saving to disk, loading from disk).

## 3. When to use
- In the retrieval phase of a RAG pipeline.
- When searching for semantically similar documents, FAQs, or code snippets.

## 4. When NOT to use
- When exact keyword matching is the sole requirement (use Elasticsearch or standard SQL instead).
- For simple key-value lookups.

## 5. Workflow
1. **Schema Design**: Determine the embedding dimension (e.g., 1536 for OpenAI `text-embedding-ada-002`) and distance metric (Cosine, L2, Inner Product).
2. **Initialization**: Load the DB from disk or connect to a remote instance.
3. **Upsert**: Add vectors alongside metadata (e.g., source file name, chunk text).
4. **Search**: Given a query vector, retrieve the `k` closest vectors.
5. **Persistence**: Ensure the index is saved securely and synchronized with the latest documents.

## 6. Best practices
- **Distance Metrics**: Always match the distance metric recommended by the embedding model (e.g., Cosine Similarity for OpenAI).
- **Metadata Filtering**: Utilize Vector DB metadata filters (if supported) to restrict searches (e.g., only search documents from `course_id=101`).
- **Batching**: Upsert vectors in batches rather than one by one to save time and API costs.

## 7. Coding conventions
- Wrap the Vector DB specific code in an abstract repository class (e.g., `VectorStoreInterface`) so swapping from FAISS to Qdrant is seamless.
- Always include `metadata` typing definitions.

## 8. Example prompts
- "Write a wrapper class for FAISS that can store embeddings, save the index to disk, and retrieve the top 5 nearest neighbors."
- "Implement a ChromaDB client that handles collection creation and adds document chunks with metadata."

## 9. Example tasks
- "Create a setup script that initializes a new Qdrant collection with 768 dimensions and Cosine distance."
- "Write a migration function to re-index all data if the embedding model changes."

## 10. Common pitfalls
- **Dimension Mismatch**: Attempting to insert a 768-dimensional vector into a 1536-dimensional index will crash.
- **Normalization**: Failing to normalize vectors if using Inner Product to simulate Cosine Similarity (especially in FAISS).
- **Memory Leaks**: Storing massive amounts of metadata in RAM instead of disk in local vector DBs.

## 11. Directory structure
```
src/
├── database/
│   ├── __init__.py
│   ├── vector_store.py
│   ├── faiss_client.py
│   └── qdrant_client.py
```

## 12. Suggested libraries
- `faiss-cpu` / `faiss-gpu`
- `chromadb`
- `qdrant-client`

## 13. References
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
