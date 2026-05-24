"""Testes unitários — worker de geração de embeddings (SPK-93)."""
from __future__ import annotations

import sys
import types
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers para monkeypatch do pool asyncpg
# ---------------------------------------------------------------------------

def _make_pool(rows=None, execute_result="INSERT 0 1"):
    """Retorna um pool mock cujas conexões respondem de forma configurável."""
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=rows or [])
    conn.execute = AsyncMock(return_value=execute_result)

    pool = MagicMock()
    pool.acquire = MagicMock(return_value=_AsyncContextManager(conn))
    return pool, conn


class _AsyncContextManager:
    def __init__(self, value):
        self._value = value

    async def __aenter__(self):
        return self._value

    async def __aexit__(self, *_):
        pass


def _fake_encode(text: str):
    v = np.zeros(384, dtype=np.float32)
    v[0] = 1.0
    return v


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_gera_vetores():
    """Worker deve retornar contagem igual ao número de produções pendentes."""
    rows = [{"id": 1, "titulo": "Artigo sobre dengue"}, {"id": 2, "titulo": "Redes neurais"}]
    pool, conn = _make_pool(rows=rows, execute_result="INSERT 0 1")

    with patch("worker.embeddings_worker.encode", side_effect=_fake_encode):
        from worker.embeddings_worker import run_worker
        total = await run_worker(pool)

    assert total == 2


@pytest.mark.asyncio
async def test_worker_idempotente():
    """Se todas as produções já têm vetor, nada é inserido (ON CONFLICT)."""
    rows = [{"id": 1, "titulo": "Artigo existente"}]
    pool, conn = _make_pool(rows=rows, execute_result="INSERT 0 0")

    with patch("worker.embeddings_worker.encode", side_effect=_fake_encode):
        from worker.embeddings_worker import run_worker
        total = await run_worker(pool)

    assert total == 0


@pytest.mark.asyncio
async def test_worker_sem_pendentes():
    """Worker sem produções pendentes deve retornar 0 sem chamar encode."""
    pool, _ = _make_pool(rows=[])

    with patch("worker.embeddings_worker.encode", side_effect=_fake_encode) as mock_enc:
        from worker.embeddings_worker import run_worker
        total = await run_worker(pool)

    assert total == 0
    mock_enc.assert_not_called()


@pytest.mark.asyncio
async def test_worker_embedding_384_dims():
    """Embedding inserido deve ter 384 dimensões."""
    captured: list[list[float]] = []

    async def _capture_execute(sql, prod_id, embedding, model):
        captured.append(embedding)
        return "INSERT 0 1"

    rows = [{"id": 10, "titulo": "Bioinformática"}]
    pool, conn = _make_pool(rows=rows)
    conn.execute = _capture_execute

    with patch("worker.embeddings_worker.encode", side_effect=_fake_encode):
        from worker.embeddings_worker import run_worker
        await run_worker(pool)

    assert len(captured) == 1
    assert len(captured[0]) == 384


@pytest.mark.asyncio
async def test_worker_continua_apos_erro():
    """Erro em uma produção não deve interromper as demais."""
    rows = [
        {"id": 1, "titulo": "Artigo A"},
        {"id": 2, "titulo": "Artigo B"},
    ]
    pool, conn = _make_pool(rows=rows, execute_result="INSERT 0 1")

    call_count = 0

    def _flaky_encode(text):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("modelo indisponível")
        return _fake_encode(text)

    with patch("worker.embeddings_worker.encode", side_effect=_flaky_encode):
        from worker.embeddings_worker import run_worker
        total = await run_worker(pool)

    # Apenas o segundo artigo deve ter sido inserido
    assert total == 1
