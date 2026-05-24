"""
Testes unitários — POST /api/search/text
Cobre: resultado com dados, resultado vazio, entrada inválida.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_pool(rows=None, val=None):
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=rows or [])
    conn.fetchval = AsyncMock(return_value=val)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=cm)
    return pool


def _sample_row(total_count=1):
    return {
        "id": 1,
        "titulo": "Dengue em zonas urbanas",
        "tipo_producao": "ARTIGO",
        "ano_publicacao": 2024,
        "nome_veiculo": "PLOS BIOLOGY",
        "issn": "1545-7885",
        "doi": "10.1371/test",
        "qualis": "A1",
        "jcr": 7.8,
        "pesquisador_id": 1,
        "nome_completo": "Eduardo Jorge",
        "departamento": "DCET",
        "campus": "Campus I",
        "rank": 0.92,
        "total_count": total_count,
    }


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ── testes ────────────────────────────────────────────────────────────────────

def test_search_text_resultado_com_dados():
    pool = _make_pool(rows=[_sample_row(total_count=1)])
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.post("/api/search/text", json={"query": "dengue"})

    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["total_pages"] == 1
    assert len(data["resultados"]) == 1
    prod = data["resultados"][0]
    assert prod["titulo"] == "Dengue em zonas urbanas"
    assert prod["qualis"] == "A1"
    assert prod["jcr"] == 7.8
    assert prod["pesquisador"]["nome_completo"] == "Eduardo Jorge"
    # similarity_score deve estar ausente na busca textual
    assert "similarity_score" not in prod


def test_search_text_resultado_vazio():
    pool = _make_pool(rows=[])
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.post("/api/search/text", json={"query": "xyzxyzxyz"})

    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 0
    assert data["total_pages"] == 0
    assert data["resultados"] == []


def test_search_text_entrada_invalida_query_vazia():
    pool = _make_pool()
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.post("/api/search/text", json={"query": ""})

    assert r.status_code == 422


def test_search_text_entrada_invalida_page_zero():
    pool = _make_pool()
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.post("/api/search/text", json={"query": "dengue", "page": 0})

    assert r.status_code == 422


def test_search_text_null_fields_omitidos():
    """Campos NULL não devem aparecer na resposta."""
    row = _sample_row()
    row["nome_veiculo"] = None
    row["issn"] = None
    row["doi"] = None
    row["qualis"] = None
    row["jcr"] = None
    pool = _make_pool(rows=[row])
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.post("/api/search/text", json={"query": "dengue"})

    assert r.status_code == 200
    prod = r.json()["resultados"][0]
    assert "nome_veiculo" not in prod
    assert "issn" not in prod
    assert "doi" not in prod
    assert "qualis" not in prod
    assert "jcr" not in prod


def test_search_text_paginacao():
    rows = [_sample_row(total_count=25)]
    pool = _make_pool(rows=rows)
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.post("/api/search/text", json={"query": "dengue", "page": 2})

    assert r.status_code == 200
    data = r.json()
    assert data["page"] == 2
    assert data["total"] == 25
    assert data["total_pages"] == 2
