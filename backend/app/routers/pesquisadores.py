import math

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db
from app.schemas import (
    AnoStat,
    PesquisadorProfile,
    PesquisadorProducaoItem,
    PesquisadorProducoesResponse,
    PesquisadorStatsResponse,
    QualisStat,
)

router = APIRouter(prefix="/api/pesquisadores", tags=["pesquisadores"])

PAGE_SIZE = 20


@router.get(
    "/{pesquisador_id}",
    response_model=PesquisadorProfile,
    response_model_exclude_none=True,
)
async def perfil_pesquisador(pesquisador_id: int, pool=Depends(get_db)):
    sql = """
        SELECT id, lattes_id, nome_completo, departamento, campus, resumo,
               data_atualizacao, total_producoes, indice_h, total_a1_a2
        FROM pesquisadores
        WHERE id = $1
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, pesquisador_id)

    if row is None:
        raise HTTPException(status_code=404, detail="Pesquisador não encontrado")

    return PesquisadorProfile(
        id=row["id"],
        lattes_id=row["lattes_id"],
        nome_completo=row["nome_completo"],
        departamento=row["departamento"] or None,
        campus=row["campus"] or None,
        resumo=row["resumo"] or None,
        data_atualizacao=row["data_atualizacao"],
        total_producoes=row["total_producoes"],
        indice_h=row["indice_h"],
        total_a1_a2=row["total_a1_a2"],
    )


@router.get(
    "/{pesquisador_id}/producoes",
    response_model=PesquisadorProducoesResponse,
    response_model_exclude_none=True,
)
async def producoes_pesquisador(
    pesquisador_id: int,
    page: int = 1,
    pool=Depends(get_db),
):
    if page < 1:
        page = 1
    offset = (page - 1) * PAGE_SIZE

    sql = """
        SELECT
            id, titulo, tipo_producao, ano_publicacao, nome_veiculo, qualis, jcr,
            COUNT(*) OVER() AS total_count
        FROM producoes
        WHERE pesquisador_id = $1
        ORDER BY ano_publicacao DESC NULLS LAST, titulo ASC
        LIMIT $2 OFFSET $3
    """
    async with pool.acquire() as conn:
        # Verify researcher exists
        exists = await conn.fetchval("SELECT 1 FROM pesquisadores WHERE id = $1", pesquisador_id)
        if exists is None:
            raise HTTPException(status_code=404, detail="Pesquisador não encontrado")
        rows = await conn.fetch(sql, pesquisador_id, PAGE_SIZE, offset)

    total = int(rows[0]["total_count"]) if rows else 0
    total_pages = math.ceil(total / PAGE_SIZE) if total > 0 else 0

    resultados = [
        PesquisadorProducaoItem(
            id=r["id"],
            titulo=r["titulo"],
            tipo_producao=r["tipo_producao"],
            ano_publicacao=r["ano_publicacao"],
            nome_veiculo=r["nome_veiculo"] or None,
            qualis=r["qualis"] or None,
            jcr=float(r["jcr"]) if r["jcr"] is not None else None,
        )
        for r in rows
    ]

    return PesquisadorProducoesResponse(
        total=total,
        page=page,
        total_pages=total_pages,
        resultados=resultados,
    )


@router.get(
    "/{pesquisador_id}/stats",
    response_model=PesquisadorStatsResponse,
)
async def stats_pesquisador(pesquisador_id: int, pool=Depends(get_db)):
    sql_por_ano = """
        SELECT ano_publicacao AS ano, COUNT(*) AS total
        FROM producoes
        WHERE pesquisador_id = $1 AND ano_publicacao IS NOT NULL
        GROUP BY ano_publicacao
        ORDER BY ano_publicacao ASC
    """
    sql_por_qualis = """
        SELECT qualis, COUNT(*) AS total
        FROM producoes
        WHERE pesquisador_id = $1 AND qualis IS NOT NULL
        GROUP BY qualis
        ORDER BY qualis ASC
    """

    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT 1 FROM pesquisadores WHERE id = $1", pesquisador_id)
        if exists is None:
            raise HTTPException(status_code=404, detail="Pesquisador não encontrado")

        rows_ano = await conn.fetch(sql_por_ano, pesquisador_id)
        rows_qualis = await conn.fetch(sql_por_qualis, pesquisador_id)

    return PesquisadorStatsResponse(
        por_ano=[AnoStat(ano=r["ano"], total=r["total"]) for r in rows_ano],
        por_qualis=[QualisStat(qualis=r["qualis"], total=r["total"]) for r in rows_qualis],
    )
