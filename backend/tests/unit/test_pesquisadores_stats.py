"""
Testes unitários — GET /api/pesquisadores/{id}/stats
Cobre: estrutura por_ano e por_qualis, pesquisador inexistente.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_pool_stats(exists=True, rows_ano=None, rows_qualis=None):
    conn = AsyncMock()
    # fetchval: SELECT 1 FROM pesquisadores WHERE id = $1
    conn.fetchval = AsyncMock(return_value=1 if exists else None)
    # fetch chamado 2x: por_ano e por_qualis
    conn.fetch = AsyncMock(side_effect=[rows_ano or [], rows_qualis or []])
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=cm)
    return pool


def _make_pool_perfil(row=None):
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value=row)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=cm)
    return pool


def _make_pool_producoes(exists=True, rows=None):
    conn = AsyncMock()
    conn.fetchval = AsyncMock(return_value=1 if exists else None)
    conn.fetch = AsyncMock(return_value=rows or [])
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=conn)
    cm.__aexit__ = AsyncMock(return_value=False)
    pool = MagicMock()
    pool.acquire = MagicMock(return_value=cm)
    return pool


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


# ── testes de /stats ──────────────────────────────────────────────────────────

def test_pesquisador_stats_estrutura_por_ano_e_qualis():
    rows_ano = [
        {"ano": 2022, "total": 5},
        {"ano": 2023, "total": 8},
        {"ano": 2024, "total": 12},
    ]
    rows_qualis = [
        {"qualis": "A1", "total": 10},
        {"qualis": "A2", "total": 7},
        {"qualis": "B1", "total": 3},
    ]
    pool = _make_pool_stats(rows_ano=rows_ano, rows_qualis=rows_qualis)
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.get("/api/pesquisadores/1/stats")

    assert r.status_code == 200
    data = r.json()
    assert "por_ano" in data
    assert "por_qualis" in data
    assert len(data["por_ano"]) == 3
    assert len(data["por_qualis"]) == 3
    # Validar estrutura dos itens
    assert data["por_ano"][0] == {"ano": 2022, "total": 5}
    assert data["por_qualis"][0] == {"qualis": "A1", "total": 10}


def test_pesquisador_stats_resultado_vazio():
    pool = _make_pool_stats(rows_ano=[], rows_qualis=[])
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.get("/api/pesquisadores/1/stats")

    assert r.status_code == 200
    data = r.json()
    assert data["por_ano"] == []
    assert data["por_qualis"] == []


def test_pesquisador_stats_nao_encontrado():
    pool = _make_pool_stats(exists=False)
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.get("/api/pesquisadores/999/stats")

    assert r.status_code == 404


# ── testes de /perfil ─────────────────────────────────────────────────────────

def test_pesquisador_perfil_retorna_dados():
    row = {
        "id": 1,
        "lattes_id": "1234567890123456",
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I",
        "resumo": "Pesquisador na área de bioinformática.",
        "data_atualizacao": None,
        "total_producoes": 91,
        "indice_h": 4,
        "total_a1_a2": 13,
    }
    pool = _make_pool_perfil(row=row)
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.get("/api/pesquisadores/1")

    assert r.status_code == 200
    data = r.json()
    assert data["nome_completo"] == "Hugo Saba Pereira Cardoso"
    assert data["total_producoes"] == 91
    assert data["indice_h"] == 4


def test_pesquisador_perfil_nao_encontrado():
    pool = _make_pool_perfil(row=None)
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.get("/api/pesquisadores/999")

    assert r.status_code == 404


# ── testes de /{id}/producoes ─────────────────────────────────────────────────

def test_pesquisador_producoes_resultado_com_dados():
    rows = [
        {
            "id": 1,
            "titulo": "Aprendizado de máquina aplicado",
            "tipo_producao": "ARTIGO",
            "ano_publicacao": 2023,
            "nome_veiculo": "Test Journal",
            "qualis": "A2",
            "jcr": 3.5,
            "total_count": 1,
        }
    ]
    pool = _make_pool_producoes(rows=rows)
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.get("/api/pesquisadores/1/producoes")

    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert len(data["resultados"]) == 1


def test_pesquisador_producoes_vazio():
    pool = _make_pool_producoes(rows=[])
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.get("/api/pesquisadores/1/producoes")

    assert r.status_code == 200
    assert r.json()["total"] == 0
    assert r.json()["resultados"] == []


def test_pesquisador_producoes_nao_encontrado():
    pool = _make_pool_producoes(exists=False)
    app.dependency_overrides[get_db] = lambda: pool

    with TestClient(app) as client:
        r = client.get("/api/pesquisadores/999/producoes")

    assert r.status_code == 404
