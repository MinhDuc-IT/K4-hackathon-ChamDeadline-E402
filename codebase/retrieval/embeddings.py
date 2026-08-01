import numpy as np
from fastembed import TextEmbedding


class EmbeddingModel:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: TextEmbedding | None = None
        self._load_error: str | None = None

    @property
    def uses_e5_prefix(self) -> bool:
        return "e5" in self.model_name.lower()

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def load(self) -> None:
        if self._model is not None:
            return
        if self._load_error:
            raise RuntimeError(f"Embedding model unavailable: {self._load_error}")
        print(f"Loading embedding model: {self.model_name}")
        try:
            self._model = TextEmbedding(model_name=self.model_name)
        except Exception as error:
            self._load_error = str(error)
            raise
        print("Embedding model ready")

    @property
    def model(self) -> TextEmbedding:
        self.load()
        assert self._model is not None
        return self._model

    def _prepare_query(self, query: str) -> str:
        if self.uses_e5_prefix:
            return f"query: {query}"
        return query

    def _prepare_passage(self, text: str) -> str:
        if self.uses_e5_prefix:
            return f"passage: {text}"
        return text

    def embed_query(self, query: str) -> np.ndarray:
        vector = next(self.model.embed([self._prepare_query(query)]))
        return np.asarray(vector, dtype=np.float32)

    def embed_passages(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 1), dtype=np.float32)
        prepared = [self._prepare_passage(text) for text in texts]
        vectors = list(self.model.embed(prepared))
        return np.asarray(vectors, dtype=np.float32)
