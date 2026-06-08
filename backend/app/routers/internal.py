from __future__ import annotations

import os
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_db
from app.schemas import (
    PesquisadorAdminItem,
    PesquisadorAdminListResponse,
    PesquisadorCreateRequest,
    PesquisadorUpdateRequest,
    ReprocessarResponse,
    TriggerEmbeddingsResponse,
    TriggerEtlResponse,
)

router = APIRouter(prefix="/internal", tags=["internal"])

_bearer = HTTPBearer(auto_error=False)


def _require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    key = os.getenv("INTERNAL_API_KEY", "")
    if not key or credentials is None or credentials.credentials != key:
        raise HTTPException(status_code=403, detail="Forbidden")


# ── Embeddings ────────────────────────────────────────────────────────────────

@router.post(
    "/trigger-embeddings",
    response_model=TriggerEmbeddingsResponse,
    dependencies=[Depends(_require_api_key)],
)
async def trigger_embeddings(pool=Depends(get_db)):
    from worker.embeddings_worker import run_worker  # lazy import — heavy model

    total = await run_worker(pool)
    return TriggerEmbeddingsResponse(vetores_gerados=total)


# ── ETL ───────────────────────────────────────────────────────────────────────

@router.post(
    "/trigger-etl",
    response_model=TriggerEtlResponse,
    dependencies=[Depends(_require_api_key)],
)
async def trigger_etl(
    files: List[UploadFile],
    pool=Depends(get_db),
):
    from app.services.etl_pipeline import run_pipeline  # lazy import

    if not files:
        raise HTTPException(status_code=422, detail="Nenhum arquivo XML enviado")

    xml_bytes_list = [await f.read() for f in files]
    result = await run_pipeline(pool, xml_bytes_list)

    return TriggerEtlResponse(
        pesquisadores=result.pesquisadores,
        producoes=result.producoes,
        qualis_match=result.qualis_match,
        doi_fill=result.doi_fill,
        resumo_fill=result.resumo_fill,
        jcr_fill=result.jcr_fill,
        vetores_gerados=result.vetores_gerados,
        erros=result.erros,
    )


# ── Pesquisadores (admin) ─────────────────────────────────────────────────────

_SQL_LIST = """
    SELECT id, lattes_id, nome_completo, departamento, campus,
           total_producoes, data_atualizacao
    FROM pesquisadores
    {where}
    ORDER BY nome_completo
"""

_SQL_COUNT = "SELECT COUNT(*) FROM pesquisadores {where}"


@router.get(
    "/pesquisadores",
    response_model=PesquisadorAdminListResponse,
    dependencies=[Depends(_require_api_key)],
)
async def list_pesquisadores(q: str | None = None, pool=Depends(get_db)):
    if q:
        where = "WHERE nome_completo ILIKE $1"
        param = f"%{q}%"
        async with pool.acquire() as conn:
            total = await conn.fetchval(_SQL_COUNT.format(where=where), param)
            rows = await conn.fetch(_SQL_LIST.format(where=where), param)
    else:
        async with pool.acquire() as conn:
            total = await conn.fetchval(_SQL_COUNT.format(where=""))
            rows = await conn.fetch(_SQL_LIST.format(where=""))

    return PesquisadorAdminListResponse(
        total=total,
        resultados=[PesquisadorAdminItem(**dict(r)) for r in rows],
    )


_SQL_UPSERT = """
    INSERT INTO pesquisadores (lattes_id, nome_completo, departamento, campus)
    VALUES ($1, $2, $3, $4)
    ON CONFLICT (lattes_id) DO UPDATE SET
        nome_completo = EXCLUDED.nome_completo,
        departamento  = EXCLUDED.departamento,
        campus        = EXCLUDED.campus
    RETURNING id, lattes_id, nome_completo, departamento, campus,
              total_producoes, data_atualizacao
"""


@router.post(
    "/pesquisadores",
    response_model=PesquisadorAdminItem,
    status_code=201,
    dependencies=[Depends(_require_api_key)],
)
async def create_pesquisador(
    body: PesquisadorCreateRequest,
    pool=Depends(get_db),
):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            _SQL_UPSERT,
            body.lattes_id,
            body.nome_completo,
            body.departamento,
            body.campus,
        )
    return PesquisadorAdminItem(**dict(row))


@router.put(
    "/pesquisadores/{pesquisador_id}",
    response_model=PesquisadorAdminItem,
    dependencies=[Depends(_require_api_key)],
)
async def update_pesquisador(
    pesquisador_id: int,
    body: PesquisadorUpdateRequest,
    pool=Depends(get_db),
):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=422, detail="Nenhum campo para atualizar")

    set_clause = ", ".join(f"{k} = ${i + 1}" for i, k in enumerate(updates))
    values = list(updates.values()) + [pesquisador_id]
    sql = (
        f"UPDATE pesquisadores SET {set_clause} WHERE id = ${len(values)}"
        " RETURNING id, lattes_id, nome_completo, departamento, campus,"
        " total_producoes, data_atualizacao"
    )

    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *values)

    if row is None:
        raise HTTPException(status_code=404, detail="Pesquisador não encontrado")
    return PesquisadorAdminItem(**dict(row))


@router.delete(
    "/pesquisadores/{pesquisador_id}",
    status_code=204,
    dependencies=[Depends(_require_api_key)],
)
async def delete_pesquisador(pesquisador_id: int, pool=Depends(get_db)):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM pesquisadores WHERE id = $1", pesquisador_id
        )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Pesquisador não encontrado")


@router.post(
    "/pesquisadores/{pesquisador_id}/reprocessar",
    response_model=ReprocessarResponse,
    dependencies=[Depends(_require_api_key)],
)
async def reprocessar_pesquisador(pesquisador_id: int, pool=Depends(get_db)):
    async with pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM pesquisadores WHERE id = $1", pesquisador_id
        )
    if not exists:
        raise HTTPException(status_code=404, detail="Pesquisador não encontrado")

    from app.services.etl_pipeline import run_enrichment_for_pesquisador  # lazy

    result = await run_enrichment_for_pesquisador(pool, pesquisador_id)
    return ReprocessarResponse(
        qualis_match=result.qualis_match,
        doi_fill=result.doi_fill,
        resumo_fill=result.resumo_fill,
        jcr_fill=result.jcr_fill,
        vetores_gerados=result.vetores_gerados,
        erros=result.erros,
    )
