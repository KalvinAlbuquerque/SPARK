"""
Testes unitários — geração de embeddings e ranqueamento por similaridade.
Requer sentence-transformers instalado com o modelo all-MiniLM-L6-v2 em cache local.
Execute `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"` para baixar o modelo antes de rodar estes testes.
"""
import os

import numpy as np
import pytest

# Pula todos os testes deste módulo se o modelo não estiver em cache local
_cache_root = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
_model_cached = os.path.isdir(os.path.join(_cache_root, "models--sentence-transformers--all-MiniLM-L6-v2"))
pytestmark = pytest.mark.skipif(
    not _model_cached,
    reason="modelo all-MiniLM-L6-v2 não está em cache local — execute o download antes",
)

from app.services.embeddings import encode


def test_encode_retorna_ndarray():
    result = encode("aprendizado de máquina")
    assert isinstance(result, np.ndarray)


def test_encode_shape_384():
    result = encode("epidemiologia de arboviroses")
    assert result.shape == (384,)


def test_encode_dtype_float32():
    result = encode("saúde pública")
    assert result.dtype == np.float32


def test_encode_normalizado():
    """Embedding deve ter norma ~1.0 (normalize_embeddings=True)."""
    result = encode("pesquisa científica UNEB")
    norm = float(np.linalg.norm(result))
    assert abs(norm - 1.0) < 1e-5


def test_encode_textos_diferentes():
    """Textos diferentes devem produzir embeddings diferentes."""
    e1 = encode("dengue fever in Brazil")
    e2 = encode("deep learning neural networks")
    assert not np.allclose(e1, e2)


def test_ranqueamento_similaridade():
    """
    Um texto muito próximo ao query deve ter similaridade maior do que
    um texto não relacionado.
    """
    query = encode("epidemiologia de dengue no nordeste")
    similar = encode("surto de dengue na Bahia: fatores epidemiológicos")
    dissimilar = encode("redes neurais profundas para visão computacional")

    # Similaridade de cosseno = produto escalar (vetores normalizados)
    score_similar = float(np.dot(query, similar))
    score_dissimilar = float(np.dot(query, dissimilar))

    assert score_similar > score_dissimilar
