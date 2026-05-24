"""
Testes unitários — POST /api/search/semantic
Cobre: resultado com dados, resultado vazio, entrada inválida.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_pool(rows=None):
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=rows or [])
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=cm)
    return pool


def _sample_row():
    return {
        "id": 2,
        "titulo": "Arboviroses no Nordeste",
        "tipo_producao": "ARTIGO",
        "ano_publicacao": 2023,
        "nome_veiculo": "NATURE COMMUNICATIONS",
        "issn": "2041-1723",
        "doi": "10.1038/test",
        "qualis": "A1",
        "jcr": 14.7,
        "pesquisador_id": 1,
        "nome_completo": "Eduardo Jorge",
        "departamento": "DCET",
        "campus": "Campus I",
        "similarity_score": 0.89,
    }


_FAKE_EMBEDDING = np.zeros(384, dtype=np.float32)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ── testes ────────────────────────────────────────────────────────────────────

def test_search_semantic_resultado_com_dados():
    pool = _make_pool(rows=[_sample_row()])
    app.dependency_overrides[get_db] = lambda: pool

    with patch("app.services.semantic_search.encode", return_value=_FAKE_EMBEDDING):
        with TestClient(app) as client:
            r = client.post("/api/search/semantic", json={"query": "arboviroses nordeste"})

    assert r.status_code == 200
    data = r.json()
    assert len(data["resultados"]) == 1
    prod = data["resultados"][0]
    assert prod["titulo"] == "Arboviroses no Nordeste"
    # similarity_score é obrigatório na resposta semântica
    assert "similarity_score" in prod
    assert 0.0 <= prod["similarity_score"] <= 1.0


def test_search_semantic_resultado_vazio():
    pool = _make_pool(rows=[])
    app.dependency_overrides[get_db] = lambda: pool

    with patch("app.services.semantic_search.encode", return_value=_FAKE_EMBEDDING):
        with TestClient(app) as client:
            r = client.post("/api/search/semantic", json={"query": "xyzxyz"})

    assert r.status_code == 200
    assert r.json()["resultados"] == []


def test_search_semantic_entrada_invalida_query_vazia():
    pool = _make_pool()
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.post("/api/search/semantic", json={"query": ""})

    assert r.status_code == 422


def test_search_semantic_null_fields_omitidos():
    row = _sample_row()
    row["nome_veiculo"] = None
    row["qualis"] = None
    row["jcr"] = None
    pool = _make_pool(rows=[row])
    app.dependency_overrides[get_db] = lambda: pool

    with patch("app.services.semantic_search.encode", return_value=_FAKE_EMBEDDING):
        with TestClient(app) as client:
            r = client.post("/api/search/semantic", json={"query": "teste"})

    assert r.status_code == 200
    prod = r.json()["resultados"][0]
    assert "nome_veiculo" not in prod
    assert "qualis" not in prod
    assert "jcr" not in prod
    # similarity_score deve continuar presente mesmo com outros campos ausentes
    assert "similarity_score" in prod


def test_search_semantic_top_10():
    rows = [_sample_row() for _ in range(10)]
    for i, row in enumerate(rows):
        row["id"] = i + 1
        row["similarity_score"] = round(0.9 - i * 0.05, 2)
    pool = _make_pool(rows=rows)
    app.dependency_overrides[get_db] = lambda: pool

    with patch("app.services.semantic_search.encode", return_value=_FAKE_EMBEDDING):
        with TestClient(app) as client:
            r = client.post("/api/search/semantic", json={"query": "dengue"})

    assert r.status_code == 200
    assert len(r.json()["resultados"]) == 10
