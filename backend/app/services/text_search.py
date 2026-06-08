from __future__ import annotations

import math
import re
from typing import Any

import asyncpg

from app.schemas import (
    FacetItem,
    PesquisadorSummary,
    ProducaoCard,
    SearchFacetas,
    SearchFilters,
    SearchTextResponse,
)

PAGE_SIZE = 20

QUALIS_B1_PLUS = ["B1", "B2", "B3", "B4", "B5", "C"]


def normalize_query(query: str) -> str:
    """Translate explicit AND/NOT operators to websearch_to_tsquery format."""
    q = query.strip()
    # AND is implicit in websearch_to_tsquery; remove it
    q = re.sub(r"\bAND\b\s*", " ", q, flags=re.IGNORECASE)
    # NOT word → -word (websearch_to_tsquery NOT operator)
    q = re.sub(r"\bNOT\s+", "-", q, flags=re.IGNORECASE)
    q = re.sub(r"\s+", " ", q).strip()
    return q


def expand_qualis(qualis_list: list[str]) -> list[str]:
    """Expand 'B1+' shortcut to all strata from B1 downwards."""
    result: list[str] = []
    for q in qualis_list:
        if q == "B1+":
            result.extend(QUALIS_B1_PLUS)
        else:
            result.append(q)
    return list(dict.fromkeys(result))


def _build_filters(filters: SearchFilters, params: list[Any], idx: int) -> tuple[str, int]:
    """Append filter conditions to params and return the SQL fragment + next idx."""
    conditions: list[str] = []

    if filters.ano_min is not None:
        conditions.append(f"p.ano_publicacao >= ${idx}")
        params.append(filters.ano_min)
        idx += 1

    if filters.ano_max is not None:
        conditions.append(f"p.ano_publicacao <= ${idx}")
        params.append(filters.ano_max)
        idx += 1

    if filters.qualis:
        expanded = expand_qualis(filters.qualis)
        ph = ", ".join(f"${idx + i}" for i in range(len(expanded)))
        conditions.append(f"p.qualis IN ({ph})")
        params.extend(expanded)
        idx += len(expanded)

    if filters.tipos:
        ph = ", ".join(f"${idx + i}" for i in range(len(filters.tipos)))
        conditions.append(f"p.tipo_producao IN ({ph})")
        params.extend(filters.tipos)
        idx += len(filters.tipos)

    jcr_parts: list[str] = []
    if filters.jcr_min is not None:
        jcr_parts.append(f"p.jcr >= ${idx}")
        params.append(filters.jcr_min)
        idx += 1
    if filters.jcr_max is not None:
        jcr_parts.append(f"p.jcr <= ${idx}")
        params.append(filters.jcr_max)
        idx += 1

    if jcr_parts:
        jcr_clause = " AND ".join(jcr_parts)
        if filters.jcr_nulo:
            conditions.append(f"({jcr_clause} OR p.jcr IS NULL)")
        else:
            conditions.append(f"({jcr_clause})")
    elif filters.jcr_nulo:
        conditions.append("p.jcr IS NULL")

    if filters.anos:
        ph = ", ".join(f"${idx + i}" for i in range(len(filters.anos)))
        conditions.append(f"p.ano_publicacao IN ({ph})")
        params.extend(filters.anos)
        idx += len(filters.anos)

    if filters.pesquisador_id is not None:
        conditions.append(f"p.pesquisador_id = ${idx}")
        params.append(filters.pesquisador_id)
        idx += 1

    sql = (" AND " + " AND ".join(conditions)) if conditions else ""
    return sql, idx


_QUALIS_ORDER = ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4", "B5", "C"]


def build_facetas_from_rows(facet_rows: list) -> SearchFacetas:
    qualis: list[FacetItem] = []
    tipos: list[FacetItem] = []
    anos: list[FacetItem] = []
    for row in facet_rows:
        item = FacetItem(valor=row["val"], total=row["cnt"])
        dim = row["dim"]
        if dim == "qualis":
            qualis.append(item)
        elif dim == "tipo":
            tipos.append(item)
        else:
            anos.append(item)
    qualis.sort(key=lambda x: _QUALIS_ORDER.index(x.valor) if x.valor in _QUALIS_ORDER else 99)
    tipos.sort(key=lambda x: x.valor)
    anos.sort(key=lambda x: x.valor, reverse=True)
    return SearchFacetas(qualis=qualis, tipos=tipos, anos=anos[:15])


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
    )


async def search_text(
    pool: asyncpg.Pool,
    query: str,
    filters: SearchFilters,
    page: int,
) -> SearchTextResponse:
    normalized = normalize_query(query)
    offset = (page - 1) * PAGE_SIZE

    base_params: list[Any] = [normalized]
    filter_sql, next_idx = _build_filters(filters, base_params, 2)

    main_params = list(base_params) + [PAGE_SIZE, offset]
    limit_ph = f"${next_idx}"
    offset_ph = f"${next_idx + 1}"

    sql = f"""
        WITH base AS (
            SELECT
                p.id, p.titulo, p.tipo_producao, p.ano_publicacao, p.nome_veiculo,
                p.issn, p.doi, p.qualis, p.jcr,
                pe.id AS pe_id, pe.nome_completo, pe.departamento, pe.campus,
                ts_rank(p.texto_busca, websearch_to_tsquery('portuguese', $1)) AS rank
            FROM producoes p
            JOIN pesquisadores pe ON pe.id = p.pesquisador_id
            WHERE p.texto_busca @@ websearch_to_tsquery('portuguese', $1)
            {filter_sql}
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
                FROM base
                ORDER BY LOWER(titulo), COALESCE(ano_publicacao, 0), pe_id
            ) sub
            GROUP BY LOWER(titulo), COALESCE(ano_publicacao, 0)
        ),
        deduped AS (
            SELECT DISTINCT ON (LOWER(titulo), COALESCE(ano_publicacao, 0))
                id, titulo, tipo_producao, ano_publicacao, nome_veiculo, issn, doi, qualis, jcr, rank
            FROM base
            ORDER BY LOWER(titulo), COALESCE(ano_publicacao, 0), rank DESC, id
        ),
        counted AS (
            SELECT d.*, a.pesquisadores_json, COUNT(*) OVER() AS total_count
            FROM deduped d
            JOIN authors a
                ON LOWER(d.titulo) = a.tkey
                AND COALESCE(d.ano_publicacao, 0) = a.akey
        )
        SELECT * FROM counted
        ORDER BY rank DESC
        LIMIT {limit_ph} OFFSET {offset_ph}
    """

    facet_sql = f"""
        WITH base AS (
            SELECT DISTINCT ON (LOWER(p.titulo), COALESCE(p.ano_publicacao, 0))
                p.qualis, p.tipo_producao, p.ano_publicacao
            FROM producoes p
            JOIN pesquisadores pe ON pe.id = p.pesquisador_id
            WHERE p.texto_busca @@ websearch_to_tsquery('portuguese', $1)
            {filter_sql}
            ORDER BY LOWER(p.titulo), COALESCE(p.ano_publicacao, 0), p.id
        )
        SELECT 'qualis' AS dim, qualis AS val, COUNT(*)::int AS cnt
            FROM base WHERE qualis IS NOT NULL GROUP BY qualis
        UNION ALL
        SELECT 'tipo' AS dim, tipo_producao AS val, COUNT(*)::int AS cnt
            FROM base GROUP BY tipo_producao
        UNION ALL
        SELECT 'ano' AS dim, CAST(ano_publicacao AS TEXT) AS val, COUNT(*)::int AS cnt
            FROM base WHERE ano_publicacao IS NOT NULL GROUP BY ano_publicacao
    """

    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(sql, *main_params)
            facet_rows = await conn.fetch(facet_sql, *base_params)
        except Exception:
            rows, facet_rows = [], []

    total = int(rows[0]["total_count"]) if rows else 0
    total_pages = math.ceil(total / PAGE_SIZE) if total > 0 else 0
    facetas = build_facetas_from_rows(facet_rows)

    return SearchTextResponse(
        total=total,
        page=page,
        total_pages=total_pages,
        resultados=[_row_to_card(r) for r in rows],
        facetas=facetas,
    )
