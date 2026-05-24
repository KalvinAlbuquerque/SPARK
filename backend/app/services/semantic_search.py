from __future__ import annotations

from typing import Any

import asyncpg
import numpy as np

from app.schemas import (
    PesquisadorSummary,
    ProducaoCard,
    SearchFilters,
    SearchSemanticResponse,
)
from app.services.embeddings import encode
from app.services.text_search import _build_filters

TOP_K = 10


def _row_to_card(row: Any) -> ProducaoCard:
    return ProducaoCard(
        id=row["id"],
        titulo=row["titulo"],
        tipo_producao=row["tipo_producao"],
        ano_publicacao=row["ano_publicacao"],
        nome_veiculo=row["nome_veiculo"] or None,
        issn=row["issn"] or None,
        doi=row["doi"] or None,
        qualis=row["qualis"] or None,
        jcr=float(row["jcr"]) if row["jcr"] is not None else None,
        pesquisador=PesquisadorSummary(
            id=row["pesquisador_id"],
            nome_completo=row["nome_completo"],
            departamento=row["departamento"] or None,
            campus=row["campus"] or None,
        ),
        similarity_score=float(row["similarity_score"]),
    )


async def search_semantic(
    pool: asyncpg.Pool,
    query: str,
    filters: SearchFilters,
) -> SearchSemanticResponse:
    embedding: np.ndarray = encode(query)

    params: list[Any] = [embedding]
    filter_sql, next_idx = _build_filters(filters, params, 2)
    params.append(TOP_K)
    limit_ph = f"${next_idx}"

    sql = f"""
        SELECT
            p.id, p.titulo, p.tipo_producao, p.ano_publicacao, p.nome_veiculo,
            p.issn, p.doi, p.qualis, p.jcr,
            pe.id AS pesquisador_id, pe.nome_completo, pe.departamento, pe.campus,
            GREATEST(0.0, 1.0 - (v.embedding <=> $1)) AS similarity_score
        FROM vetores v
        JOIN producoes p ON p.id = v.producao_id
        JOIN pesquisadores pe ON pe.id = p.pesquisador_id
        WHERE TRUE
        {filter_sql}
        ORDER BY v.embedding <=> $1
        LIMIT {limit_ph}
    """

    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(sql, *params)
        except Exception:
            rows = []

    return SearchSemanticResponse(resultados=[_row_to_card(r) for r in rows])
