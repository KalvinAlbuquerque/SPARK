"""Testes unitários — endpoints internos (SPK-93/SPK-103)."""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# App fixture com pool mockado
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "test-secret-key")

    # Mock do pool para não precisar de banco real
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=0)
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.execute = AsyncMock(return_value="DELETE 0")

    class _CM:
        async def __aenter__(self):
            return mock_conn
        async def __aexit__(self, *_):
            pass

    mock_pool = MagicMock()
    mock_pool.acquire = MagicMock(return_value=_CM())

    from app.main import app
    from app.database import get_db

    app.dependency_overrides[get_db] = lambda: mock_pool
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------

def test_trigger_embeddings_sem_auth_retorna_403(client):
    resp = client.post("/internal/trigger-embeddings")
    assert resp.status_code == 403


def test_trigger_embeddings_token_errado_retorna_403(client):
    resp = client.post(
        "/internal/trigger-embeddings",
        headers={"Authorization": "Bearer token-errado"},
    )
    assert resp.status_code == 403


def test_trigger_etl_sem_auth_retorna_403(client):
    resp = client.post("/internal/trigger-etl")
    assert resp.status_code == 403


def test_list_pesquisadores_sem_auth_retorna_403(client):
    resp = client.get("/internal/pesquisadores")
    assert resp.status_code == 403


def test_create_pesquisador_sem_auth_retorna_403(client):
    resp = client.post(
        "/internal/pesquisadores",
        json={"lattes_id": "1234567890123456", "nome_completo": "Fulano"},
    )
    assert resp.status_code == 403


def test_delete_pesquisador_sem_auth_retorna_403(client):
    resp = client.delete("/internal/pesquisadores/1")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# trigger-embeddings autenticado
# ---------------------------------------------------------------------------

def test_trigger_embeddings_com_auth_retorna_200(client, monkeypatch):
    async def _fake_worker(pool):
        return 5

    monkeypatch.setattr("worker.embeddings_worker.run_worker", _fake_worker, raising=False)

    with patch("worker.embeddings_worker.run_worker", new=_fake_worker):
        resp = client.post(
            "/internal/trigger-embeddings",
            headers={"Authorization": "Bearer test-secret-key"},
        )

    assert resp.status_code == 200
    assert resp.json()["vetores_gerados"] == 5


# ---------------------------------------------------------------------------
# trigger-etl autenticado
# ---------------------------------------------------------------------------

def test_trigger_etl_sem_arquivos_retorna_422(client):
    resp = client.post(
        "/internal/trigger-etl",
        headers={"Authorization": "Bearer test-secret-key"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Pesquisadores (admin) autenticados
# ---------------------------------------------------------------------------

def test_list_pesquisadores_retorna_200(client):
    resp = client.get(
        "/internal/pesquisadores",
        headers={"Authorization": "Bearer test-secret-key"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "resultados" in data


def test_delete_pesquisador_inexistente_retorna_404(client):
    resp = client.delete(
        "/internal/pesquisadores/9999",
        headers={"Authorization": "Bearer test-secret-key"},
    )
    assert resp.status_code == 404
