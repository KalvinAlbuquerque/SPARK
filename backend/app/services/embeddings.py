from __future__ import annotations

import os

import numpy as np

_model = None

_CACHE_DIR = os.path.join(
    os.path.expanduser("~"),
    ".cache", "huggingface", "hub",
    "models--sentence-transformers--all-MiniLM-L6-v2",
)


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # Evita chamadas de rede quando o modelo já está em cache local
        local_only = os.path.isdir(_CACHE_DIR)
        _model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=local_only)
    return _model


def encode(text: str) -> np.ndarray:
    """Return a normalized float32 embedding vector of shape (384,)."""
    embedding = get_model().encode(text, normalize_embeddings=True)
    return np.array(embedding, dtype=np.float32)
