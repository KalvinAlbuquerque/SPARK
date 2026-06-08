from __future__ import annotations

from collections import Counter
from typing import Any

import asyncpg
import numpy as np

from app.schemas import (
    FacetItem,
    PesquisadorSummary,
    ProducaoCard,
    SearchFacetas,
    SearchFilters,
    SearchSemanticResponse,
)
from app.services.embeddings import encode
from app.services.text_search import _QUALIS_ORDER, _build_filters

TOP_K = 10
TOP_K_INNER = TOP_K * 5  # fetch more to account for duplicates before dedup


def _facetas_from_cards(cards: list[ProducaoCard]) -> SearchFacetas:
    qualis_counts = Counter(c.qualis for c in cards if c.qualis)
    tipo_counts = Counter(c.tipo_producao for c in cards)
    ano_counts = Counter(str(c.ano_publicacao) for c in cards if c.ano_publicacao)
    qualis = sorted(
        [FacetItem(valor=k, total=v) for k, v in qualis_counts.items()],
        key=lambda x: _QUALIS_ORDER.index(x.valor) if x.valor in _QUALIS_ORDER else 99,
    )
    tipos = sorted([FacetItem(valor=k, total=v) for k, v in tipo_counts.items()], key=lambda x: x.valor)
    anos = sorted([FacetItem(valor=k, total=v) for k, v in ano_counts.items()], key=lambda x: x.valor, reverse=True)
    return SearchFacetas(qualis=qualis, tipos=tipos, anos=anos)


def _row_to_card(row: Any) -> ProducaoCard:
    import json as _json
    raw = row["pesquisadores_json"]
    pesquisadores_data = _json.loads(raw) if isinstance(raw, str) else raw
    pesquisadores = [
        PesquisadorSummary(
            id=p["id"],
            nome_completo=p["nome_completo"],
            departamento=p.get("departamento") or None,
            campus=p.get("campus") or None,
        )
        for p in pesquisadores_data
    ]
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
        pesquisadores=pesquisadores,
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
    params.append(TOP_K_INNER)
    inner_limit_ph = f"${next_idx}"
    params.append(TOP_K)
    limit_ph = f"${next_idx + 1}"

    sql = f"""
        WITH candidates AS (
            SELECT
                p.id, p.titulo, p.tipo_producao, p.ano_publicacao, p.nome_veiculo,
                p.issn, p.doi, p.qualis, p.jcr,
                pe.id AS pe_id, pe.nome_completo, pe.departamento, pe.campus,
                GREATEST(0.0, 1.0 - (v.embedding <=> $1)) AS similarity_score
            FROM vetores v
            JOIN producoes p ON p.id = v.producao_id
            JOIN pesquisadores pe ON pe.id = p.pesquisador_id
            WHERE TRUE
            {filter_sql}
            ORDER BY v.embedding <=> $1
            LIMIT {inner_limit_ph}
        ),
        authors AS (
            SELECT
                LOWER(titulo) AS tkey,
                COALESCE(ano_publicacao, 0) AS akey,
                json_agg(
                    json_build_object(
                        'id', pe_id,
                        'nome_completo', nome_completo,
                        'departamento', departamento,
                        'campus', campus
                    ) ORDER BY nome_completo
                ) AS pesquisadores_json
            FROM (
                SELECT DISTINCT ON (LOWER(titulo), COALESCE(ano_publicacao, 0), pe_id)
                    titulo, ano_publicacao, pe_id, nome_completo, departamento, campus
                FROM candidates
                ORDER BY LOWER(titulo), COALESCE(ano_publicacao, 0), pe_id
            ) sub
            GROUP BY LOWER(titulo), COALESCE(ano_publicacao, 0)
        ),
        deduped AS (
            SELECT DISTINCT ON (LOWER(titulo), COALESCE(ano_publicacao, 0))
                id, titulo, tipo_producao, ano_publicacao, nome_veiculo, issn, doi, qualis, jcr, similarity_score
            FROM candidates
            ORDER BY LOWER(titulo), COALESCE(ano_publicacao, 0), similarity_score DESC, id
        )
        SELECT d.*, a.pesquisadores_json
        FROM deduped d
        JOIN authors a
            ON LOWER(d.titulo) = a.tkey
            AND COALESCE(d.ano_publicacao, 0) = a.akey
        ORDER BY similarity_score DESC
        LIMIT {limit_ph}
    """

    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(sql, *params)
        except Exception:
            rows = []

    cards = [_row_to_card(r) for r in rows]
    return SearchSemanticResponse(resultados=cards, facetas=_facetas_from_cards(cards))
