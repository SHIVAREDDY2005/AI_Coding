import hashlib
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Optional
import numpy as np

logger = logging.getLogger("ai_coding.embeddings")

DEFAULT_EMBEDDING_CACHE_DB = Path("data/cache/embeddings.db")
DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


def _text_hash(model_name: str, text: str) -> str:
    return hashlib.sha256(f"{model_name}::{text}".encode("utf-8")).hexdigest()


class EmbeddingService:
    """
    Generates normalized vector embeddings using Sentence Transformers (all-MiniLM-L6-v2)
    with a persistent SQLite cache so embeddings are computed at most once per text.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        cache_db_path: Path = DEFAULT_EMBEDDING_CACHE_DB,
        enabled: bool = True,
    ):
        self.model_name = model_name
        self.cache_db_path = cache_db_path
        self.enabled = enabled
        self._model = None
        self._lock = threading.Lock()
        self._mem_cache: dict[str, np.ndarray] = {}
        self._init_db()

    def _init_db(self) -> None:
        if not self.enabled:
            return
        try:
            self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.cache_db_path, timeout=30.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS embeddings (
                        key TEXT PRIMARY KEY,
                        dim INTEGER NOT NULL,
                        vec BLOB NOT NULL
                    )
                    """
                )
        except Exception as e:
            logger.warning("Failed to initialize embedding SQLite cache: %s", e)

    def _get_model(self):
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is None:
                from sentence_transformers import SentenceTransformer

                logger.info("Loading SentenceTransformer model: %s", self.model_name)
                self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode_texts(self, texts: list[str]) -> list[Optional[np.ndarray]]:
        if not self.enabled or not texts:
            return [None for _ in texts]

        keys = [_text_hash(self.model_name, t) for t in texts]
        results: list[Optional[np.ndarray]] = [None] * len(texts)
        missing_indices: list[int] = []

        # 1. Check in-memory cache
        for i, k in enumerate(keys):
            if k in self._mem_cache:
                results[i] = self._mem_cache[k]
            else:
                missing_indices.append(i)

        # 2. Check SQLite disk cache
        if missing_indices:
            try:
                with self._lock, sqlite3.connect(self.cache_db_path, timeout=30.0) as conn:
                    still_missing: list[int] = []
                    for i in missing_indices:
                        row = conn.execute(
                            "SELECT dim, vec FROM embeddings WHERE key = ?", (keys[i],)
                        ).fetchone()
                        if row:
                            vec = np.frombuffer(row[1], dtype=np.float32)
                            self._mem_cache[keys[i]] = vec
                            results[i] = vec
                        else:
                            still_missing.append(i)
                    missing_indices = still_missing
            except Exception as e:
                logger.warning("Embedding SQLite read error: %s", e)

        # 3. Compute missing embeddings in batch
        if missing_indices:
            try:
                model = self._get_model()
                missing_texts = [texts[i] for i in missing_indices]
                encoded = model.encode(
                    missing_texts,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                to_persist: list[tuple[str, int, bytes]] = []
                with self._lock:
                    for idx, vec in zip(missing_indices, encoded):
                        arr = np.asarray(vec, dtype=np.float32)
                        k = keys[idx]
                        self._mem_cache[k] = arr
                        results[idx] = arr
                        to_persist.append((k, int(arr.shape[0]), arr.tobytes()))

                    try:
                        with sqlite3.connect(self.cache_db_path, timeout=30.0) as conn:
                            conn.executemany(
                                "INSERT OR REPLACE INTO embeddings (key, dim, vec) VALUES (?, ?, ?)",
                                to_persist,
                            )
                    except Exception as e:
                        logger.warning("Embedding SQLite write error: %s", e)
            except Exception as e:
                logger.warning("SentenceTransformer encoding failed, falling back: %s", e)

        return results

    @staticmethod
    def cosine_similarity(vec_a: Optional[np.ndarray], vec_b: Optional[np.ndarray]) -> float:
        if vec_a is None or vec_b is None:
            return 0.0
        sim = float(np.dot(vec_a, vec_b))
        return max(0.0, min(1.0, sim))
