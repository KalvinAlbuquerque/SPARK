"""
Worker de geração de embeddings — SPK-102.

Dois modos de invocação:
  1. Via endpoint HTTP: `run_worker(pool)` chamado por POST /internal/trigger-embeddings
  2. Standalone CLI: `python worker/embeddings_worker.py` (Engenheiro de Dados)
"""
from __future__ import annotations

import asyncio
import os
import sys

import asyncpg
from dotenv import load_dotenv
from pgvector.asyncpg import register_vector

# Garante que o pacote app seja encontrado quando executado como script
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.services.embeddings import encode  # noqa: E402

MODEL_NAME = "all-MiniLM-L6-v2"

_SQL_PENDING = """
    SELECT id, titulo
    FROM producoes
    WHERE id NOT IN (SELECT producao_id FROM vetores)
    ORDER BY id
"""

_SQL_INSERT = """
    INSERT INTO vetores (producao_id, embedding, modelo_llm)
    VALUES ($1, $2, $3)
    ON CONFLICT (producao_id) DO NOTHING
"""


async def run_worker(pool: asyncpg.Pool) -> int:
    """Processa produções pendentes e retorna o total de vetores gerados."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(_SQL_PENDING)

    count = 0
    for row in rows:
        try:
            embedding = encode(row["titulo"])
            async with pool.acquire() as conn:
                result = await conn.execute(
                    _SQL_INSERT, row["id"], embedding.tolist(), MODEL_NAME
                )
            # asyncpg retorna "INSERT 0 N" — conta apenas inserções reais
            if result.endswith("1"):
                count += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[worker] erro produção {row['id']}: {exc}", file=sys.stderr)

    return count


async def _main() -> None:
    load_dotenv()
    db_url = os.getenv(
        "DATABASE_URL", "postgresql://spark:changeme@localhost:5432/spark"
    )
    pool = await asyncpg.create_pool(db_url, init=register_vector, min_size=1, max_size=4)
    try:
        total = await run_worker(pool)
        print(f"[worker] vetores gerados: {total}")
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(_main())
